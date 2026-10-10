# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from collective.classification.folder.testing import COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING
from collective.classification.folder.testing import MEMBER_ID
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest


class TestSettingsView(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def test___call__(self):
        """The control panel shows the 4 settings to a manager only"""
        html = self.portal.restrictedTraverse("@@collectiveclassificationfolder-settings")()
        for label in (
            u"Number of next folder",
            u"Folder internal reference default value expression",
            u"Number of next subfolder",
            u"Subfolder internal reference default value expression",
        ):
            self.assertIn(label, html)
        self.assertIn(u"python:'F%04d'%int(number)", html)
        login(self.portal, MEMBER_ID)
        self.assertRaises(Unauthorized, self.portal.restrictedTraverse, "@@collectiveclassificationfolder-settings")

    def test_evaluate_tal_expression(self):
        view = self.portal.restrictedTraverse("@@collectiveclassificationfolder-settings")
        folders = api.content.create(container=self.portal, type="ClassificationFolders", id="folders", title=u"Folders")
        self.assertEqual(
            "F0003", view.evaluate_tal_expression(u"python:'F%04d'%int(number)", folders, self.request, self.portal, 3)
        )
        # the variables of the expression
        self.assertEqual(
            "folders-3-plone",
            view.evaluate_tal_expression(
                u"python:'%s-%s-%s' % (context.id, number, portal.id)", folders, self.request, self.portal, 3
            ),
        )
        self.assertEqual(
            "Folders", view.evaluate_tal_expression(u"context/Title", folders, self.request, self.portal, 3)
        )
        self.assertTrue(
            view.evaluate_tal_expression(u"python:date.year() > 2000", folders, self.request, self.portal, 3)
        )
        self.assertEqual(
            "extra", view.evaluate_tal_expression(u"python:extra", folders, self.request, self.portal, 3, extra="extra")
        )
        # an error is returned as the value
        self.assertTrue(
            view.evaluate_tal_expression(u"python:unknown", folders, self.request, self.portal, 3).startswith(
                "Error in expression: "
            )
        )
