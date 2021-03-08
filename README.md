# Repository Description/General Info

* CalculateExtremeEventTimeSeries.py takes the slp data and calculates extreme event time series based on the 5th percentile of slp in th months of november, december, january, february and march seperately
*
*

# Requirements

## Python

* install conda with

```
 wget https://repo.anaconda.com/archive/Anaconda3-2020.11-Linux-x86_64.sh

 bash Anaconda3-2020.11-Linux-x86_64.sh

```

* after that, the following should be in .bashrc

```
# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('~/anaconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "~/anaconda3/etc/profile.d/conda.sh" ]; then
        . "~/anaconda3/etc/profile.d/conda.sh"
    else
        export PATH="~/anaconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

```
* this could lead to conda activaing automatically, which can be stopped with the following command

```
conda config --set auto_activate_base false

```

* now, create a conda env based on environment.yaml and the installation dependencies in it

```
conda env create -f environment.yaml

```
* the created env can now be activated or deactivated
```
conda activate <name of env in environment.yml>

conda deactivate

``` 

## Data

* data used for analyses and calculations can be requested at ozansahin92@gmail.com

# TODOS

## Primary Tasks

* calculate and subsequently save extreme event time series out of the slp time series
* adjusting ES_numba.py to new spatially reduced data
* running ES_numba.py with parallel_for_loop_es.sh on PIK cluster for taumax=2,8,16
* adjusting scp.sh to get the calculated data from the PIK cluster
* plotting ES maps and saving the adjacency matrices for taumax=2,8,16 wir ES_Extreme.ipynb
* sending JH the adjacecy matrices and the definitions of the CN measures used in Complex_network_analysis.ipynb

## Secondary Tasks

* cleaning up the code and remove unnecessary parts
* add comprehensive description of all parts of this repository and the code to README.md
