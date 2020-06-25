SUPREME Balloon Analogue Risk Task Model
============================================


This is the model of the balloon analogue risk task (BART) paradigm that is included in *SUPREME*
(Sensing to Understanding and Prediction Realized via an Experiment and Modeling
Ecosystem). After data has been acquired with the BART task, users can
gain insight into latent mechanisms by fitting the model. Data are first
converted to a readable format using functions in `smile`_. The Python-based
model uses `RunDEMC`_ to calculate a posterior distribution for each parameter
via Bayesian-inspired methods.

`_smile: https://github.com/compmem/smile`
`_RunDEMC: http://github.com/compmem/RunDEMC`

It requires Python 3. Included in this directory is a `envrionment.yml` file, which lists all Python package
versions and environment variables. Using an Anaconda distribution of Python 3, you can create a virtual 
environment that contains all necessary packages with the appropriate versions by running the following 
command:
```bash
conda env create -f environment.yml
```

How to install the correct version of RunDEMC:
```bash
git clone https://github.com/compmem/RunDEMC.git
cd RunDEMC
git checkout f2d07db
python setup.py install
```

The following commands provide a way for generating various information related to the BART experiment. These
commands require an `.h5` file containing information about the generated balloons in the BART experiment and a
`.csv` file containing the partipants' responses. The `.h5` file can be generated using code from the 
`bart_preproc.py` file. To generate a`.csv` file from smile `.slog` files, use the following Python code:

```
from smile.log import log2dl
import pandas as pd

data = pd.DataFrame(log2dl("[subject]/[session]/log_BART_0.slog"))
data.to_csv("[filename].csv")
```

To generate a dataframe containing partipant performance, run the command below. (note, replace the `*` with the
path/filename of your participant responses `.csv` file and your balloon info `.h5` file:

```Python 3
python generate_summary_dataframe.py --responses_csv=*.csv --balloon_info_h5=*.h5
``` 
This summary dataframe is useful for data analysis.



To fit the BART model to participant data, run the command below. Replace the `*` after --fits_storage= with the
path/name of the folder you wish to store the model fits. Replace the `*` after --fits_tag= with something to
denote the fits

```Python 3
python model.py --responses_csv=*.csv --balloon_info_h5=*.h5 --fits_storage=* --fits_tag=*
```


Citation
--------

If you used *SUPREME* experiments or models for your research, please cite:

```bibtex
   @Misc{SUPREME,
     title = {Quantifying Mechanisms of Cognition with an Experiment and Modeling Ecosystem},
     author = {Weichart, Emily and Darby, Kevin and Fenton, Adam and Jacques, Brandon and Kirkpatrick, Ryan and Turner, Brandon and Sederberg, Per},
     howpublished = {\url{https://github.com/compmem/supreme}},
     year = {2020}
   }
```