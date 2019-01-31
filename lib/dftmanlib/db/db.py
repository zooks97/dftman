from .. import base
from ..job import SubmitJob
from ..pwscf import PWInput, PWOutput, PWCalculation
from ..pwscf.workflow import EOSWorkflow

import os.path
import codecs
import json
import warnings

from collections.abc import Mapping

from tinydb import TinyDB, Query, Storage, where
from tinydb.database import Table, StorageProxy, _get_doc_id, _get_doc_ids

from monty.json import MontyEncoder, MontyDecoder

DB_PATH = 'db.tinydb'

def init_db(path=DB_PATH,):
    if not os.path.exists(path):
        db = TinyDB(path, storage=MSONStorage,
                    storage_proxy_class=MSONStorageProxy,
                    table_class=MSONTable)
    else:
        raise FileExistsError('{} already exists, loading.')
        db = TinyDB(path)
    return db

def load_db(path=DB_PATH, init=True):
    if os.path.exists(path):
        return TinyDB(path, storage=MSONStorage,
                      storage_proxy_class=MSONStorageProxy,
                      table_class=MSONTable)
    elif init:
        return init_db(path)
    else:
        raise FileNotFoundError('{} does not exist.')

def touch(fname, create_dirs):
    if create_dirs:
        base_dir = os.path.dirname(fname)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

    if not os.path.exists(fname):
        with open(fname, 'a'):
            os.utime(fname, None)
                
                
class AlreadyStoredError(Exception):
    pass


class MSONStorage(Storage):
    """
    Store the data in a MSON file.
    """

    def __init__(self, path, create_dirs=False, encoding=None, **kwargs):
        """
        Create a new instance.
        Also creates the storage file, if it doesn't exist.
        :param path: Where to store the MSON data.
        :type path: str
        """
        touch(path, create_dirs=create_dirs)  # Create file if not exists
        self.kwargs = kwargs
        self._handle = codecs.open(path, 'r+', encoding=encoding)

    def close(self):
        self._handle.close()

    def read(self):
        # Get the file size
        self._handle.seek(0, os.SEEK_END)
        size = self._handle.tell()

        if not size:
            # File is empty
            return None
        else:
            self._handle.seek(0)
            return json.load(self._handle, cls=MontyDecoder)

    def write(self, data):
        self._handle.seek(0)
        serialized = json.dumps(data, cls=MontyEncoder, **self.kwargs)
        self._handle.write(serialized)
        self._handle.flush()
        os.fsync(self._handle.fileno())
        self._handle.truncate()


class MSONStorageProxy(StorageProxy):
    
    def _new_document(self, key, value):
        doc_id = int(key)
        value.doc_id = doc_id
        return value

    
class MSONTable(Table):

    def check_stored(self, msonable):
        """
        Check if an msonable is already stored
        
        :param msonable: the msonable object to check
        :returns: doc_ids of matches
        """
        query = Query()
        hash_ = msonable.hash
        matches = self.search(query.hash == hash_)
        doc_ids = [match.doc_id for match in matches]
        return doc_ids
    
        
    def insert(self, document, block_if_stored=True):
        """
        Insert a new document into the table.

        :param document: the document to insert
        :returns: the inserted document's ID
        """
        
        if block_if_stored:
            doc_ids = self.check_stored(document)
            if doc_ids:
                raise AlreadyStoredError('Already stored at doc_ids {}'
                                         .format(doc_ids))

        doc_id = self._get_doc_id(document)
        data = self._read()
        data[doc_id] = document
        self._write(data)

        return doc_id

    def insert_multiple(self, documents, block_if_stored=True):
        """
        Insert multiple documents into the table.

        :param documents: a list of documents to insert
        :returns: a list containing the inserted documents' IDs
        """

        if block_if_stored:
            doc_ids = []
            for doc in documents:
                doc_ids += self.check_stored(soc)
            if doc_ids:
                raise AlreadyStoredError('Already stored at doc_ids {}'
                                         .format(doc_ids))
        
        doc_ids = []
        data = self._read()

        for doc in documents:
            doc_id = self._get_doc_id(doc)
            doc_ids.append(doc_id)

            data[doc_id] = doc

        self._write(data)

        return doc_ids
        
    def write_back(self, documents, doc_ids=None, eids=None):
        """
        Write back documents by doc_id
        :param documents: a list of document to write back
        :param doc_ids: a list of document IDs which need to be written back
        :returns: a list of document IDs that have been written
        """
        doc_ids = _get_doc_ids(doc_ids, eids)

        if doc_ids is not None and not len(documents) == len(doc_ids):
            raise ValueError(
                'The length of documents and doc_ids is not match.')

        if doc_ids is None:
            doc_ids = [doc.doc_id for doc in documents]

        # Since this function will write docs back like inserting, to ensure
        # here only process existing or removed instead of inserting new,
        # raise error if doc_id exceeded the last.
        if len(doc_ids) > 0 and max(doc_ids) > self._last_id:
            raise IndexError(
                'ID exceeds table length, use existing or removed doc_id.')

        data = self._read()

        # Document specified by ID
        documents.reverse()
        for doc_id in doc_ids:
            data[doc_id] = documents.pop()
    
        self._write(data)

        return doc_ids

