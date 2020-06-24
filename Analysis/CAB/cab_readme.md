SUPREME continuous associative binding model
============================================

This is the model of the continuous associative binding (CAB) task paradigm that is included in *SUPREME*
(Sensing to Understanding and Prediction Realized via an Experiment and Modeling
Ecosystem). After data has been acquired with the CAB task, users can
gain insight into latent mechanisms by fitting the model. Data are first
converted to a readable format using functions in `smile`_. The Python-based
model uses `RunDEMC`_ to calculate a posterior distribution for each parameter
via Bayesian-inspired methods.

`_smile: https://github.com/compmem/smile`
`_RunDEMC: http://github.com/compmem/RunDEMC`

It requires Python 3, as well as the following packages and versions:
`NumPy`_ (v1.18.1),
`Pandas`_ (v1.0.1),
`scoop`_ (v0.7),
`scipy`_ (v1.4.1),

`_NumPy: https://www.numpy.org/`
`_Pandas: https://pandas.pydata.org/`
`_scoop: https://github.com/soravux/scoop`
`_scipy: https://www.scipy.org/`

How to install the correct version of RunDEMC:
```bash
git clone https://github.com/compmem/RunDEMC.git
cd RunDEMC
git checkout f2d07db
python setup.py install
```

Fitting the model
-----------------

These instructions describe how to fit the *SUPREME* CAB model to data
from one subject. First, convert the relevant *smile* data log (slog) for your
subject to a CSV using the following Python code:

```python
from smile.log import log2dl
import pandas as pd

data = pd.DataFrame(log2dl("[subject]/[session]/log_cont_ass_bind_0.slog"))
data.to_csv("[filename].csv")
```

​You can then fit the model to your data from the command prompt using the
following line:

```bash
python -m scoop cab_SUPREME.py [filename].csv
```

Citation
--------

If you used *SUPREME* experiments or models for your research, please cite:

.. code:: bibtex

   @Misc{SUPREME,
     title = {Quantifying Mechanisms of Cognition with an Experiment and Modeling Ecosystem},
     author = {Weichart, Emily and Darby, Kevin and Fenton, Adam and Jacques, Brandon and Kirkpatrick, Ryan and Turner, Brandon and Sederberg, Per},
     howpublished = {\url{https://github.com/compmem/supreme}},
     year = {2020}
   }
