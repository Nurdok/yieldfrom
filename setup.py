import os

from setuptools import setup

# Don't forget to update __version__ in the module itself.
version = '1.0.2rc'

with open(os.path.join(os.path.dirname(__file__), "README.md")) as readme:
    long_description = readme.read()

setup(
    name='yieldfrom',
    version=version,
    description="A backport of the `yield from` semantic from Python 3.x to "
                "Python 2.7",
    long_description=long_description,
    license='MIT',
    author='Amir Rachum',
    author_email='amir@rachum.com',
    url='https://github.com/Nurdok/yieldfrom/',
    classifiers=[
        'Intended Audience :: Developers',
        'Environment :: Console',
        'Programming Language :: Python :: 2',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ],
    keywords='yield, from, yield from, generators, backport',
    py_modules=('yieldfrom',),
)
