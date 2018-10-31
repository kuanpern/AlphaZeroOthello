# start an interactive play
export project_home=/home/ucare_worker/mcts_othello
$project_home/venv/bin/python Othello_interactive_play_main.py \
  --agent_p pars/random_predictor.dill \
  --agent_q pars/random_predictor.dill \
  --config_p pars/config_sample.yaml   \
  --config_q pars/config_sample.yaml   \
  --max_length 62 \
  --repo_size 30 \
  --outfile output/test_run_02.dill
