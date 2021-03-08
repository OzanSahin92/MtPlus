#!/bin/bash

#SBATCH --qos=short
#SBATCH --job-name=es
#SBATCH --account=synet
#SBATCH --output=%j.out
#SBATCH --error=%j.err
#SBATCH --nodes=20
#SBATCH --ntasks-per-node=5
#SBATCH --cpus-per-task=2
#SBATCH --workdir=/p/tmp/sahin
#SBATCH --mail-type=END
#SBATCH --mail-user=ozansahin92@gmail.com

module load anaconda/5.0.0_py3 

source activate sahin

TAUMAX=$1
SIGN=$2
GOALDIR=$3

srun --mpi=pmi2 -n 100 python ES_numba.py $TAUMAX $SIGN $GOALDIR


