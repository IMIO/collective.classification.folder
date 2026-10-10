# -*- coding: utf-8 -*-
from collective.classification.folder.content.classification_subfolder import (
    IClassificationSubfolder,
)  # NOQA E501
from collective.classification.folder.testing import (
    COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING,
)  # noqa
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility

import unittest


class ClassificationSubfolderIntegrationTest(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            "ClassificationFolder",
            self.portal,
            "classification_subfolder",
            title="Parent container",
        )
        self.parent = self.portal[parent_id]

    def test_ct_classification_subfolder_schema(self):
        fti = queryUtility(IDexterityFTI, name="ClassificationSubfolder")
        schema = fti.lookupSchema()
        self.assertEqual(IClassificationSubfolder, schema)

    def test_ct_classification_subfolder_fti(self):
        fti = queryUtility(IDexterityFTI, name="ClassificationSubfolder")
        self.assertTrue(fti)

    def test_ct_classification_subfolder_factory(self):
        fti = queryUtility(IDexterityFTI, name="ClassificationSubfolder")
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            IClassificationSubfolder.providedBy(obj),
            u"IClassificationSubfolder not provided by {0}!".format(
                obj,
            ),
        )

    def test_ct_classification_subfolder_adding(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        obj = api.content.create(
            container=self.parent,
            type="ClassificationSubfolder",
            id="classification_subfolder",
        )

        self.assertTrue(
            IClassificationSubfolder.providedBy(obj),
            u"IClassificationSubfolder not provided by {0}!".format(
                obj.id,
            ),
        )

    def test_ct_classification_subfolder_globally_not_addable(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="ClassificationSubfolder")
        self.assertFalse(fti.global_allow, u"{0} is globally addable!".format(fti.id))


class TestClassificationSubfolder(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        portal = self.layer["portal"]
        setRoles(portal, TEST_USER_ID, ["Manager"])
        folders = api.content.create(container=portal, type="ClassificationFolders", id="folders", title=u"Folders")
        self.folder = api.content.create(container=folders, type="ClassificationFolder", id="folder", title=u"Tâche")
        self.subfolder = api.content.create(
            container=self.folder, type="ClassificationSubfolder", id="subfolder", title=u"Sous-tâche"
        )

    def test_cf_parent(self):
        self.assertEqual(self.folder, self.subfolder.cf_parent())

    def test_get_full_title(self):
        self.assertEqual(u"Tâche ⏩ Sous-tâche", self.subfolder.get_full_title())
