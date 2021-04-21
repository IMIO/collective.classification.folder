# -*- coding: utf-8 -*-
from collective.classification.folder.content.classification_folders import IClassificationFolders  # NOQA E501
from collective.classification.folder.testing import COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING  # noqa
from plone import api
from plone.api.exc import InvalidParameterError
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility

import unittest


class ClassificationFoldersIntegrationTest(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

    def test_ct_classification_folders_schema(self):
        fti = queryUtility(IDexterityFTI, name='ClassificationFolders')
        schema = fti.lookupSchema()
        self.assertEqual(IClassificationFolders, schema)

    def test_ct_classification_folders_fti(self):
        fti = queryUtility(IDexterityFTI, name='ClassificationFolders')
        self.assertTrue(fti)

    def test_ct_classification_folders_factory(self):
        fti = queryUtility(IDexterityFTI, name='ClassificationFolders')
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            IClassificationFolders.providedBy(obj),
            u'IClassificationFolders not provided by {0}!'.format(
                obj,
            ),
        )

    def test_ct_classification_folders_adding(self):
        setRoles(self.portal, TEST_USER_ID, ['Contributor'])
        obj = api.content.create(
            container=self.portal,
            type='ClassificationFolders',
            id='classification_folders',
        )

        self.assertTrue(
            IClassificationFolders.providedBy(obj),
            u'IClassificationFolders not provided by {0}!'.format(
                obj.id,
            ),
        )

    def test_ct_classification_folders_globally_addable(self):
        setRoles(self.portal, TEST_USER_ID, ['Contributor'])
        fti = queryUtility(IDexterityFTI, name='ClassificationFolders')
        self.assertTrue(
            fti.global_allow,
            u'{0} is not globally addable!'.format(fti.id)
        )

    def test_ct_classification_folders_filter_content_type_true(self):
        setRoles(self.portal, TEST_USER_ID, ['Contributor'])
        fti = queryUtility(IDexterityFTI, name='ClassificationFolders')
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            fti.id,
            self.portal,
            'classification_folders_id',
            title='ClassificationFolders container',
        )
        self.parent = self.portal[parent_id]
        with self.assertRaises(InvalidParameterError):
            api.content.create(
                container=self.parent,
                type='Document',
                title='My Content',
            )
