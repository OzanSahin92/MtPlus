FROM gcc:latest

SHELL [ "/bin/bash", "--login", "-c" ]

RUN  apt-get update --quiet --yes \
  && apt-get install --quiet --yes --no-install-recommends \
  apt-utils \
  wget \
  libxi6:amd64 \
  libxfixes3:amd64 \
  libxcursor1:amd64 \
  libxdamage1:amd64 \
  libxcomposite1:amd64

RUN rm -rf /var/lib/apt/lists/*

# Create a non-root user
ARG username=mtplus
ARG uid=1000
ARG gid=100
ENV USER $username
ENV UID $uid
ENV GID $gid
ENV HOME /home/$USER
ENV PROJECT_DIR $HOME/project
ENV MINICONDA_VERSION 4.9.2
ENV CONDA_DIR $HOME/miniconda3
# make non-activate conda commands available
ENV PATH=$CONDA_DIR/bin:$PATH
ENV SHELL /bin/bash

RUN adduser --disabled-password \
    --gecos "Non-root user" \
    --uid $UID \
    --gid $GID \
    --home $HOME \
    $USER

# create a project directory inside user home
RUN mkdir $PROJECT_DIR
WORKDIR $PROJECT_DIR

COPY MtPlus/environment.yml /tmp/
RUN chown $UID:$GID /tmp/environment.yml

COPY MtPlus/entrypoint.sh /usr/local/bin/
RUN chown $UID:$GID /usr/local/bin/entrypoint.sh && \
    chmod u+x /usr/local/bin/entrypoint.sh

USER $USER
# install miniconda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-py38_4.9.2-Linux-x86_64.sh -O ~/miniconda.sh && \
    chmod +x ~/miniconda.sh && \
    ~/miniconda.sh -b -p $CONDA_DIR && \
    rm ~/miniconda.sh

# make conda activate command available from /bin/bash --login shells
RUN echo ". $CONDA_DIR/etc/profile.d/conda.sh" >> ~/.profile
# make conda activate command available from /bin/bash --interative shells
RUN conda init bash

# build the conda environment
RUN conda update --name base --channel defaults conda && \
    conda env create --file /tmp/environment.yml --force && \
    conda clean --all --yes

ENTRYPOINT [ "/usr/local/bin/entrypoint.sh" ]

# default command will launch JupyterLab server for development
CMD [ "jupyter", "lab", "--no-browser", "--ip", "0.0.0.0", "--LabApp.token=''", "--LabApp.password=''" ]
