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
from zope.schema import getValidationErrors

import unittest


class ClassificationFolderIntegrationTest(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            'ClassificationFolders',
            self.portal,
            'classification_folder',
            title='Parent container',
        )
        self.parent = self.portal[parent_id]

    def test_ct_classification_folder_schema(self):
        fti = queryUtility(IDexterityFTI, name='ClassificationFolder')
        schema = fti.lookupSchema()
        self.assertEqual(IClassificationFolder, schema)

    def test_ct_classification_folder_fti(self):
        fti = queryUtility(IDexterityFTI, name='ClassificationFolder')
        self.assertTrue(fti)

    def test_ct_classification_folder_factory(self):
        fti = queryUtility(IDexterityFTI, name='ClassificationFolder')
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
            type='ClassificationFolder',
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
        fti = queryUtility(IDexterityFTI, name='ClassificationFolder')
        self.assertFalse(
            fti.global_allow,
            u'{0} is globally addable!'.format(fti.id)
        )

    def test_ct_classification_folder_filter_content_type_true(self):
        setRoles(self.portal, TEST_USER_ID, ['Contributor'])
        fti = queryUtility(IDexterityFTI, name='ClassificationFolder')
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            fti.id,
            self.portal,
            'classification_folder_id',
            title='ClassificationFolder container',
        )
        self.parent = self.portal[parent_id]
        with self.assertRaises(InvalidParameterError):
            api.content.create(
                container=self.parent,
                type='Document',
                title='My Content',
            )

    def test_searchable_text_indexation(self):
        setRoles(self.portal, TEST_USER_ID, ['Contributor'])

        category_container = api.content.create(
            id="container", type="ClassificationContainer", container=self.portal
        )
        category = createObject("ClassificationCategory")
        category.identifier = u"123456789"
        category.title = u"Category_title_123"
        category_container._add_element(category)

        classification_folder = api.content.create(
            container=self.parent,
            type='ClassificationFolder',
            id='classification_folder_searchable',
            title=u"title_123",
            classification_identifier=u"classification_identifier_123",
            classification_categories=[category.UID()],
            classification_informations=u"classification_informations_123",
        )
        classification_folder.reindexObject(idxs=["SearchableText"])

        for text in (
            u"title_123",
            u"classification_identifier_123",
            u"123456789",
            u"Category_title_123",
            u"classification_informations_123",
        ):
            self.assertEquals(len(api.content.find(SearchableText=text)), 1)


class ClassificationFolderUniquenessTest(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            "ClassificationFolders",
            self.portal,
            "classification_folder",
            title="Parent container",
        )
        self.parent = self.portal[parent_id]

        self.category_container = api.content.create(
            id="container", type="ClassificationContainer", container=self.portal
        )
        self.category = createObject("ClassificationCategory")
        self.category.identifier = u"123456789"
        self.category.title = u"Category title"
        self.category_container._add_element(self.category)

        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        first_classification_folder = api.content.create(
            container=self.parent,
            type="ClassificationFolder",
            id="classification_folder_1",
            title=u"Folder 1",
            classification_identifier=u"unique",
        )
        first_classification_folder.reindexObject()

    def tearDown(self):
        api.content.delete(self.parent)
        api.content.delete(self.category_container)

    def test_classification_add_unacceptable(self):
        second_classification_folder = api.content.create(
            container=self.parent,
            type="ClassificationFolder",
            id="classification_folder_2",
            title=u"Folder 2",
            classification_categories=[self.category.UID()],
            classification_identifier=u"unique",
        )
        errors = getValidationErrors(
            IClassificationFolder, second_classification_folder
        )
        self.assertEquals(len(errors), 1)

    def test_classification_edit_acceptable(self):
        second_classification_folder = api.content.create(
            container=self.parent,
            type="ClassificationFolder",
            id="classification_folder_2",
            title=u"Folder 2",
            classification_categories=[self.category.UID()],
            classification_identifier=u"future acceptable",
        )
        errors = getValidationErrors(
            IClassificationFolder, second_classification_folder
        )
        self.assertEquals(len(errors), 0)

        second_classification_folder.classification_identifier = u"still acceptable"
        errors = getValidationErrors(
            IClassificationFolder, second_classification_folder
        )
        self.assertEquals(len(errors), 0)

    def test_classification_edit_unacceptable(self):
        second_classification_folder = api.content.create(
            container=self.parent,
            type="ClassificationFolder",
            id="classification_folder_2",
            title=u"Folder 2",
            classification_categories=[self.category.UID()],
            classification_identifier=u"future unacceptable",
        )
        second_classification_folder.reindexObject()

        errors = getValidationErrors(
            IClassificationFolder, second_classification_folder
        )
        self.assertEquals(len(errors), 0)

        second_classification_folder.classification_identifier = u"unique"
        errors = getValidationErrors(
            IClassificationFolder, second_classification_folder
        )
        self.assertEquals(len(errors), 1)
