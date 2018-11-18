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
    install_requires=["argparse", "autopep8>=1.3.3", "icdiff", "jsbeautifier", "python-magic", "termcolor"],
    dependency_links=["git+https://github.com/jeffkaufman/icdiff.git"],
    keywords=["style", "style50"],
    name="style50",
    py_requires=">=3.6",
    license="GPLv3",
    packages=find_packages(),
    entry_points={
        "console_scripts": ["style50=style50.__main__:main"],
    },
    url="https://github.com/cs50/style50",
    version="2.6.4"
)
