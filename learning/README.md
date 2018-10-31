

### Loss function
<a href="https://www.codecogs.com/eqnedit.php?latex=l&space;=&space;(z&space;-&space;v)^2&space;-&space;\pi^T&space;\log&space;p&space;&plus;&space;c&space;\left&space;\|&space;\theta&space;\right&space;\|&space;^2" target="_blank"><img src="https://latex.codecogs.com/gif.latex?l&space;=&space;(z&space;-&space;v)^2&space;-&space;\pi^T&space;\log&space;p&space;&plus;&space;c&space;\left&space;\|&space;\theta&space;\right&space;\|&space;^2" title="l = (z - v)^2 - \pi^T \log p + c \left \| \theta \right \| ^2" /></a>

### Network architecture
A single convolutional block followed by either 19 or 39 residual blocks.

The convolutional block applies the following modules:

1. A convolution of 256 filters of kernel size 3 × 3 with stride 1
1. Batch normalisation
1. A rectifier non-linearity

Each residual block applies the following modules sequentially to its input:

1. A convolution of 256 filters of kernel size 3 × 3 with stride 1
2. Batch normalisation
3. A rectifier non-linearity
4. A convolution of 256 filters of kernel size 3 × 3 with stride 1
5. Batch normalisation
6. A skip connection that adds the input to the block
7. A rectifier non-linearity

The output of the residual tower is passed into two separate “heads” for computing the policy
and value respectively. The policy head applies the following modules:

1. A convolution of 2 filters of kernel size 1 × 1 with stride 1
2. Batch normalisation
3. A rectifier non-linearity
4. A fully connected linear layer that outputs a vector of size 19 2 + 1 = 362 corresponding to logit probabilities for all intersections and the pass move

The value head applies the following modules:

1. A convolution of 1 filter of kernel size 1 × 1 with stride 1
2. Batch normalisation
3. A rectifier non-linearity
4. A fully connected linear layer to a hidden layer of size 256
5. A rectifier non-linearity
6. A fully connected linear layer to a scalar
7. A tanh non-linearity outputting a scalar in the range [−1, 1]


#### Reference
* <a href="https://www.nature.com/articles/nature24270"> DeepMind Nature paper </a>

