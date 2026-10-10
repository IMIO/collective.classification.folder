# -*- coding: utf-8 -*-
from collective.classification.folder.browser.tables import SubFoldersFacetedTableView
from collective.classification.folder.testing import COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.batching import Batch

import unittest


class TestSubFoldersFacetedTableView(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def test__getViewFields(self):
        """The table of the subfolders of a folder"""
        portal = self.layer["portal"]
        setRoles(portal, TEST_USER_ID, ["Manager"])
        api.group.create(groupname="service-a", title="Service A")
        folders = api.content.create(container=portal, type="ClassificationFolders", id="folders", title="Folders")
        folder = api.content.create(container=folders, type="ClassificationFolder", id="folder", title="Budget")
        api.content.create(
            container=folder,
            type="ClassificationSubfolder",
            id="subfolder",
            title="Budget 2024",
            internal_reference_no="F0001-01",
            treating_groups="service-a",
        )
        table = SubFoldersFacetedTableView(folder, self.layer["request"])
        table.update(Batch(api.content.find(context=folder, portal_type="ClassificationSubfolder"), 9999))
        self.assertEqual(
            [
                "pretty_link",
                "internal_reference_no",
                "classification_tree_identifiers",
                "classification_treating_group",
            ],
            [c.__name__ for c in table.columns],
        )
        html = table.render()
        for text in ("http://nohost/plone/folders/folder/subfolder", ">Budget 2024<", "F0001-01", "Service A"):
            self.assertIn(text, html)
        self.assertNotIn("_blank", html)  # the subfolder opens in the same window
