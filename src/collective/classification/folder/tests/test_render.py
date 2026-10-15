# -*- coding: utf-8 -*-
"""The main pages render on Plone 6 (views, forms, widgets)."""
from collective.classification.folder import testing
from collective.classification.tree.utils import create_category
from lxml import html
from plone import api
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.testing.zope import Browser

import json
import transaction
import unittest


class TestRender(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_FOLDER_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        container = api.content.create(title="Tree", type="ClassificationContainer", container=self.portal)
        self.cat1 = create_category(container, {"identifier": "001", "title": "Finances"}).UID()
        self.cat2 = create_category(container, {"identifier": "002", "title": "Travaux"}).UID()
        api.group.create(groupname="group1", title="Group 1")
        self.folders = api.content.create(title="Folders", type="ClassificationFolders", container=self.portal)
        self.folder1 = api.content.create(
            container=self.folders,
            type="ClassificationFolder",
            title="Budget",
            internal_reference_no="F1",
            classification_categories=[self.cat1],
            treating_groups="group1",
            recipient_groups=["group1"],
        )
        self.folder2 = api.content.create(
            container=self.folders,
            type="ClassificationFolder",
            title="Budget voirie",
            internal_reference_no="F2",
            classification_categories=[self.cat2],
            treating_groups="group1",
        )
        self.subfolder = api.content.create(
            container=self.folder1,
            type="ClassificationSubfolder",
            title="Exercice 2026",
            internal_reference_no="F1-01",
            treating_groups="group1",
        )
        self.item = api.content.create(
            container=self.portal,
            type="testingtype",
            title="Mail",
            classification_folders=[self.subfolder.UID()],
        )
        self.folders()  # the first page rendered writes the Plone Site FTI and footer portlets (CSRF)
        transaction.commit()
        self.browser = Browser(self.layer["app"])
        self.browser.handleErrors = False
        self.browser.addHeader("Authorization", "Basic {0}:{1}".format(TEST_USER_NAME, TEST_USER_PASSWORD))

    def _widget(self, name):
        [widget] = html.fromstring(self.browser.contents).xpath('//*[@name="{0}"]'.format(name))
        return widget

    def test_folders_container(self):
        self.browser.open(self.folders.absolute_url())
        self.assertIn("faceted-form", self.browser.contents)
        self.browser.open(self.folders.absolute_url() + "/@@faceted_query")
        self.assertIn("Budget voirie", self.browser.contents)
        self.assertIn("Budget ⏩ Exercice 2026", self.browser.contents)
        # categories autocomplete criterion
        self.browser.open(self.folders.absolute_url() + "/@@classificationcategory-autocomplete-suggest?term=fin")
        self.assertEqual([{"id": self.cat1, "text": "001 - Finances"}], json.loads(self.browser.contents))

    def test_folder_views(self):
        self.browser.open(self.folder1.absolute_url())
        self.assertIn("faceted-form", self.browser.contents)
        self.browser.open(self.folder1.absolute_url() + "/@@faceted_query")
        contents = self.browser.contents
        self.assertIn("001 - Finances", contents)
        self.assertIn("Group 1", contents)
        self.assertIn("Exercice 2026", contents)  # subfolders table
        self.browser.open(self.subfolder.absolute_url() + "/@@faceted_query")
        self.assertIn("classification_folder_details", self.browser.contents)

    def test_control_panel(self):
        self.browser.open(self.portal.absolute_url() + "/@@collectiveclassificationfolder-settings")
        self.assertEqual("python:'F%04d'%int(number)", self._widget("form.widgets.folder_talexpression").value)

    def test_import(self):
        self.browser.open(self.folders.absolute_url() + "/@@import")
        self.browser.getControl(name="form.widgets.source").add_file(
            "Title;Code;Categories\nImported folder;F9;001\n".encode("utf8"), "text/csv", "folders.csv"
        )
        self.browser.getControl(name="form.widgets.separator:list").value = [";"]
        self.browser.getControl(name="form.buttons.continue").click()
        self.assertTrue(self.browser.url.endswith("/@@import-process"))
        self.browser.getControl(name="form.widgets.column_0:list").value = ["title"]
        self.browser.getControl(name="form.widgets.column_1:list").value = ["internal_reference_no"]
        self.browser.getControl(name="form.widgets.column_2:list").value = ["classification_categories"]
        self.browser.getControl(name="form.buttons.import").click()
        self.assertIn('id="progress"', self.browser.contents)
        self.assertIn(
            self.portal.absolute_url() + "/++resource++collective.classification.folder/progressbar.min.js",
            self.browser.contents,
        )
        self.assertEqual(["F9"], [b.internal_reference_no for b in api.content.find(internal_reference_no="F9")])

    def test_folder_forms(self):
        self.browser.open(self.folders.absolute_url() + "/++add++ClassificationFolder")
        self.assertEqual("F0003", self._widget("form.widgets.internal_reference_no").value)
        self.assertIn("pat-select2", self._widget("form.widgets.recipient_groups").get("class"))
        self.assertIsNotNone(self._widget("form.widgets.treating_groups:list"))
        self.browser.open(self.folder1.absolute_url() + "/edit")
        options = json.loads(self._widget("form.widgets.classification_categories").get("data-pat-select2"))
        self.assertEqual({self.cat1: "001 - Finances"}, options["initialValues"])
        self.browser.getControl(name="form.widgets.classification_categories").value = "{0};{1}".format(
            self.cat1, self.cat2
        )
        self.browser.getControl(name="form.widgets.recipient_groups").value = []
        self.browser.getControl(name="form.buttons.save").click()
        transaction.begin()
        self.assertEqual([self.cat1, self.cat2], self.folder1.classification_categories)
        self.assertEqual([], self.folder1.recipient_groups)
        self.browser.open(options["vocabularyUrl"] + "?query=trav")
        self.assertEqual(["002 - Travaux"], [r["text"] for r in json.loads(self.browser.contents)["results"]])

    def test_item_forms(self):
        name = "form.widgets.IClassificationFolder.classification_folders"
        self.browser.open(self.portal.absolute_url() + "/++add++testingtype")
        self._widget(name)
        self.browser.open(self.item.absolute_url() + "/edit")
        options = json.loads(self._widget(name).get("data-pat-select2"))
        self.assertEqual({self.subfolder.UID(): "Budget ⏩ Exercice 2026 (F1-01) [Group 1]"}, options["initialValues"])
        url = options["vocabularyUrl"]
        self.assertTrue(url.endswith("/++widget++{0}/@@getSource".format(name)))
        self.browser.open(url + "?query=budget")
        self.assertEqual(3, len(json.loads(self.browser.contents)["results"]))
        # filtered by the selected categories (sent by folder_widget.js)
        self.browser.open(url + "?query=budget&categories=" + self.cat2)
        self.assertEqual(
            ["Budget voirie (F2) [Group 1]"], [r["text"] for r in json.loads(self.browser.contents)["results"]]
        )
        # display: pretty links of the folder and subfolder
        self.browser.open(self.item.absolute_url())
        self.assertIn('href="{0}"'.format(self.subfolder.absolute_url()), self.browser.contents)
        self.assertIn('href="{0}"'.format(self.folder1.absolute_url()), self.browser.contents)
