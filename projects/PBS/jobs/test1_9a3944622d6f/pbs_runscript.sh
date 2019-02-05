
#!/bin/bash
#PBS -l walltime=01:00:00
#PBS -l nodes=1:ppn=20
#PBS -q standby
#PBS -N test1



mpirun -np 20 mpirun -np 20 pw.x < /home/nanohub/azadoks/git/dftman/projects/PBS/jobs/test1_9a3944622d6f/pwscf.in > /home/nanohub/azadoks/git/dftman/projects/PBS/jobs/test1_9a3944622d6f/pwscf.out


