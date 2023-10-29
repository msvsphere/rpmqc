from setuptools import find_namespace_packages, setup

with open('README.md', 'r') as fd:
    long_description = fd.read()

setup(
    name='rpmqc',
    version='0.0.4',
    author='Eugene Zamriy',
    author_email='ezamriy@msvsphere-os.ru',
    description='The RPM packages quality control tool',
    license='GPL-2.0-or-later',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/msvsphere/rpmqc',
    project_urls={
        'Bug Tracker': 'https://github.com/msvsphere/rpmqc/issues'
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
        'Topic :: Utilities'
    ],
    packages=find_namespace_packages(include=['msvsphere.*']),
    entry_points={
        'console_scripts': [
            'rpmqc = msvsphere.rpmqc.cli:main'
        ]
    },
    install_requires=[
        'cryptography',
        'importlib-metadata ~= 1.0 ; python_version < "3.8"',
        'pyyaml',
        'schema'
    ],
    python_requires=">=3.6",
    zip_safe=False
)
