from setuptools import setup

setup(
    name='DOCS_CLONE',
    version='0.1',
    packages=['docs_clone'],
    install_requires=[
        'PyQt5',
        'pyqt5-tools',
    ],
    entry_points={
        'console_scripts': [
            'docs_clone = docs_clone.main:main',
        ],
    },
)
