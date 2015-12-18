# Always prefer setuptools over distutils
from setuptools import setup, find_packages

setup(
    name='gq',

    version='1.0.1',

    description='HTCondor Hierarchical Group Management Software Library',

    # The project's main homepage.
    url='https://github.com/fubarwrangler/group-quota',

    author='William Strecker-Kellogg',
    author_email='willsk-at-bnl.gov',

    # Choose your license
    license='GPLv2',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: Developers',
        'Topic :: System :: Distributed Computing',
        'Topic :: Scientific/Engineering',

        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    install_requires=['MySQL-python'],
    keywords='htcondor condor group-quota flask',
    packages=find_packages(exclude=['gqweb.*', 'gqweb']),
    package_data={'gq.config': ['*.cfg']},
)
