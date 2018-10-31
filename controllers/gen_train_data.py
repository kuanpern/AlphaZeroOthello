# generate self play training data
from string import Template
import subprocess
from multiprocessing import Pool

cmd_template = Template('''
$venv/bin/python $exedir/Othello_self_play_main.py 
  --agent_p $agentp
  --agent_q $agentq
  --config_p $configp
  --config_q $configq
  --max_length 62 
  --repo_size 30 
  --outfile $outdir/$outroot-$num.dill > $logdir/$outroot-$num.log
''')

def run_cmd(cmd):
	lines = cmd.strip().splitlines()
	lines = [line.strip() for line in lines]
	cmd = ' '.join(lines)
	out = subprocess.check_output(cmd, shell=True)
	return out
# end def


import argparse
import datetime

# parse inputs
parser = argparse.ArgumentParser(description='Othello DeepLearning Training')
parser.add_argument('--N',        help="number of game to simulate", type=int, required=True)
parser.add_argument('--nproc',    help="number of processes", type=int, default=1)
parser.add_argument('--exedir',   help="execuatable directory",  type=str, required=True)
parser.add_argument('--venv' ,    help="virtual environment directory",   type=str, required=True)
parser.add_argument('--agentp',   help="agent P model file", type=str, required=True)
parser.add_argument('--agentq' ,  help="agent Q model file", type=str, required=True)
parser.add_argument('--configp',  help="agent P simulation config file", type=str, required=True)
parser.add_argument('--configq' , help="agent Q simulation config file", type=str, required=True)
parser.add_argument('--outroot',  help="output root name",   type=str, required=True)
parser.add_argument('--outdir' ,  help="output directory",   type=str, required=True)
parser.add_argument('--logdir',   help="log file directory", type=str, required=True)
pars = vars(parser.parse_args())

N     = pars['N']
nproc = pars['nproc']

# build command lines
cmds = []
filln = max(6, len(str(N)))
for i in range(1, N+2):
	num = str(i).zfill(filln)
	cmd = cmd_template.substitute({
	  'num'    : num,
	  'venv'   : pars['venv'],
	  'exedir' : pars['exedir'],
	  'agentp' : pars['agentp'],
	  'agentq' : pars['agentq'],
	  'configp': pars['configp'],
	  'configq': pars['configq'],
	  'outroot': pars['outroot'],
	  'outdir' : pars['outdir'],
	  'logdir' : pars['logdir']
	})
	lines = cmd.splitlines()
	lines = [line.strip() for line in lines]
	cmd = ' '.join(lines)

	cmds.append(cmd)
# end for

# make a pool of process and start computing
pool_size = nproc
p = Pool(pool_size)
p.map(run_cmd, cmds)
p.close()
p.join()
