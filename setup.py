# -*- coding: utf-8 -*-
"""Installer for the collective.classification.folder package."""

from setuptools import find_packages
from setuptools import setup


long_description = "\n\n".join(
    [
        open("README.rst").read(),
        open("CONTRIBUTORS.rst").read(),
        open("CHANGES.rst").read(),
    ]
)


setup(
    name="collective.classification.folder",
    version="1.0a2.dev0",
    description="Addon to manage classification folders",
    long_description=long_description,
    # Get more from https://pypi.org/classifiers/
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 4.3",
        "Framework :: Plone :: 6.0",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords="Python Plone CMS",
    author="Martin Peeters",
    author_email="support@imio.be",
    url="https://github.com/collective/collective.classification.folder",
    project_urls={
        "PyPI": "https://pypi.python.org/pypi/collective.classification.folder",
        "Source": "https://github.com/collective/collective.classification.folder",
        "Tracker": (
            "https://github.com/collective/collective.classification.folder/issues"
        ),
        # 'Documentation': 'https://collective.classification.folder.readthedocs.io/en/latest/',
    },
    license="GPL version 2",
    packages=find_packages("src", exclude=["ez_setup"]),
    namespace_packages=["collective", "collective.classification"],
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    python_requires="==2.7",
    install_requires=[
        "setuptools",
        # -*- Extra requirements: -*-
        "z3c.jbot",
        "Products.GenericSetup>=1.8.2",
        "plone.api>=1.8.4",
        "plone.restapi",
        "plone.app.dexterity",
        # "plone.app.referenceablebehavior",  # not py3 compatible
        "plone.app.relationfield",
        "plone.app.lockingbehavior",
        "plone.schema",
        "collective.classification.tree",
        "eea.facetednavigation",
        "collective.eeafaceted.z3ctable",
        "imio.helpers",
        "imio.prettylink",
        "collective.dexteritytextindexer",
        "collective.z3cform.select2",
        "dexterity.localrolesfield",
        "collective.z3cform.chosen; python_version<='2.7.18'",
        "plone.app.contenttypes",
        "plone.formwidget.autocomplete",
        "Unidecode",
    ],
    extras_require={
        "test": [
            "plone.app.testing",
            # Plone KGS does not use this version, because it would break
            # Remove if your package shall be part of coredev.
            # plone_coredev tests as of 2016-04-01.
            "plone.testing",
            "plone.app.robotframework[debug]",
        ]
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    [console_scripts]
    update_locale = collective.classification.folder.locales.update:update_locale
    """,
)
