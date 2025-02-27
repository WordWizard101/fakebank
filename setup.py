from setuptools import setup, find_packages

setup(
    name='fakebank',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Django==5.1.6',
        'psycopg2-binary',
    ],
    description='A Django-based fake banking application for managing user accounts and transactions.',
    author='Matthew Storie',
    author_email='matthewrstorie@gmail.com',
    url='https://github.com/WordWizard101/fakebank',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
    ],
    python_requires='>=3.13',
)
