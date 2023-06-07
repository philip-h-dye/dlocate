from setuptools import setup

setup(
    name='dlocate',
    version='1.9.3',
    description="Parse ~/.updatedb.rc, merge with defaults " +
                "and return configuration as namedtuples.",
    author='Philip H Dye',
    author_email='philip@phd-solutions.com',
    packages=['dlocate'],
    entry_points='''
        [console_scripts]
            dlocate             = dlocate.locate:main
            dupdatedb           = dlocate.updatedb:main
            dupdate             = dlocate.updatedb:main
        ''',
    # install_requires=[], #external packages as dependencies
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
)
