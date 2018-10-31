export project_home=/home/mpiuser/cloud/mcts_othello/
$project_home/venv/bin/python $project_home/controllers/gen_train_data.py \
  --N 500 \
  --nproc 4 \
  --exedir  $project_home/ \
  --venv    $project_home/venv/ \
  --agentp  $project_home/pars/random_predictor.dill \
  --agentq  $project_home/pars/random_predictor.dill \
  --configp $project_home/pars/config_sample.yaml    \
  --configq $project_home/pars/config_sample.yaml    \
  --outroot random \
  --outdir  $project_home/data/playouts/ \
  --logdir  $project_home/data/playouts/

