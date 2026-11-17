# -*- coding: utf-8 -*-
from collective.classification.folder.browser.autocomplete import parse_query
from collective.classification.folder.testing import COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING
from imio.helpers import EMPTY_STRING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import createObject

import json
import unittest


class AutocompleteTestCase(unittest.TestCase):
    """Categories and folders to suggest"""

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        tree = api.content.create(container=self.portal, type="ClassificationContainer", id="tree", title="Tree")
        self.category_uids = []
        for identifier, title in (("001", "Administration"), ("002", "Finances")):
            category = createObject("ClassificationCategory")
            category.identifier = identifier
            category.title = title
            tree._add_element(category)
            self.category_uids.append(category.UID())
        folders = api.content.create(container=self.portal, type="ClassificationFolders", id="folders", title="Folders")
        self.folder = api.content.create(container=folders, type="ClassificationFolder", id="folder", title="Budget")
        self.subfolder = api.content.create(
            container=self.folder, type="ClassificationSubfolder", id="subfolder", title="Budget 2024"
        )

    def suggest(self, name, term):
        self.request.form["term"] = term
        self.request.other.pop("term", None)  # request.get caches the form values in request.other
        result = json.loads(self.portal.restrictedTraverse(name)())
        self.assertEqual("application/json", self.request.response.getHeader("Content-type"))
        return result


class TestAutocomplete(unittest.TestCase):

    def test_parse_query(self):
        self.assertEqual({"SearchableText": "Budget* AND 2024*"}, parse_query("Budget 2024"))
        self.assertEqual({"SearchableText": "a* AND b* AND c*"}, parse_query("a-b (c?)"))
        # an empty SearchableText matches nothing since ZCatalog 4 (ignored on Plone 4): no criterion
        self.assertEqual({}, parse_query(""))


class TestClassificationCategorySuggest(AutocompleteTestCase):

    def test___call__(self):
        self.assertEqual([], self.suggest("@@classificationcategory-autocomplete-suggest", ""))
        self.assertEqual(
            [{"id": self.category_uids[1], "text": "002 - Finances"}],
            self.suggest("@@classificationcategory-autocomplete-suggest", "finan"),
        )
        self.assertEqual(
            [self.category_uids[0], self.category_uids[1]],
            [r["id"] for r in self.suggest("@@classificationcategory-autocomplete-suggest", "00")],
        )
        # the "no value" choice, to find the folders without category
        self.assertEqual(
            [{"id": EMPTY_STRING, "text": "No value"}],
            self.suggest("@@classificationcategory-autocomplete-suggest", "no val"),
        )


class TestFolderSuggest(AutocompleteTestCase):

    def test___call__(self):
        self.assertEqual([], self.suggest("@@folder-autocomplete-suggest", ""))
        # Plone 4 bug: the view reads the get_full_title metadata, which only imio.dms.mail adds to the catalog
        self.assertRaises(AttributeError, self.suggest, "@@folder-autocomplete-suggest", "budg")
        api.portal.get_tool("portal_catalog").addColumn("get_full_title")
        self.folder.reindexObject()
        self.subfolder.reindexObject()
        self.assertEqual(
            [
                {"id": self.folder.UID(), "text": "Budget"},
                {"id": self.subfolder.UID(), "text": "Budget ⏩ Budget 2024"},
            ],
            self.suggest("@@folder-autocomplete-suggest", "budg"),
        )
        self.assertEqual(
            [self.subfolder.UID()], [r["id"] for r in self.suggest("@@folder-autocomplete-suggest", "2024")]
        )
        self.assertEqual(
            [{"id": EMPTY_STRING, "text": "No value"}], self.suggest("@@folder-autocomplete-suggest", "no val")
        )
