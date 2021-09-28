# -*- coding: utf-8 -*-
from collective.classification.folder.content.classification_folder import (
    IClassificationFolder,
)  # NOQA E501
from collective.classification.folder.testing import (
    COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING,
)  # noqa
from plone import api
from plone.api.exc import InvalidParameterError
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zExceptions import Redirect
from zope.component import createObject
from zope.component import queryUtility
from zope.event import notify
from zope.lifecycleevent import ObjectCopiedEvent
from zope.lifecycleevent import ObjectModifiedEvent
from zope.lifecycleevent import ObjectMovedEvent
from zope.schema import getValidationErrors

import unittest


class ClassificationFolderIntegrationTest(unittest.TestCase):

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

    def test_ct_classification_folder_schema(self):
        fti = queryUtility(IDexterityFTI, name="ClassificationFolder")
        schema = fti.lookupSchema()
        self.assertEqual(IClassificationFolder, schema)

    def test_ct_classification_folder_fti(self):
        fti = queryUtility(IDexterityFTI, name="ClassificationFolder")
        self.assertTrue(fti)

    def test_ct_classification_folder_factory(self):
        fti = queryUtility(IDexterityFTI, name="ClassificationFolder")
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            IClassificationFolder.providedBy(obj),
            u"IClassificationFolder not provided by {0}!".format(
                obj,
            ),
        )

    def test_ct_classification_folder_adding(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        obj = api.content.create(
            container=self.parent,
            type="ClassificationFolder",
            id="classification_folder",
        )

        self.assertTrue(
            IClassificationFolder.providedBy(obj),
            u"IClassificationFolder not provided by {0}!".format(
                obj.id,
            ),
        )

    def test_ct_classification_folder_globally_not_addable(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="ClassificationFolder")
        self.assertFalse(fti.global_allow, u"{0} is globally addable!".format(fti.id))

    def test_ct_classification_folder_filter_content_type_true(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="ClassificationFolder")
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            fti.id,
            self.portal,
            "classification_folder_id",
            title="ClassificationFolder container",
        )
        self.parent = self.portal[parent_id]
        with self.assertRaises(InvalidParameterError):
            api.content.create(
                container=self.parent,
                type="Document",
                title="My Content",
            )

    def test_searchable_text_indexation(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])

        category_container = api.content.create(
            id="container", type="ClassificationContainer", container=self.portal
        )
        category = createObject("ClassificationCategory")
        category.identifier = u"123456789"
        category.title = u"Category_title_123"
        category_container._add_element(category)

        classification_folder = api.content.create(
            container=self.parent,
            type="ClassificationFolder",
            id="classification_folder_searchable",
            title=u"title_123",
            internal_reference_no=u"internal_reference_no_123",
            classification_categories=[category.UID()],
            classification_informations=u"classification_informations_123",
        )
        classification_folder.reindexObject(idxs=["SearchableText"])

        for text in (
            u"title_123",
            u"internal_reference_no_123",
            u"123456789",
            u"Category_title_123",
            u"classification_informations_123",
        ):
            self.assertEquals(len(api.content.find(SearchableText=text)), 1)


class ClassificationFolderIntegrityTest(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            "ClassificationFolders",
            self.portal,
            "classification_folders",
            title="Parent container",
        )
        self.parent = self.portal[parent_id]

        fti = queryUtility(IDexterityFTI, name="Document")
        behaviors = list(fti.behaviors)
        behavior_name = "collective.classification.folder.behaviors.classification_folder.IClassificationFolder"
        if behavior_name not in behaviors:
            behaviors.append(behavior_name)
        fti._updateProperty("behaviors", tuple(behaviors))

        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        self.classification_folder = api.content.create(
            container=self.parent,
            type="ClassificationFolder",
            id="classification_folder",
        )
        self.classification_folder.reindexObject()

    def tearDown(self):
        api.content.delete(self.parent)

    def test_delete_not_referenced_folder(self):
        api.content.delete(self.classification_folder)

    def test_delete_referenced_folder(self):
        classification_folder_uid = api.content.get_uuid(self.classification_folder)
        document = api.content.create(
            container=self.portal,
            type="Document",
            id="document-referencing",
            classification_folders=[classification_folder_uid],
        )
        document.reindexObject(idxs=["classification_folders"])

        brains = api.content.find(
            context=self.portal, classification_folders=classification_folder_uid
        )
        self.assertEquals(len(brains), 1)
        self.assertEquals(api.content.get_uuid(document), brains[0].UID)

        with self.assertRaises(Redirect):
            api.content.delete(self.classification_folder)


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
            internal_reference_no=u"unique",
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
            internal_reference_no=u"unique",
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
            internal_reference_no=u"future acceptable",
        )
        errors = getValidationErrors(
            IClassificationFolder, second_classification_folder
        )
        self.assertEquals(len(errors), 0)

        second_classification_folder.internal_reference_no = u"still acceptable"
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
            internal_reference_no=u"future unacceptable",
        )
        second_classification_folder.reindexObject()

        errors = getValidationErrors(
            IClassificationFolder, second_classification_folder
        )
        self.assertEquals(len(errors), 0)

        second_classification_folder.internal_reference_no = u"unique"
        errors = getValidationErrors(
            IClassificationFolder, second_classification_folder
        )
        self.assertEquals(len(errors), 1)


