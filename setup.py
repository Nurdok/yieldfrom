from setuptools import setup

# Don't forget to update __version__ in the module itself.
version = '1.0.0rc'

setup(
    name='yieldfrom',
    version=version,
    description="A backport of the `yield from` semantic from Python 3.x to "
                "Python 2.7",
    long_description=open('README.md').read(),
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
