#!/bin/sh
# RemoteBatchAppScript:makeMPITemplate
# SubmissionScripts/Distributor/Batch/APP/mpi
#
SCRIPT=`basename $0`
WORKINGDIR=`dirname $0`

cd ${WORKINGDIR}


export SESSION=1443092


TIMEPATH=
for timePath in ${HOME}/bin/time /usr/bin/time /usr/local/bin/time ; do
   if [ -x ${timePath} ] ; then
      TIMEPATH=${timePath}
      break
   fi
done

rankExtension=`printf "%06d" ${OMPI_MCA_ns_nds_vpid}`
${TIMEPATH} --format "Command exited with status %x\nreal %e\nuser %U\nsys %S" -o .__time_results.07037007_01-${rankExtension} \
   /depot/nanohub/apps/rice/share64/espresso/espresso-6.2.1/bin/pw.x -in ./57bbff0d649a.in  "$@" < /dev/null
