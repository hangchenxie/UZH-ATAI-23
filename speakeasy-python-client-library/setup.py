from setuptools import setup, find_packages

name = "speakeasypy"
version = "1.0.0"
description = "demo for speakeasypy"
author = "Hangchen Xie"
author_email = "Hangchen Xie@uzh.ch"
url = "https://gitlab.ifi.uzh.ch/ddis/Lectures/atai/speakeasy-python-client-library"

install_requires = open("requirements.txt").read().split('\n')

packages = find_packages()

setup(
    name=name,
    version=version,
    description=description,
    author=author,
    author_email=author_email,
    url=url,
    packages=packages,
    python_requires='>=3.6',
    install_requires=install_requires,
)
