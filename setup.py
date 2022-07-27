#!/usr/bin/env python3
#
#   Copyright 2016 Gogo, LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""Lavatory installer"""

from setuptools import find_packages, setup

with open('requirements.txt', 'rt') as reqs_file:
    REQUIREMENTS = reqs_file.readlines()

setup(
    name='lavatory',
    description='Run retention policies against Artifactory repositories',
    long_description=open('README.rst').read(),
    author='Gogo DevOps',
    author_email='ps-devops-tooling@example.com',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    setup_requires=['setuptools_scm'],
    use_scm_version={'local_scheme': 'dirty-tag'},
    install_requires=REQUIREMENTS,
    include_package_data=True,
    keywords="infrastructure python artifactory jfrog",
    url='https://gitlab.com/remyj38/lavatory',
    download_url='https://gitlab.com/remyj38/lavatory',
    platforms=['OS Independent'],
    license='Apache License (2.0)',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    entry_points={
        'console_scripts': [
            'lavatory=lavatory.__main__:root'
        ]
    },
)
