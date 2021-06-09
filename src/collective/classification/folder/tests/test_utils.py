# -*- coding: utf-8 -*-

from collective.classification.folder import testing
from collective.classification.folder import utils
from plone import api
from zope.component import createObject
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

import unittest


class TestUtils(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_FOLDER_FUNCTIONAL_TESTING
    maxDiff = 10000

    def setUp(self):
        self.portal = self.layer["portal"]
        self.folder = api.content.create(
            id="folder", type="Folder", container=self.portal
        )
        container = api.content.create(
            title="Container", type="ClassificationContainer", container=self.folder
        )
        structure = (
            (u"001", u"First", ((u"001.1", u"first 1"), (u"001.2", u"second 1"))),
            (u"002", u"Second", ((u"002.1", u"first"),)),
        )
        for id, title, subelements in structure:
            category = self._create_category(id, title)
            container._add_element(category)
            if subelements:
                for id, title in subelements:
                    subcategory = self._create_category(id, title)
                    category._add_element(subcategory)
        self.folders = api.content.create(
            title="Folders", type="ClassificationFolders", container=self.folder
        )

    def tearDown(self):
        api.content.delete(self.folder)

    def _create_category(self, id, title):
        category = createObject("ClassificationCategory")
        category.identifier = id
        category.title = title
        return category

    @property
    def _tree_vocabulary(self):
        return getUtility(
            IVocabularyFactory,
            "collective.classification.vocabularies:tree_id_mapping",
        )(self.folder)

    def _get_uid(self, value):
        """Return uid from id"""
        return self._tree_vocabulary.getTerm(value).title

    def test_importer_one_level(self):
        self.assertEqual(0, len(self.folders))
        result = utils.importer(
            self.folders,
            None,
            u"F1",
            u"Folder 1",
            data={"classification_categories": [u"001"]},
            _children=[],
        )
        expected_result = (
            "POST",
            {
                "data": [
                    {
                        "@type": "ClassificationFolder",
                        "internal_reference_no": u"F1",
                        "classification_informations": None,
                        "title": u"Folder 1",
                        "classification_categories": [self._get_uid(u"001")],
                    }
                ]
            },
        )
        self.assertEqual(expected_result, result)

    def test_importer_one_level_modified(self):
        api.content.create(
            container=self.folders,
            type="ClassificationFolder",
            internal_reference_no="F1",
            title="Folder 1",
            classification_categories=[self._get_uid(u"001")],
        )
        self.assertEqual(1, len(self.folders))

        # No modification
        result = utils.importer(
            self.folders,
            None,
            u"F1",
            u"Folder 1",
            data={"classification_categories": [u"001"]},
            _children=[],
        )
        expected_result = ("PATCH", {"data": []})
        self.assertEqual(expected_result, result)

        result = utils.importer(
            self.folders,
            None,
            u"F1",
            u"Folder 1 updated",
            data={"classification_categories": [u"001.1"]},
            _children=[],
        )
        expected_result = (
            "PATCH",
            {
                "data": [
                    {
                        "internal_reference_no": u"F1",
                        "title": "Folder 1 updated",
                        "classification_categories": [self._get_uid(u"001.1")],
                    }
                ]
            },
        )
        self.assertEqual(expected_result, result)

    def test_importer_multi_level(self):
        self.assertEqual(0, len(self.folders))
        result = utils.importer(
            self.folders,
            None,
            u"F1",
            u"Folder 1",
            data={"classification_categories": [u"001"]},
            _children=[
                {
                    "internal_reference_no": u"F1.1",
                    "title": u"Folder 1.1",
                    "data": {"classification_categories": [u"001.1"]},
                },
                {
                    "internal_reference_no": u"F1.2",
                    "title": u"Folder 1.2",
                    "data": {"classification_categories": [u"001.2"]},
                },
            ],
        )
        expected_result = (
            "POST",
            {
                "data": [
                    {
                        "@type": "ClassificationFolder",
                        "internal_reference_no": u"F1",
                        "classification_informations": None,
                        "title": u"Folder 1",
                        "classification_categories": [self._get_uid(u"001")],
                        "__children__": [
                            {
                                "@type": "ClassificationSubfolder",
                                "internal_reference_no": u"F1.1",
                                "classification_informations": None,
                                "title": u"Folder 1.1",
                                "classification_categories": [self._get_uid(u"001.1")],
                            },
                            {
                                "@type": "ClassificationSubfolder",
                                "internal_reference_no": u"F1.2",
                                "classification_informations": None,
                                "title": u"Folder 1.2",
                                "classification_categories": [self._get_uid(u"001.2")],
                            },
                        ],
                    }
                ]
            },
        )
        self.assertEqual(expected_result, result)

    def test_importer_multi_level_modified_new_element(self):
        folder = api.content.create(
            container=self.folders,
            type="ClassificationFolder",
            internal_reference_no="F1",
            title="Folder 1",
            classification_categories=[self._get_uid(u"001")],
        )
        api.content.create(
            container=folder,
            type="ClassificationSubfolder",
            internal_reference_no="F1.1",
            title="Folder 1.1",
            classification_categories=[self._get_uid(u"001.1")],
        )
        self.assertEqual(1, len(self.folders))
        result = utils.importer(
            self.folders,
            None,
            u"F1",
            u"Folder 1",
            data={"classification_categories": [u"001"]},
            _children=[
                {
                    "internal_reference_no": u"F1.1",
                    "title": u"Folder 1.1",
                    "data": {"classification_categories": [u"001.1"]},
                },
                {
                    "internal_reference_no": u"F1.2",
                    "title": u"Folder 1.2",
                    "data": {"classification_categories": [u"001.2"]},
                },
            ],
        )
        expected_result = (
            "PATCH",
            {
                "data": [
                    {
                        "internal_reference_no": u"F1",
                        "__children__": [
                            {
                                "@type": "ClassificationSubfolder",
                                "internal_reference_no": u"F1.2",
                                "classification_informations": None,
                                "title": u"Folder 1.2",
                                "classification_categories": [self._get_uid(u"001.2")],
                            },
                        ],
                    }
                ]
            },
        )
        self.assertEqual(expected_result, result)

    def test_importer_multi_level_modified_updated_element(self):
        folder = api.content.create(
            container=self.folders,
            type="ClassificationFolder",
            internal_reference_no="F1",
            title="Folder 1",
            classification_categories=[self._get_uid(u"001")],
        )
        api.content.create(
            container=folder,
            type="ClassificationSubfolder",
            internal_reference_no="F1.1",
            title="Folder 1.1",
            classification_categories=[self._get_uid(u"001.1")],
        )
        api.content.create(
            container=folder,
            type="ClassificationSubfolder",
            internal_reference_no="F1.2",
            title="Folder 1.2",
            classification_categories=[self._get_uid(u"001.2")],
        )
        self.assertEqual(1, len(self.folders))
        result = utils.importer(
            self.folders,
            None,
            u"F1",
            u"Folder 1",
            data={"classification_categories": [u"001"]},
            _children=[
                {
                    "internal_reference_no": u"F1.1",
                    "title": u"Folder 1.1",
                    "data": {"classification_categories": [u"001.1"]},
                },
                {
                    "internal_reference_no": u"F1.2",
                    "title": u"Folder 1.2 updated",
                    "data": {"classification_categories": [u"001.1"]},
                },
            ],
        )
        expected_result = (
            "PATCH",
            {
                "data": [
                    {
                        "internal_reference_no": u"F1",
                        "__children__": [
                            {
                                "internal_reference_no": u"F1.2",
                                "title": u"Folder 1.2 updated",
                                "classification_categories": [self._get_uid(u"001.1")],
                            },
                        ],
                    }
                ]
            },
        )
        self.assertEqual(expected_result, result)
