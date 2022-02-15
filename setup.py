from setuptools import setup, find_packages
from setuptools_scm import get_version

readme = open('README.md').read()

VERSION = get_version(root='..', relative_to=__file__)

setup(
    # Metadata
    name='splatpy2',
    version=VERSION,
    author='Teppei Sudo',
    author_email='sudo20.t.ab@gmail.com',
    url='https://github.com/sp-yduck/splatpy2',
    description='A lightweight Python SDK for the Splatoon2 Web API.',
    long_description=readme,
    long_description_content_type='text/markdown',
    license='MIT',

    # Package info
    packages=find_packages(exclude=('*test*',)),

    #
    zip_safe=True,
    use_scm_version=True,
    setup_requires=['setuptools_scm'],

    # Classifiers
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
)