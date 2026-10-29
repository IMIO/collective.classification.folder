# -*- coding: utf-8 -*-
from collective.classification.folder.testing import COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest


class TestClassificationHelper(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def test_can_import(self):
        """The import action of collective.classification.tree is shown on the folders container"""
        portal = self.layer["portal"]
        setRoles(portal, TEST_USER_ID, ["Manager"])
        folders = api.content.create(container=portal, type="ClassificationFolders", id="folders", title="Folders")
        helper = folders.restrictedTraverse("@@classification_helper")
        self.assertTrue(helper.can_import())
        self.assertFalse(helper.can_add_category())
        actions = api.portal.get_tool("portal_actions").listFilteredActionsFor(folders)["object_buttons"]
        self.assertIn("http://nohost/plone/folders/@@import", [a["url"] for a in actions])
