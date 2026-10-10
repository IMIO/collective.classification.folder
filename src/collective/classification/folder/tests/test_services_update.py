# -*- coding: utf-8 -*-
from collective.classification.folder.services.update import BasePatch
from collective.classification.folder.services.update import ImportPatch
from collective.classification.folder.testing import COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import json
import unittest


class ServiceTestCase(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        api.group.create(groupname="service-a", title=u"Service A")
        self.folders = api.content.create(
            container=self.portal, type="ClassificationFolders", id="folders", title=u"Folders"
        )
        self.folder = api.content.create(
            container=self.folders, type="ClassificationFolder", id="budget", title=u"Budget",
            internal_reference_no=u"F0001", treating_groups=u"service-a",
        )
        self.subfolder = api.content.create(
            container=self.folder, type="ClassificationSubfolder", id="budget-2024", title=u"Budget 2024",
            internal_reference_no=u"F0001-01", treating_groups=u"service-a",
        )
        self.other = api.content.create(
            container=self.folders, type="ClassificationFolder", id="staff", title=u"Staff",
            internal_reference_no=u"F0002", treating_groups=u"service-a",
        )

    def patch(self, service_class, data):
        """PATCH of the JSON data to @import, as the import page does"""
        service = service_class()
        service.context = self.folders
        service.request = self.request
        self.request.set("BODY", json.dumps(data))
        return service.reply()


class TestBasePatch(ServiceTestCase):

    def test_reply(self):
        """A folder found by its reference is updated with its subfolders"""
        self.patch(
            BasePatch,
            {
                "internal_reference_no": u"F0001",
                "title": u"Budget updated",
                "__children__": [{"internal_reference_no": u"F0001-01", "title": u"Budget 2024 updated"}],
            },
        )
        self.assertEqual(u"Budget updated", self.folder.title)
        self.assertEqual(u"Budget 2024 updated", self.subfolder.title)
        self.assertRaises(ValueError, self.patch, BasePatch, {"title": u"No reference"})
        self.assertRaises(ValueError, self.patch, BasePatch, {"internal_reference_no": u"F9999"})


class TestImportPatch(ServiceTestCase):

    def test_reply(self):
        self.patch(ImportPatch, {"data": [{"internal_reference_no": u"F0001", "title": u"Budget updated"}]})
        self.assertEqual(u"Budget updated", self.folder.title)
        # Plone 4 bug: the next folders are searched in the previous one (BasePatch.reply replaces self.context)
        self.assertRaises(
            ValueError,
            self.patch,
            ImportPatch,
            {"data": [{"internal_reference_no": u"F0001", "title": u"Budget"},
                      {"internal_reference_no": u"F0002", "title": u"Staff updated"}]},
        )
        self.assertEqual(u"Staff", self.other.title)
