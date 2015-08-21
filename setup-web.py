# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import os
import os.path


def listdir(dirs, root):
    old = os.getcwd()
    os.chdir(root)
    l = list()
    for D in dirs:
        l.extend([os.path.join(dp, f) for dp, dn, fn in os.walk(D) for f in fn])
    os.chdir(old)
    return l

data_files = listdir(['templates', 'static'], 'gqweb')

setup(
    name='gqweb',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.5.0',

    description='HTCondor Hierarchical Group Management Web Interface',

    # The project's main homepage.
    url='https://github.com/fubarwrangler/group-quota',

    author='William Strecker-Kellogg',
    author_email='willsk-at-bnl.gov',

    # Choose your license
    license='GPLv2',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: System :: Distributed Computing',
        'Framework :: Flask',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],

    install_requires=['Flask', 'SQLAlchemy', 'Flask-Principal', 'gq'],
    # What does your project relate to?
    keywords='htcondor condor group-quota',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['gq', 'gq.*']),
    package_data={'gqweb': data_files},
)
