from setuptools import setup, find_packages

setup(
    name='grab-o-scope-gui',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A GUI wrapper for the grab-o-scope script to capture oscilloscope screen images.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/grab-o-scope-gui',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'pyvisa',
        'pyvisa-py',
        'PyQt5',  # or 'PySide2' depending on your choice of GUI framework
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)