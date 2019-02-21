from setuptools import setup

VERSION = '0.3.0'
BASE_CVS_URL = 'https://github.com/carmelom/optivis'

setup(
    name='optivis',
    packages=['optivis', ],
    version=VERSION,
    author='SeanDS',
    author_email='author@email.com',
    install_requires=[x.strip() for x in open('requirements.txt').readlines()],
    url=BASE_CVS_URL,
    download_url='{}/tarball/{}'.format(BASE_CVS_URL, VERSION),
    test_suite='tests',
    tests_require=[x.strip() for x in open('requirements_test.txt').readlines()],
    keywords=[],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Operating System :: OS Independent",
    ],
)
