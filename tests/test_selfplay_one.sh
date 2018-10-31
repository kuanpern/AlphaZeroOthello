# generate a self play
export project_home=/home/kuanpern/Desktop/mcts_othello

$project_home/venv/bin/python Othello_self_play_main.py \
  --agent_p pars/random_predictor.dill \
  --agent_q pars/random_predictor.dill \
  --config_p pars/config_sample.yaml   \
  --config_q pars/config_sample.yaml   \
  --max_length 62 \
  --repo_size 30 \
  --outfile output/test_run_01.dill > output/test_run_01.log

# plot confidence level
$project_home/venv/bin/python analysis_toolbox/plot_confidence.py \
  --input_path output/test_run_01.dill \
  --out_fig    output/test_run_01.confidence.png

# plot the game play
rm -r output/test_run_01_gameplay/
$project_home/venv/bin/python analysis_toolbox/plot_gameplay.py \
  --input_path output/test_run_01.dill \
  --out_dir output/test_run_01_gameplay

