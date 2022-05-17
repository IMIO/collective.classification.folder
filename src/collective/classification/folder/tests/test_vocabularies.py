# -*- coding: utf-8 -*-

from collective.classification.folder.content.vocabularies import (
    ClassificationFolderSource,
)
from collective.classification.folder.testing import (
    COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING,
)  # noqa
from dexterity.localroles.utils import add_fti_configuration
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import createObject
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

import unittest


class ClassificationFolderSourceTest(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        # we avoid Anonymous having View permission
        self.portal.manage_permission('View', ('Contributor', 'Editor', 'Manager', 'Reader', 'Site Administrator'),
                                      acquire=0)
        # we configure localroles
        roles_config = {
            'treating_groups': {None: {'': {'roles': ['Contributor', 'Editor']}}},
            'recipient_groups': {None: {'': {'roles': ['Reader']}}}
        }
        for keyname in roles_config:
            add_fti_configuration('ClassificationFolder', roles_config[keyname], keyname=keyname)
            add_fti_configuration('ClassificationSubfolder', roles_config[keyname], keyname=keyname)

        user1 = api.user.create(email="user1@test.com", username="user1")
        api.user.create(email="user2@test.com", username="user2")
        api.group.create(
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
            recipient_groups=[u"group1"],
        )
        self.folder1_uid = api.content.get_uuid(self.folder1)

        self.folder2 = api.content.create(
            container=self.folders,
            type="ClassificationFolder",
            id="folder2",
            title=u"Folder 2",
            recipient_groups=[],
        )
        self.folder2_uid = api.content.get_uuid(self.folder2)

    def test_available_folders_as_manager(self):
        source = ClassificationFolderSource(self.portal)
        terms = [(term.value, term.title) for term in source]
        self.assertEqual(
            [(self.folder1_uid, u"Folder 1"), (self.folder2_uid, u"Folder 2")], terms
        )

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
            type="ClassificationSubfolder",
            id="subfolder1",
            title="Subfolder 1",
            recipient_groups=[],
        )
        self.subfolder_uid = api.content.get_uuid(self.subfolder)
        login(self.portal, "user1")

        source = ClassificationFolderSource(self.portal)
        terms = [(term.value, term.title) for term in source]
        self.assertEqual(
            [
                (self.folder1_uid, u"Folder 1"),
                # (self.subfolder_uid, u"Folder 1 / Subfolder 1"),
            ],
            terms,
        )

    def test_voc_with_reference(self):
        source = ClassificationFolderSource(self.portal)
        self.folder1.internal_reference_no = 'Pastaga'
        notify(ObjectModifiedEvent(self.folder1))
        terms = [(term.value, term.title) for term in source]
        self.assertEqual(
            [(self.folder1_uid, u"Folder 1 (Pastaga)"), (self.folder2_uid, u"Folder 2")], terms
        )
        source = ClassificationFolderSource(self.portal)
        titles = [term.title for term in source.search("Fold pasta")]
        self.assertEqual(titles, [u"Folder 1 (Pastaga)"])


