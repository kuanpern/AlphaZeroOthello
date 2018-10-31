## Testing Scenario


#### Generate a random predictor
To test/run the server working, we can use a random predictor (rather than training one).
```
# generate a random predictor
$project_home/venv/bin/python $project_home/tests/generate_random_predictor.py
```

### test self-play for one game
```
$ ./test_selfplay_one.sh
```

### start an interactive play
```
$ ./test_interactive_play.sh
```

### generate playouts in batch
```
$ ./test_generate_playouts.sh
```

### encode playouts to ML input format
```
$ ./encode_simulation_data.sh
```

### training using AlphaZero algorithm (single node)
```
$project_home/learning/venv/bin/python $project_home/learning/OthelloZeroNet.py  \
  --inputdir $project_home/data/training_inputs/ \
  --outroot random \
  --outdir   $project_home/data/models/ \
  --interval 60
```

### training using AlphaZero algorithm (multi-process, single server)
```
$project_home/learning/venv/bin/python $project_home/learning/OthelloZeroNet.distributed.py \
  --inputdir $project_home/data/training_inputs/ \
  --outroot random_dist \
  --outdir $project_home/data/models/ \
  --interval 60 \
  --host 127.0.0.1 \
  --port 5000 \
  --worldsize 2
```

### training using AlphaZero algorithm (multi-process, multi-nodes)
To utilize the full capability of using multi-process multi-nodes for training, the setup process is more involved.

First, we need to setup a MPI cluster.
#### Prerequisites
 - assign one master and several clients
 - enable password-less SSH login with the cluster
 - (optional) each node could identify peer with hostname
```
master,clients>$ sudo apt-get install nfs-common

# enable NFS shared directory
master>$ mkdir cloud
master>$ sudo nano /etc/exports
# add the following line
# /home/mpiuser/cloud *(rw,sync,no_root_squash,no_subtree_check)
master>$ sudo exportfs -a
master>$ sudo service nfs-kernel-server restart

# mount shared directory
clients>$ mkdir cloud
clients>$ sudo mount -t nfs master:/home/mpiuser/cloud ~/cloud

# install anaconda
master>$ wget https://repo.anaconda.com/archive/Anaconda3-5.2.0-Linux-x86_64.sh
master>$ bash Anaconda3-5.2.0-Linux-x86_64.sh 
# - note: choose anaconda home directory to be in the shared directory

# install prerequisites
master>$ export CMAKE_PREFIX_PATH=$anaconda_home
master>$ $anaconda_home/bin/conda install numpy pyyaml mkl mkl-include setuptools cmake cffi typing
master>$ $anaconda_home/bin/conda install -c mingfeima mkldnn

# install MPICH
master>$ $anaconda_home/bin/conda install -c conda-forge mpich
master>$ $anaconda_home/bin/conda install -c conda-forge/label/broken mpich 

# compile pytorch from source
master>$ git clone --recursive https://github.com/pytorch/pytorch
master>$ cd pytorch/
master>$ $anaconda_home/bin/python setup.py install
```

To run the test
(note: use client name as per defined in the cluster)
```
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
```
