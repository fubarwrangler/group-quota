import os.path
import glob

""" Get list of files in this (jobquery) directory not including __init__.py
    and generate a list @module_names from them of the right string to
    pass to __import__() in the getidle.py program
"""

moddir = os.path.dirname(__file__)

mods = [os.path.basename(x) for x in glob.glob(moddir + "/*.py")]
mods.pop(mods.index('__init__.py'))

module_names = [os.path.basename(moddir)+'.'+x[:-3] for x in mods]

__all__ = ['module_names']
