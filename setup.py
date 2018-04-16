#!/usr/bin/env python
from setuptools import setup, find_packages

test_deps = [
    'coverage',
    'pytest-cov',
    'pytest',
    'httmock',
]

extras = {
    'testing': test_deps,
}

setup(
    name='stmocli',
    version='0.1',
    description='CLI for managing re:dash queries in plain text.',
    author='Ryan Harter',
    author_email='harterrt@mozilla.com',
    url='https://github.com/harterrt/stmocli',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=[
        "redash-client",
        "click",
    ],
    tests_require=test_deps,
    extras_require=extras,
    entry_points={
        "console_scripts": [
            "stmocli=stmocli.cli:cli",
        ]
    },
)
