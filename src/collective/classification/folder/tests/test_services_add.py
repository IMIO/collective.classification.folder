# -*- coding: utf-8 -*-
from collective.classification.folder.services.add import BasePost
from collective.classification.folder.services.add import ImportPost
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

    def post(self, service_class, data):
        """POST of the JSON data to @import, as the import page does"""
        service = service_class()
        service.context = self.folders
        service.request = self.request
        self.request.set("BODY", json.dumps(data))
        return service.reply()


class TestBasePost(ServiceTestCase):

    def test_reply(self):
        """A folder is created with its subfolders"""
        result = self.post(
            BasePost,
            {
                "@type": "ClassificationFolder",
                "title": u"Budget",
                "internal_reference_no": u"F0001",
                "treating_groups": u"service-a",
                "__children__": [
                    {
                        "@type": "ClassificationSubfolder",
                        "title": u"Budget 2024",
                        "internal_reference_no": u"F0001-01",
                        "treating_groups": u"service-a",
                    },
                ],
            },
        )
        self.assertEqual(u"http://nohost/plone/folders/budget", result["@id"])
        self.assertEqual([u"http://nohost/plone/folders/budget/budget-2024"], [c["@id"] for c in result["__children__"]])
        folder = self.folders["budget"]
        self.assertEqual((u"Budget", u"F0001", u"service-a"),
                         (folder.title, folder.internal_reference_no, folder.treating_groups))
        self.assertEqual(u"F0001-01", folder["budget-2024"].internal_reference_no)


class TestImportPost(ServiceTestCase):

    def test_reply(self):
        """Every folder of the data is created"""
        result = self.post(
            ImportPost,
            {
                "data": [
                    {"@type": "ClassificationFolder", "title": u"Budget", "internal_reference_no": u"F0001",
                     "treating_groups": u"service-a"},
                    {"@type": "ClassificationFolder", "title": u"Staff", "internal_reference_no": u"F0002",
                     "treating_groups": u"service-a"},
                ]
            },
        )
        self.assertEqual(["budget", "staff"], sorted(self.folders.keys()))
        # Plone 4 bug: result.extend(dict) adds the keys of the serialized folders instead of the folders
        self.assertEqual(2, result["data"].count(u"@id"))
        self.assertEqual(2, result["data"].count(u"title"))