class ClassificationFolderSourceClassificationsTest(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.category_uids = {}
        self.container = api.content.create(
            title="Container", type="ClassificationContainer", container=self.portal
        )
        structure = (
            (u"001", u"First", ((u"001.1", u"first"), (u"001.2", u"second"))),
            (u"002", u"Second", ((u"002.1", u"first"),)),
        )
        for id, title, subelements in structure:
            category = self._create_category(id, title)
            self.container._add_element(category)
            self.category_uids[id] = category.UID()
            if subelements:
                for id, title in subelements:
                    subcategory = self._create_category(id, title)
                    category._add_element(subcategory)
                    self.category_uids[id] = subcategory.UID()
        last_element = category
        category = self._create_category(u"002.1.1", u"first")
        last_element._add_element(category)
        self.category_uids[id] = category.UID()

        self.folders = api.content.create(
            container=self.portal,
            type="ClassificationFolders",
            id="folders",
            title=u"Folders",
        )

    def tearDown(self):
        api.content.delete(self.folders)
        api.content.delete(self.container)

    def _create_category(self, id, title):
        category = createObject("ClassificationCategory")
        category.identifier = id
        category.title = title
        return category

    def _create_folder(self, id, title, container, categories=None):
        if not categories:
            categories = []
        return api.content.create(
            container=container,
            type="ClassificationFolder",
            id=id,
            title=title,
            classification_categories=categories,
        )

    def _create_subfolder(self, id, title, container, categories=None):
        if not categories:
            categories = []
        return api.content.create(
            container=container,
            type="ClassificationSubfolder",
            id=id,
            title=title,
            classification_categories=categories,
        )

    def test_folder_without_categories(self):
        self.folder1 = self._create_folder("folder1", u"Folder 1", self.folders)
        self.folder1_1 = self._create_subfolder(
            "folder1-1", u"Folder 1-1 child", self.folder1
        )
        self.folder2 = self._create_folder("folder2", u"Folder 2", self.folders)

        source = ClassificationFolderSource(self.portal)
        titles = [term.title for term in source.search("Folder")]
        self.assertEqual(titles, [u"Folder 1", u"Folder 1 ⏩ Folder 1-1 child", u"Folder 2"])
        titles = [term.title for term in source.search("Folder 1")]
        self.assertEqual(titles, [u"Folder 1", u"Folder 1 ⏩ Folder 1-1 child"])
        titles = [term.title for term in source.search("Folder 2")]
        self.assertEqual(titles, ["Folder 2"])
        titles = [term.title for term in source.search("Folder child")]
        self.assertEqual(titles, [u"Folder 1 ⏩ Folder 1-1 child"])

    def test_subfolder_inherits_parent_categories(self):
        cat = self.category_uids["001"]
        self.folder1 = self._create_folder(
            "folder1", u"Folder 1", self.folders, categories=[cat]
        )
        self.folder1_1 = self._create_subfolder(
            "folder1-1", u"Folder 1-1", self.folder1
        )
        self.folder2 = self._create_folder("folder2", u"Folder 2", self.folders)

        source = ClassificationFolderSource(self.portal)
        titles = [
            term.title for term in source.search("Folder", categories_filter=[cat])
        ]
        self.assertEqual(titles, [u"Folder 1", u"Folder 1 ⏩ Folder 1-1"])

    def test_no_folder_matches_category(self):
        cat_used = self.category_uids["001"]
        cat_not_used = self.category_uids["002"]

        self.folder1 = self._create_folder(
            "folder1", u"Folder 1", self.folders, categories=[cat_used]
        )
        self.folder1_1 = self._create_subfolder(
            "folder1-1", u"Folder 1-1", self.folder1
        )
        self.folder2 = self._create_folder("folder2", u"Folder 2", self.folders)

        source = ClassificationFolderSource(self.portal)
        titles = [
            term.title
            for term in source.search("Folder", categories_filter=[cat_not_used])
        ]
        self.assertEqual(titles, [u"Folder 1", u"Folder 1 ⏩ Folder 1-1", u"Folder 2"])

    def test_folder_mixed_case_accented_searches(self):
        self._create_folder("folder1", u"Tâche", self.folders)
        self._create_folder("folder2", u"Tache", self.folders)
        self._create_folder("folder3", u"tâche", self.folders)
        self._create_folder("folder4", u"tache", self.folders)

        source = ClassificationFolderSource(self.portal)
        for terms in (u"Tâche", u"Tache", u"tâche", u"tache"):
            titles = [term.title for term in source.search(terms)]
            self.assertEqual(len(titles), 4)

    def test_folder_matches_category_titles(self):
        cat_used = self.category_uids["001"]
        cat_not_used = self.category_uids["002"]

        self.folder1 = self._create_folder(
            "folder1", u"Folder 1", self.folders, categories=[self.category_uids["001"]]
        )
        self.folder1_1 = self._create_subfolder(
            "folder1-1", u"Folder 1-1", self.folder1
        )
        self.folder2 = self._create_folder("folder2", u"Folder 2", self.folders)

        source = ClassificationFolderSource(self.portal)
        titles = [term.title for term in source.search("Folder")]
        self.assertEqual(titles, [u"Folder 1", u"Folder 1 ⏩ Folder 1-1", u"Folder 2"])
        titles = [term.title for term in source.search("Folder First")]
        self.assertEqual(titles, [u"Folder 1", u"Folder 1 ⏩ Folder 1-1"])
