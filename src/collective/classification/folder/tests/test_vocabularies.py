# -*- coding: utf-8 -*-
from collective.classification.folder.content.vocabularies import ClassificationFolderSource
from collective.classification.folder.testing import COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING  # noqa
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest


class ClassificationFolderSourceTest(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        user1 = api.user.create(email="user1@test.com", username="user1")
        user2 = api.user.create(email="user2@test.com", username="user2")
        group1 = api.group.create(
            groupname="group1",
            title=u"Group 1",
        )
        api.group.add_user(groupname="group1", user=user1)

        self.folders = api.content.create(
            container=self.portal,
            type="ClassificationFolders",
            id="folders",
            title=u"Folders",
        )

        self.folder1 = api.content.create(
            container=self.folders,
            type="ClassificationFolder",
            id="folder1",
            title=u"Folder 1",
            services_in_copy=["group1"],
        )
        self.folder1_uid = api.content.get_uuid(self.folder1)

        self.folder2 = api.content.create(
            container=self.folders,
            type="ClassificationFolder",
            id="folder2",
            title=u"Folder 2",
            services_in_copy=[],
        )
        self.folder2_uid = api.content.get_uuid(self.folder2)

    def test_available_folders_as_manager(self):
        source = ClassificationFolderSource(self.portal)
        terms = [(term.value, term.title) for term in source]
        self.assertEqual([(self.folder1_uid, u"Folder 1"), (self.folder2_uid, u"Folder 2")], terms)

    def test_available_folders_as_groupmember(self):
        login(self.portal, "user1")
        source = ClassificationFolderSource(self.portal)
        terms = [(term.value, term.title) for term in source]
        self.assertEqual([(self.folder1_uid, u"Folder 1")], terms)

    def test_available_folders_as_lambda(self):
        login(self.portal, "user2")
        source = ClassificationFolderSource(self.portal)
        terms = [(term.value, term.title) for term in source]
        self.assertEqual([], terms)

    def test_available_folders_inheritance(self):

        self.subfolder = api.content.create(
            container=self.folder1,
            type='ClassificationSubfolder',
            id='subfolder1',
            title='Subfolder 1',
            services_in_copy=[],
        )
        self.subfolder_uid = api.content.get_uuid(self.subfolder)
        login(self.portal, "user1")

        source = ClassificationFolderSource(self.portal)
        terms = [(term.value, term.title) for term in source]
        self.assertEqual([(self.folder1_uid, u"Folder 1"), (self.subfolder_uid, u"Folder 1 >> Subfolder 1")], terms)

