#!/usr/bin/env bash
#py_env for imaris-yuqi
# windows python3.7, and apache-maven
# To use:
#  1. open gitbash
#  2. run this script (bash imaris_py37.bash)
#     Alternativly, use "source imaris_py37.bash" to allow starting arbirary python code easily.
#     ex (after the source command): python example_ij_classifier.py
#

# check for pip, which indicates we're in a "ready" python env.
if which python &> /dev/null;
then
    # use the workstation(or system) python
    py_dir=$(dirname $(which python));
fi;
# Or specify a path to the python you want.
# DO NOT use python 39. imaris is picky about only accepting python37
# py_dir=/k/DevApps/python/python39
# py_dir=/L/DevApps/python/python39
# py_dir=/L/DevApps/python/python37
py_dir=/k/DevApps/python/python37
ims_dir="/c/Program Files/bitplane/imaris 9.9.0"
pyxt_dir="$ims_dir/xt/python3";
export PATH="$py_dir:$py_dir/Scripts:$ims_dir:$pyxt_dir:$PATH";
# pyimagej requires apache-maven. (It's a simple download and unpack to get it.)
if ! which mvn &> /dev/null
then
    export PATH="$PATH:$(cygpath -u $WORKSTATION_AUX/apache-maven-3.9.6/bin)"
fi;
# this is how you open a new python shell (from git bash shell)
#start python
#python MainAlgor\ -\ multiRegions.py;
