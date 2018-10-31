## Prerequisites
# assign one master and several clients
# enable password-less SSH login with the cluster
# (optional) each node could identify peer with hostname

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

# done.
