## AlphaZeroOthello
Migrating AlphaGO Zero strategy to play Othello.
The package is organized such that the strategy is flexible enough to be plug-and-play to play different games/scenarios.


#### Demo
note: This repo also contains socket-powered real-time gameplay engine and web-browser interface.

```
# start the main server
cd $project_home/servers; venv/bin/python app.py

# sockets connections
cd $project_home/servers/relay; venv/bin/python relayer.py --input sock_pairs.yaml 

# start the MCTS gameplay
cd $project_home/; venv/bin/python Othello_interactive_play_main.py   \
  --agent_p pars/random_predictor.dill   \
  --agent_q pars/random_predictor.dill   \
  --config_p pars/config_sample.yaml     \
  --config_q pars/config_sample.yaml     \
  --max_length 62   \
  --repo_size 30    \
  --outfile output/test_run_02.dill
```
![Alt text](images/interactive_demo.png?raw=true "interactive gameplay demo")


### Installation
```
# python tkinter for plotting
$ sudo apt-get install python3-tk
# install virtual environments
$ sudo apt-get install virtualenv
$ virtualenv -p python3 venv 
$ venv/bin/pip install -r requirements.list
```

For deep-learning part, please refer to https://pytorch.org/ to download the pytorch package

### Test run
see tests/ for test run scenarios


### References
 * AlphaGo Zero: https://deepmind.com/documents/119/agz_unformatted_nature.pdf


### File Tree
```
/
├── MCTS_lib         : core functions for Monte Carlo tree search
├── learning         : utility functions for deep-learning
├── controllers      : functions for background training
├── analysis_toolbox : functions to analyse gameplay
├── game_rules       : define Othello game rule
├── data             : data directory
├── pars             : directory for parameters (e.g. ML models)
├── servers          : servers for interactive gameplay
└── tests            : tests
```
