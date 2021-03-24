# -*- coding: utf-8 -*-
from collective.classification.folder.behaviors.classification_folder import IClassificationFolderMarker
from collective.classification.folder.testing import COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING  # noqa
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.behavior.interfaces import IBehavior
from zope.component import getUtility

import unittest


class ClassificationFolderIntegrationTest(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

    def test_behavior_classification_folder(self):
        behavior = getUtility(IBehavior, 'collective.classification.folder.classification_folder')
        self.assertEqual(
            behavior.marker,
            IClassificationFolderMarker,
        )