class ClassificationFolderMovementTest(unittest.TestCase):

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
        self.first_classification_folder = api.content.create(
            container=self.parent,
            type="ClassificationFolder",
            id="classification_folder_1",
            title=u"Folder1",
            classification_categories=[self.category.UID()],
        )
        self.first_classification_folder.reindexObject()

        self.first_classification_subfolder = api.content.create(
            container=self.first_classification_folder,
            type="ClassificationSubfolder",
            id="classification_subfolder_1",
            title=u"Subfolder1",
            classification_categories=[self.category.UID()],
        )
        self.first_classification_subfolder.reindexObject()

        self.second_classification_folder = api.content.create(
            container=self.parent,
            type="ClassificationFolder",
            id="classification_folder_2",
            title=u"Folder2",
            classification_categories=[self.category.UID()],
        )
        self.second_classification_folder.reindexObject()

    def tearDown(self):
        api.content.delete(self.parent)
        api.content.delete(self.category_container)

    def get_index_data(self, obj):
        uid = api.content.get_uuid(obj)
        brain = api.content.find(UID=uid)[0]
        return self.portal.portal_catalog.getIndexDataForRID(brain.getRID())

    def test_basic_indexes(self):
        subfolder_indexes = self.get_index_data(self.first_classification_subfolder)
        self.assertEqual(subfolder_indexes["ClassificationFolderSort"], "Folder1|Subfolder1")
        self.assertIn("folder1", subfolder_indexes["SearchableText"])

    def test_rename_parent_folder(self):
        self.first_classification_folder.title = "Folder1b"
        notify(ObjectModifiedEvent(self.first_classification_folder))

        subfolder_indexes = self.get_index_data(self.first_classification_subfolder)
        self.assertEqual(subfolder_indexes["ClassificationFolderSort"], "Folder1b|Subfolder1")
        self.assertIn("folder1b", subfolder_indexes["SearchableText"])

    def test_move_subfolder(self):
        cookie = self.first_classification_folder.manage_cutObjects(ids=("classification_subfolder_1",))
        self.second_classification_folder.manage_pasteObjects(cookie)

        notify(
            ObjectMovedEvent(
                self.first_classification_subfolder,
                self.first_classification_folder,
                "classification_subfolder_1",
                self.second_classification_folder,
                "classification_subfolder_1",
            )
        )

        subfolder_indexes = self.get_index_data(self.first_classification_subfolder)
        self.assertEqual(subfolder_indexes["ClassificationFolderSort"], "Folder2|Subfolder1")
        self.assertIn("folder2", subfolder_indexes["SearchableText"])

    def test_copy_subfolder(self):
        copied_subfolder = api.content.copy(self.first_classification_subfolder, self.second_classification_folder)

        notify(
            ObjectCopiedEvent(
                self.first_classification_subfolder,
                copied_subfolder,
            )
        )

        copied_subfolder_indexes = self.get_index_data(copied_subfolder)
        self.assertEqual(copied_subfolder_indexes["ClassificationFolderSort"], "Folder2|Subfolder1")
        self.assertIn("folder2", copied_subfolder_indexes["SearchableText"])
