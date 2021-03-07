# Requirements for python script

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
