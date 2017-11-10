from setuptools import find_packages, setup

setup(
    author="CS50",
    author_email="sysadmins@cs50.harvard.edu",
    classifiers=[
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3",
        "Topic :: Education",
        "Topic :: Utilities"
    ],
    description="This is style50, with which code can be checked against the CS50 style guide",
    install_requires=["argparse", "autopep8>=1.3.3", "icdiff", "jsbeautifier==1.6.14", "python-magic", "six", "termcolor"],
    dependency_links=["git+https://github.com/jeffkaufman/icdiff.git"],
    keywords=["style", "style50"],
    name="style50",
    license="MIT",
    packages=find_packages(),
    entry_points={
        "console_scripts": ["style50=style50.__main__:main"],
    },
    url="https://github.com/cs50/style50",
    version="2.4.0"
)
