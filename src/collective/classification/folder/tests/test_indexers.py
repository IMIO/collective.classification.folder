# -*- coding: utf-8 -*-
from collective.classification.folder.content.indexers import archived_classification_folder_index
from collective.classification.folder.content.indexers import classification_categories_index
from collective.classification.folder.content.indexers import classification_folder_sort
from collective.classification.folder.content.indexers import ClassificationSubfolderSearchableText
from collective.classification.folder.testing import COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING
from imio.helpers import EMPTY_STRING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import createObject

import unittest


class TestIndexers(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        tree = api.content.create(container=self.portal, type="ClassificationContainer", id="tree", title=u"Tree")
        category = createObject("ClassificationCategory")
        category.identifier = u"001"
        category.title = u"Administration"
        tree._add_element(category)
        self.category_uid = category.UID()
        folders = api.content.create(container=self.portal, type="ClassificationFolders", id="folders", title=u"Folders")
        self.folder = api.content.create(
            container=folders,
            type="ClassificationFolder",
            id="folder",
            title=u"Folder",
            classification_categories=[self.category_uid],
            archived=True,
        )
        self.subfolder = api.content.create(
            container=self.folder, type="ClassificationSubfolder", id="subfolder", title=u"Subfolder"
        )

    def test_archived_classification_folder_index(self):
        self.assertEqual("1", archived_classification_folder_index(self.folder)())
        self.assertEqual("0", archived_classification_folder_index(self.subfolder)())
        self.assertEqual(["folder"], [b.id for b in api.content.find(yesno_value="1")])

    def test_classification_categories_index(self):
        self.assertEqual([self.category_uid], classification_categories_index(self.folder)())
        # a folder without category can be found in the faceted criterion "no value"
        self.assertEqual([EMPTY_STRING], classification_categories_index(self.subfolder)())
        self.assertEqual(["subfolder"], [b.id for b in api.content.find(classification_categories=EMPTY_STRING)])

    def test_classification_folder_sort(self):
        self.assertEqual(u"Folder", classification_folder_sort(self.folder)())
        self.assertEqual(u"Folder|Subfolder", classification_folder_sort(self.subfolder)())


class TestClassificationSubfolderSearchableText(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def test___call__(self):
        """A subfolder is found by the title of its folder"""
        portal = self.layer["portal"]
        setRoles(portal, TEST_USER_ID, ["Manager"])
        folders = api.content.create(container=portal, type="ClassificationFolders", id="folders", title=u"Folders")
        folder = api.content.create(container=folders, type="ClassificationFolder", id="folder", title=u"Finances")
        subfolder = api.content.create(container=folder, type="ClassificationSubfolder", id="sub", title=u"Budget")
        self.assertEqual("Finances", ClassificationSubfolderSearchableText(subfolder)())
        self.assertEqual(["folder", "sub"], sorted(b.id for b in api.content.find(SearchableText="Finances")))
