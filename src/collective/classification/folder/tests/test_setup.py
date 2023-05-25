# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from collective.classification.folder import PLONE_VERSION
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from collective.classification.folder.testing import (
    COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING,
)  # noqa: E501

import unittest


try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


class TestSetup(unittest.TestCase):
    """Test that collective.classification.folder is properly installed."""

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")

    def test_product_installed(self):
        """Test if collective.classification.folder is installed."""
        if PLONE_VERSION >= '5.1':
            self.assertTrue(
                self.installer.is_product_installed("collective.classification.folder"))
        else:
            self.assertTrue(
                self.installer.isProductInstalled("collective.classification.folder"))

    def test_browserlayer(self):
        """Test that ICollectiveClassificationFolderLayer is registered."""
        from collective.classification.folder.interfaces import (
            ICollectiveClassificationFolderLayer,
        )
        from plone.browserlayer import utils

        self.assertIn(ICollectiveClassificationFolderLayer, utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
            self.installer.uninstall_product("collective.classification.folder")
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")
            self.installer.uninstallProducts(["collective.classification.folder"])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if collective.classification.folder is cleanly uninstalled."""
        if PLONE_VERSION >= '5.1':
            self.assertFalse(
                self.installer.is_product_installed("collective.classification.folder"))
        else:
            self.assertFalse(
                self.installer.isProductInstalled("collective.classification.folder"))

    def test_browserlayer_removed(self):
        """Test that ICollectiveClassificationFolderLayer is removed."""
        from collective.classification.folder.interfaces import (
            ICollectiveClassificationFolderLayer,
        )
        from plone.browserlayer import utils

        self.assertNotIn(
            ICollectiveClassificationFolderLayer, utils.registered_layers()
        )
