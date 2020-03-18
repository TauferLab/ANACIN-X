#BSUB -n 16

#BSUB -o /data/gclab/anacin-k/naive_out
#BSUB -e /data/gclab/anacin-k/naive_err

./naive_reduce_example.sh 16 0 29
