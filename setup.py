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
    description="This is style50, with which you can check code against the CS50 style guide",
    install_requires=["argparse", "autopep8", "backports.shutil_get_terminal_size", "jsbeautifier", "six", "termcolor"],
    keywords=["style", "style50"],
    name="style50",
    packages=find_packages(),
    entry_points={
        "console_scripts": ["style50=style50.__main__:main"],
    },
    url="https://github.com/cs50/style50",
    version="2.0.0"
)
