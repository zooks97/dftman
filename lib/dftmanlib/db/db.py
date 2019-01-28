import BTrees.OOBTree
import transaction
import ZODB
import ZODB.FileStorage


def init(path='./db.fs'):
    if not os.path.exists(path):
        root = load_db(path)
        root.MPQueries = BTrees.OOBTree.BTree()
        root.Jobs = BTrees.OOBTree.BTree()
        root.Workflows = BTrees.OOBTree.BTree()
        transaction.commit()
    else:
        print('This database already exists! Loading instead.')
        root = load(path)
    return root

def load(path='./db.fs'):
    storage = ZODB.FileStorage.FileStorage('db.fs')
    db = ZODB.DB(storage)
    connection = db.open()
    root = connection.root
    return root

def store(object_, root, report=True, overwrite=False):
    if isinstance(object_, SubmitJob):
        tree = root.SubmitJobs
    elif isinstance(object_, MPQuery):
        tree = root.MPQueries
    else:
        raise ValueError('This is an unsupported object.'\
                         ' The database only accepts'\
                         ' SubmitJob and MPQuery.')
    key = object_.key
    if not overwrite and key in list(tree.keys()):
        raise ValueError('This key already exists!'\
                         ' Use the overwrite argument to'
                         ' overwrite the entry.')
    else:
        tree[key] = object_
        transaction.commit()
        print('Added {} to the database'.format(key))
    return key
    
def batch_store(objects, root, report=True, overwrite=False):
    trees = []
    for object_ in objects:
        if isinstance(object_, SubmitJob):
            tree = root.SubmitJobs
        elif isinstance(object_, MPQuery):
            tree = root.MPQueries
        else:
            raise ValueError('This is an unsupported object.'\
                             ' The database only accepts'\
                             ' SubmitJob and MPQuery.')
        trees.append(tree)
    
    keys = [object_.key for object_ in objects]
    if len(set(keys)) != len(keys):
        raise ValueError('One or more of these are duplicates!')
        
    for tree, key, object_ in zip(trees, keys, objects):
        if key in list(tree.keys()):
            raise ValueError('{} is already in {}'.format(key, tree))
        else:
            tree[key] = object_
    
    transaction.commit()
    
    return keys