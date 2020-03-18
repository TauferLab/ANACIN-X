#BSUB -n 16

#BSUB -o /data/gclab/anacin-k/ninja_out
#BSUB -e /data/gclab/anacin-k/ninja_err

export MINI_NINJA_CONFIG=/home/dsuarez1/Src_mini_ninja/config/uniform.json

./naive_ninja_reduce.sh 16 0 29
