# -*- coding: utf-8 -*-
from collective.classification.folder import setuphandlers
from collective.classification.folder.testing import COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING
from eea.facetednavigation.interfaces import ICriteria
from eea.facetednavigation.interfaces import IFacetedNavigable
from plone import api

import unittest


REGISTRY_KEY = "collective.classification.folder.browser.settings.IClassificationConfig.{0}"


class TestSetuphandlers(unittest.TestCase):
    """The post install handler ran when the testing profile was applied"""

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]

    def test_create_classification_folder_facet(self):
        folder = self.portal["classification_folder_faceted_configuration"]
        self.assertEqual("Folder", folder.portal_type)
        self.assertTrue(folder.exclude_from_nav)
        self.assertTrue(IFacetedNavigable.providedBy(folder))
        criteria = ICriteria(folder)
        self.assertEqual(
            [(u"criteria", u"Current search"), (u"resultsperpage", u"Results per page"), (u"sorting", u"Sort on")],
            [(c.widget, c.title) for c in criteria.values()],
        )
        self.assertEqual(u"created(reverse)", criteria.get("c1").default)
        # a second call keeps the existing configuration
        setuphandlers.create_classification_folder_facet()
        self.assertEqual(3, len(ICriteria(self.portal["classification_folder_faceted_configuration"]).values()))

    def test_set_registry(self):
        self.assertEqual(1, api.portal.get_registry_record(REGISTRY_KEY.format("folder_number")))
        self.assertEqual(
            u"python:'F%04d'%int(number)", api.portal.get_registry_record(REGISTRY_KEY.format("folder_talexpression"))
        )
        self.assertEqual(1, api.portal.get_registry_record(REGISTRY_KEY.format("subfolder_number")))
        self.assertEqual(
            u"python:'%s-xx'%(context.internal_reference_no)",
            api.portal.get_registry_record(REGISTRY_KEY.format("subfolder_talexpression")),
        )
        # a second call keeps the values set in the control panel
        api.portal.set_registry_record(REGISTRY_KEY.format("folder_number"), 12)
        setuphandlers.set_registry()
        self.assertEqual(12, api.portal.get_registry_record(REGISTRY_KEY.format("folder_number")))

    def test_create_annexes_config(self):
        config = self.portal["annexes_types"]
        self.assertEqual("ContentCategoryConfiguration", config.portal_type)
        self.assertTrue(config.exclude_from_nav)
        setuphandlers.create_annexes_config()
        self.assertEqual(["annexes_types"], [k for k in self.portal.keys() if k.startswith("annexes_types")])


class TestHiddenProfiles(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def test_getNonInstallableProfiles(self):
        self.assertEqual(
            ["collective.classification.folder:uninstall"], setuphandlers.HiddenProfiles().getNonInstallableProfiles()
        )
