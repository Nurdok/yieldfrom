import os

from setuptools import setup

version = '1.0.3'

with open(os.path.join(os.path.dirname(__file__), "README.md")) as readme:
    long_description = readme.read()

setup(
    name='yieldfrom',
    version=version,
    description="A backport of the `yield from` semantic from Python 3.x to "
                "Python 2.7",
    long_description=long_description,
    long_description_content_type='text/markdown',
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
    keywords='yield,from,yield from,generators,backport,iterators',
    py_modules=('yieldfrom',),
)
