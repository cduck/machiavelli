from setuptools import setup, find_packages
import logging
logger = logging.getLogger(__name__)

name = 'machiavelli'
package_name = name
version = '0.1.0'
base_url = 'https://github.com/cduck'

try:
    with open('README.md', 'r') as f:
        long_desc = f.read()
except:
    logger.warning('Could not open README.md.  long_description will be set to None.')
    long_desc = None

setup(
    name = package_name,
    packages = find_packages(),
    entry_points = {
        'console_scripts': [
            'machiavelli=machiavelli.command:run_from_command_line',
        ]},
    version = version,
    description = 'Solver for the card game Machiavelli',
    long_description = long_desc,
    long_description_content_type = 'text/markdown',
    author = 'Casey Duckering',
    #author_email = '',
    url = f'{base_url}/{name}',
    download_url = f'{base_url}/{name}/archive/{version}.tar.gz',
    keywords = ['card game', 'game', 'CSP'],
    classifiers = [
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    install_requires = [
        'numpy~=1.11',
        'cvxpy~=1.1',
        'cvxopt~=1.2',
        'termcolor~=1.1',
        'colorama~=0.3',
    ],
)

