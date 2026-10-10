# -*- coding: utf-8 -*-
from collective.classification.folder.testing import COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import createObject

import unittest


REGISTRY_KEY = "collective.classification.folder.browser.settings.IClassificationConfig.{0}"


class DataProviderTestCase(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        api.group.create(groupname="service-a", title=u"Service A")
        api.group.create(groupname="service-b", title=u"Service B")
        tree = api.content.create(container=self.portal, type="ClassificationContainer", id="tree", title=u"Tree")
        category = createObject("ClassificationCategory")
        category.identifier = u"001"
        category.title = u"Administration"
        tree._add_element(category)
        self.category_uid = category.UID()
        self.folders = api.content.create(
            container=self.portal, type="ClassificationFolders", id="folders", title=u"Folders"
        )

    def add_form(self, container, portal_type):
        """The add form as shown to the user"""
        view = container.restrictedTraverse("++add++{0}".format(portal_type))
        view.update()
        return view.form_instance


class TestFolderDataProvider(DataProviderTestCase):

    def test_get(self):
        """The default reference of a new folder comes from the expression and the counter of the settings"""
        form = self.add_form(self.folders, "ClassificationFolder")
        self.assertEqual(u"F0001", form.widgets["internal_reference_no"].value)
        self.assertEqual(u"", form.widgets["title"].value)
        api.portal.set_registry_record(REGISTRY_KEY.format("folder_number"), 12)
        api.portal.set_registry_record(REGISTRY_KEY.format("folder_talexpression"), u"python:'D-%s' % number")
        form = self.add_form(self.folders, "ClassificationFolder")
        self.assertEqual(u"D-12", form.widgets["internal_reference_no"].value)


class TestSubfolderDataProvider(DataProviderTestCase):

    def test_get(self):
        """A new subfolder gets the reference, categories and services of its folder"""
        folder = api.content.create(
            container=self.folders,
            type="ClassificationFolder",
            id="folder",
            title=u"Folder",
            internal_reference_no=u"F0001",
            classification_categories=[self.category_uid],
            treating_groups=u"service-a",
            recipient_groups=[u"service-b"],
        )
        form = self.add_form(folder, "ClassificationSubfolder")
        self.assertEqual(u"F0001-xx", form.widgets["internal_reference_no"].value)
        self.assertEqual([self.category_uid], form.widgets["classification_categories"].value)
        self.assertEqual([u"service-a"], form.widgets["treating_groups"].value)
        self.assertEqual([u"service-b"], form.widgets["recipient_groups"].value)
        self.assertEqual(u"", form.widgets["title"].value)
        # an annex added in the folder has an empty description
        form = self.add_form(folder, "annex")
        self.assertEqual(u"", form.widgets["description"].value)
