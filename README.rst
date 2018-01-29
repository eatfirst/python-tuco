========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |appveyor|
        | |coveralls|
        | |landscape|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|

.. |docs| image:: https://readthedocs.org/projects/python-tuco/badge/?style=flat
    :target: https://readthedocs.org/projects/python-tuco
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/eatfirst/python-tuco.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/eatfirst/python-tuco

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/eatfirst/python-tuco?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/eatfirst/python-tuco

.. |coveralls| image:: https://coveralls.io/repos/eatfirst/python-tuco/badge.svg?branch=master&service=github
    :alt: Coverage Status
    :target: https://coveralls.io/r/eatfirst/python-tuco

.. |landscape| image:: https://landscape.io/github/eatfirst/python-tuco/master/landscape.svg?style=flat
    :target: https://landscape.io/github/eatfirst/python-tuco/master
    :alt: Code Quality Status

.. |version| image:: https://img.shields.io/pypi/v/tuco.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/tuco

.. |commits-since| image:: https://img.shields.io/github/commits-since/eatfirst/python-tuco/v0.2.0.svg
    :alt: Commits since latest release
    :target: https://github.com/eatfirst/python-tuco/compare/v0.2.0...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/tuco.svg
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/tuco

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/tuco.svg
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/tuco

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/tuco.svg
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/tuco


.. end-badges

A simple class based finite state machine with parsing time validation

* Free software: MIT license

Installation
============

::

    pip install tuco

Documentation
=============

https://python-tuco.readthedocs.io/

Development
===========
Make sure you have a running redis instance and to run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
