from setuptools import setup, find_packages

setup(name='redisjobs',
    description='A Python interface to the Jobs scheduler.',
    long_description=open('README.rst').read(),
    author='Stijn Debrouwere',
    author_email='stijn@debrouwere.org',
    url='https://github.com/debrouwere/jobs.py',
    download_url='https://github.com/debrouwere/jobs.py/tarball/master',
    version='0.5.0', 
    license='ISC',
    packages=find_packages(),
    keywords='scheduler scheduling jobs tasks asynchronous',
    install_requires=[
        'redis', 
    ], 
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        ],
    )
