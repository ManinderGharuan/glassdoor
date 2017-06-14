from setuptools import setup

setup(
    name='glassdoor',
    packages=['glassdoor'],
    include_package_data=True,
    install_requires=[
        'flask',
        'beautifulsoup4',
        'requests'
    ],
)
