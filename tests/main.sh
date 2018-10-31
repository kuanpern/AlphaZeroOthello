export project_home=/home/kuanpern/Desktop/mcts_othello/
# generate a random predictor
$project_home/venv/bin/python $project_home/tests/generate_random_predictor.py

# test self-play for one game
./test_selfplay_one.sh

# start an interactive play
./test_interactive_play.sh

# generate playouts in batch
./test_generate_playouts.sh

# encode playouts to ML input format
./encode_simulation_data.sh

# training using AlphaZero algorithm (single node)
$project_home/learning/venv/bin/python $project_home/learning/OthelloZeroNet.py  \
  --inputdir $project_home/data/training_inputs/ \
  --outroot random \
  --outdir   $project_home/data/models/ \
  --interval 60

# training using AlphaZero algorithm (multi-process, single server)
$project_home/learning/venv/bin/python $project_home/learning/OthelloZeroNet.distributed.py \
  --inputdir $project_home/data/training_inputs/ \
  --outroot random_dist \
  --outdir $project_home/data/models/ \
  --interval 60 \
  --host 127.0.0.1 \
  --port 5000 \
  --worldsize 2


# training using AlphaZero algorithm (multi-process, multi-nodes)
# - note: please refer to README.distributed.md on how to setup a MPI cluster
# - note: use client name as per defined in the cluster
$project_home/learning/anaconda3/bin/mpirun -np 6 -hosts mpi01,mpi02,mpi03 \
  $project_home/learning/anaconda3/bin/python $project_home/learning/OthelloZeroNet.distributed.py \
  --inputdir $project_home/data/training_inputs/ \
  --outroot random_dist \
  --outdir $project_home/data/models/ \
  --interval 60 \
  --host 127.0.0.1 \
  --port 5000 \
  --worldsize 0 \
  --backend mpi
