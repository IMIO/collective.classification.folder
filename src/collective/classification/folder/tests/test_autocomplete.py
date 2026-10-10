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
        tree = api.content.create(container=self.portal, type="ClassificationContainer", id="tree", title=u"Tree")
        self.category_uids = []
        for identifier, title in ((u"001", u"Administration"), (u"002", u"Finances")):
            category = createObject("ClassificationCategory")
            category.identifier = identifier
            category.title = title
            tree._add_element(category)
            self.category_uids.append(category.UID())
        folders = api.content.create(container=self.portal, type="ClassificationFolders", id="folders", title=u"Folders")
        self.folder = api.content.create(container=folders, type="ClassificationFolder", id="folder", title=u"Budget")
        self.subfolder = api.content.create(
            container=self.folder, type="ClassificationSubfolder", id="subfolder", title=u"Budget 2024"
        )

    def suggest(self, name, term):
        self.request.form["term"] = term
        self.request.other.pop("term", None)  # request.get caches the form values in request.other
        result = json.loads(self.portal.restrictedTraverse(name)())
        self.assertEqual("application/json", self.request.response.getHeader("Content-type"))
        return result


class TestAutocomplete(unittest.TestCase):

    def test_parse_query(self):
        self.assertEqual({"SearchableText": "Budget* AND 2024*"}, parse_query(u"Budget 2024"))
        self.assertEqual({"SearchableText": "a* AND b* AND c*"}, parse_query(u"a-b (c?)"))
        self.assertEqual({"SearchableText": ""}, parse_query(u""))


class TestClassificationCategorySuggest(AutocompleteTestCase):

    def test___call__(self):
        self.assertEqual([], self.suggest("@@classificationcategory-autocomplete-suggest", u""))
        self.assertEqual(
            [{u"id": self.category_uids[1], u"text": u"002 - Finances"}],
            self.suggest("@@classificationcategory-autocomplete-suggest", u"finan"),
        )
        self.assertEqual(
            [self.category_uids[0], self.category_uids[1]],
            [r[u"id"] for r in self.suggest("@@classificationcategory-autocomplete-suggest", u"00")],
        )
        # the "no value" choice, to find the folders without category
        self.assertEqual(
            [{u"id": EMPTY_STRING, u"text": u"No value"}],
            self.suggest("@@classificationcategory-autocomplete-suggest", u"no val"),
        )


class TestFolderSuggest(AutocompleteTestCase):

    def test___call__(self):
        self.assertEqual([], self.suggest("@@folder-autocomplete-suggest", u""))
        # Plone 4 bug: the view reads the get_full_title metadata, which only imio.dms.mail adds to the catalog
        self.assertRaises(AttributeError, self.suggest, "@@folder-autocomplete-suggest", u"budg")
        api.portal.get_tool("portal_catalog").addColumn("get_full_title")
        self.folder.reindexObject()
        self.subfolder.reindexObject()
        self.assertEqual(
            [
                {u"id": self.folder.UID(), u"text": u"Budget"},
                {u"id": self.subfolder.UID(), u"text": u"Budget ⏩ Budget 2024"},
            ],
            self.suggest("@@folder-autocomplete-suggest", u"budg"),
        )
        self.assertEqual(
            [self.subfolder.UID()], [r[u"id"] for r in self.suggest("@@folder-autocomplete-suggest", u"2024")]
        )
        self.assertEqual(
            [{u"id": EMPTY_STRING, u"text": u"No value"}], self.suggest("@@folder-autocomplete-suggest", u"no val")
        )
