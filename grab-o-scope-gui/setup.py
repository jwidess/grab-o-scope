from setuptools import setup, find_packages

setup(
    name='grab-o-scope-gui',
    version='0.1.0',
    author='Jwidess',
    description='A GUI wrapper for the grab-o-scope script to capture oscilloscope screen images.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/jwidess/grab-o-scope',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'pyvisa',
        'pyvisa-py',
        'PyQt5',
        'Pillow',
        'numpy',
        'psutil',
        'zeroconf',
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov',
            'flake8',
            'black',
            'mypy',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'grab-o-scope-gui=main:main',
        ],
    },
)