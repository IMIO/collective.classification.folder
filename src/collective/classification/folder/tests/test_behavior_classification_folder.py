# -*- coding: utf-8 -*-
from collective.classification.folder.behaviors.classification_folder import classification_folders_indexer
from collective.classification.folder.behaviors.classification_folder import IClassificationFolderMarker
from collective.classification.folder.testing import COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING
from dexterity.localroles.utils import add_fti_configuration
from imio.helpers.test_helpers import ImioTestHelpers
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.behavior.interfaces import IBehavior
from zope.component import getUtility

import unittest


class ClassificationFolderIntegrationTest(unittest.TestCase, ImioTestHelpers):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        # we avoid Anonymous having View permission
        self.portal.manage_permission(
            "View", ("Contributor", "Editor", "Manager", "Reader", "Site Administrator"), acquire=0
        )
        # we configure localroles
        roles_config = {
            "treating_groups": {None: {"": {"roles": ["Contributor", "Editor"]}}},
            "recipient_groups": {None: {"": {"roles": ["Reader"]}}},
        }
        for keyname in roles_config:
            add_fti_configuration("ClassificationFolder", roles_config[keyname], keyname=keyname)
            add_fti_configuration("ClassificationSubfolder", roles_config[keyname], keyname=keyname)

        user1 = api.user.create(email="user1@test.com", username="user1")
        user2 = api.user.create(email="user2@test.com", username="user2")
        api.group.create(groupname="group1", title=u"Group 1")
        api.group.create(groupname="group2", title=u"Group 2")
        api.group.add_user(groupname="group1", user=user1)
        api.group.add_user(groupname="group2", user=user2)

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
            treating_groups="group1",
        )
        self.folder1_uid = api.content.get_uuid(self.folder1)

        self.folder2 = api.content.create(
            container=self.folder1,
            type="ClassificationSubfolder",
            id="folder2",
            title=u"Folder 2",
            treating_groups=u"group2",
        )
        self.folder2_uid = api.content.get_uuid(self.folder2)

        self.tt1 = api.content.create(
            container=self.portal,
            type="testingtype",
            id="tt1",
            title=u"Testing type 1",
        )

    def test_behavior_classification_folder(self):
        behavior = getUtility(
            IBehavior,
            "collective.classification.folder.behaviors.classification_folder.IClassificationFolder",
        )
        self.assertEqual(
            behavior.marker,
            IClassificationFolderMarker,
        )

    def test_classification_folders_indexer(self):
        setRoles(self.portal, TEST_USER_ID, ["Member"])
        self.assertIsNone(api.content.get(UID=self.folder1_uid))
        self.assertIsNone(api.content.get(UID=self.folder2_uid))
        self.change_user("user1")
        self.assertEqual(api.content.get(UID=self.folder1_uid).UID(), self.folder1_uid)
        self.assertIsNone(api.content.get(UID=self.folder2_uid))
        self.change_user("user2")
        self.assertEqual(api.content.get(UID=self.folder2_uid).UID(), self.folder2_uid)
        self.assertIsNone(api.content.get(UID=self.folder1_uid))
        indexer = classification_folders_indexer(self.tt1)
        self.assertEqual(indexer(), ["__empty_string__"])
        self.tt1.classification_folders = [self.folder1_uid]
        self.assertEqual(indexer(), [self.folder1_uid])  # no matter user2 cannot see folder1
        self.tt1.classification_folders = [self.folder2_uid]
        self.assertEqual(indexer(), [self.folder2_uid, "p:{0}".format(self.folder1_uid)])
        self.tt1.classification_folders = [self.folder1_uid, self.folder2_uid]
        self.assertEqual(indexer(), [self.folder1_uid, self.folder2_uid, "p:{0}".format(self.folder1_uid)])
