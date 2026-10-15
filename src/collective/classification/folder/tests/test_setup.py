# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from collective.classification.folder.testing import COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.base.utils import get_installer

import unittest


class CommonSetup:  # noqa

    def set_installer(self):
        self.installer = get_installer(self.portal, self.layer["request"])
        self.ipi = self.installer.is_product_installed


class TestSetup(unittest.TestCase, CommonSetup):
    """Test that collective.classification.folder is properly installed."""

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        self.set_installer()

    def test_product_installed(self):
        """Test if collective.classification.folder is installed."""
        self.assertTrue(self.ipi("collective.classification.folder"))

    def test_browserlayer(self):
        """Test that ICollectiveClassificationFolderLayer is registered."""
        from collective.classification.folder.interfaces import ICollectiveClassificationFolderLayer
        from plone.browserlayer import utils

        self.assertIn(ICollectiveClassificationFolderLayer, utils.registered_layers())

    def test_catalog(self):
        """Indexes and metadata columns of the profile"""
        catalog = api.portal.get_tool("portal_catalog")
        indexes = {
            "ClassificationFolderSort": "FieldIndex",
            "classification_folders": "KeywordIndex",
            "internal_reference_no": "FieldIndex",
            "treating_groups": "KeywordIndex",
            "recipient_groups": "KeywordIndex",
            "yesno_value": "FieldIndex",
        }
        self.assertEqual(indexes, {i: catalog._catalog.getIndex(i).meta_type for i in indexes})
        for column in ("classification_folders", "internal_reference_no", "treating_groups", "recipient_groups"):
            self.assertIn(column, catalog.schema())
        self.assertTrue(api.portal.get_registry_record("plone.app.querystring.field.ClassificationFolderSort.sortable"))

    def test_controlpanel(self):
        """The configlet opens the settings view"""
        configlets = {a.getId(): a for a in api.portal.get_tool("portal_controlpanel").listActions()}
        configlet = configlets["collectiveclassificationfolder.settings"]
        self.assertEqual("Products", configlet.category)
        self.assertEqual(("Plone Site Setup: Site",), configlet.permissions)
        self.assertEqual(
            "string:${portal_url}/@@collectiveclassificationfolder-settings", configlet.getActionExpression()
        )


class TestUninstall(unittest.TestCase, CommonSetup):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.set_installer()
        self.installer.uninstall_product("collective.classification.folder")
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if collective.classification.folder is cleanly uninstalled."""
        self.assertFalse(self.ipi("collective.classification.folder"))

    def test_browserlayer_removed(self):
        """Test that ICollectiveClassificationFolderLayer is removed."""
        from collective.classification.folder.interfaces import ICollectiveClassificationFolderLayer
        from plone.browserlayer import utils

        self.assertNotIn(ICollectiveClassificationFolderLayer, utils.registered_layers())
