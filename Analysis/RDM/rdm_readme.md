SUPREME RDM model
=====================

This is the model of the random-dot motion (RDM) task paradigm that is included in *SUPREME*
(Sensing to Understanding and Prediction Realized via an Experiment and Modeling
Ecosystem). After data has been acquired with the RDM task, users can
gain insight into latent mechanisms by fitting the model. Data are first
converted to a readable format using functions in `smile`_. The Python-based
model uses `RunDEMC`_ to calculate a posterior distribution for each parameter
via Bayesian-inspired methods.

`_smile: https://github.com/compmem/smile`
`_RunDEMC: http://github.com/compmem/RunDEMC`

It requires Python 3.4, as well as the following packages and versions:
`NumPy`_ (v1.16.4),
`Pandas`_ (v0.24.2),
`scoop`_ (v0.7),
`numba`_ (v0.45.0)

`_NumPy: https://www.numpy.org/`
`_Pandas: https://pandas.pydata.org/`
`_scoop: https://github.com/soravux/scoop`
`_numba: https://numba.pydata.org/`


How to install the correct version of RunDEMC:
```bash
git clone https://github.com/compmem/RunDEMC.git
cd RunDEMC
git checkout f2d07db
python setup.py install
```

Fitting the model
-----------------

These instructions describe how to fit the *SUPREME* RDM model to data
from one subject. First, convert the relevant *smile* data log (slog) for your
subject to a CSV using the following Python code:

```python
from smile.log import log2dl
import pandas as pd

data = pd.DataFrame(log2dl("[subject]/[session]/log_MD_0.slog"))
data.to_csv("[filename].csv")
```

You can then fit the model to your data from the command prompt using the
following line:

```bash
python -m scoop rdm_SUPREME.py [filename].csv
```

Calculating Posterior Predictive Distributions
-----------------
 
The following code can be used to generate Posterior Predictive Distributions:

```bash
python -m scoop rdm_lca_calc_ppds.py [filename].csv
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
