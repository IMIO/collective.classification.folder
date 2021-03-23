# -*- coding: utf-8 -*-
from collective.classification.folder.content.classification_folder import IClassificationFolder  # NOQA E501
from collective.classification.folder.testing import COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING  # noqa
from plone import api
from plone.api.exc import InvalidParameterError
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility

import unittest


class ClassificationFolderIntegrationTest(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            'Classification Folders',
            self.portal,
            'classification_folder',
            title='Parent container',
        )
        self.parent = self.portal[parent_id]

    def test_ct_classification_folder_schema(self):
        fti = queryUtility(IDexterityFTI, name='Classification Folder')
        schema = fti.lookupSchema()
        self.assertEqual(IClassificationFolder, schema)

    def test_ct_classification_folder_fti(self):
        fti = queryUtility(IDexterityFTI, name='Classification Folder')
        self.assertTrue(fti)

    def test_ct_classification_folder_factory(self):
        fti = queryUtility(IDexterityFTI, name='Classification Folder')
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            IClassificationFolder.providedBy(obj),
            u'IClassificationFolder not provided by {0}!'.format(
                obj,
            ),
        )

    def test_ct_classification_folder_adding(self):
        setRoles(self.portal, TEST_USER_ID, ['Contributor'])
        obj = api.content.create(
            container=self.parent,
            type='Classification Folder',
            id='classification_folder',
        )

        self.assertTrue(
            IClassificationFolder.providedBy(obj),
            u'IClassificationFolder not provided by {0}!'.format(
                obj.id,
            ),
        )

    def test_ct_classification_folder_globally_not_addable(self):
        setRoles(self.portal, TEST_USER_ID, ['Contributor'])
        fti = queryUtility(IDexterityFTI, name='Classification Folder')
        self.assertFalse(
            fti.global_allow,
            u'{0} is globally addable!'.format(fti.id)
        )

    def test_ct_classification_folder_filter_content_type_true(self):
        setRoles(self.portal, TEST_USER_ID, ['Contributor'])
        fti = queryUtility(IDexterityFTI, name='Classification Folder')
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            fti.id,
            self.portal,
            'classification_folder_id',
            title='Classification Folder container',
         )
        self.parent = self.portal[parent_id]
        with self.assertRaises(InvalidParameterError):
            api.content.create(
                container=self.parent,
                type='Document',
                title='My Content',
            )
