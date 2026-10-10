# -*- coding: utf-8 -*-
from collective.classification.folder.testing import COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import createObject

import unittest


WIDGET = "++widget++form.widgets.IClassificationFolder.classification_folders"


class WidgetTestCase(unittest.TestCase):
    """Content classified in folders with the behavior"""

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        tree = api.content.create(container=self.portal, type="ClassificationContainer", id="tree", title=u"Tree")
        category = createObject("ClassificationCategory")
        category.identifier = u"001"
        category.title = u"Administration"
        tree._add_element(category)
        self.category_uid = category.UID()
        folders = api.content.create(container=self.portal, type="ClassificationFolders", id="folders", title=u"Folders")
        self.folder = api.content.create(
            container=folders,
            type="ClassificationFolder",
            id="folder",
            title=u"Staff",
            classification_categories=[self.category_uid],
        )
        self.subfolder = api.content.create(
            container=self.folder, type="ClassificationSubfolder", id="subfolder", title=u"Holidays"
        )
        self.other = api.content.create(container=folders, type="ClassificationFolder", id="other", title=u"Stock")
        self.item = api.content.create(container=self.portal, type="testingtype", id="item", title=u"Item")


class TestFolderAutocompleteSearch(WidgetTestCase):

    def search(self, query, categories=None):
        """The search of the widget of the edit form"""
        view = self.item.restrictedTraverse("@@edit/{0}/@@autocomplete-search".format(WIDGET))
        self.request.other["URL"] = "{0}/@@edit/{1}/@@autocomplete-search".format(self.item.absolute_url(), WIDGET)
        self.request.form.update({"q": query, "categories": categories})
        for key in ("q", "categories"):
            self.request.other.pop(key, None)  # request.get caches the form values in request.other
        return view()

    def test___call__(self):
        self.assertEqual("", self.search(""))
        self.assertEqual(
            "\n".join(
                [
                    "{0}|Staff".format(self.folder.UID()),
                    u"{0}|Staff ⏩ Holidays".format(self.subfolder.UID()),
                    "{0}|Stock".format(self.other.UID()),
                ]
            ),
            self.search("st"),
        )
        self.assertEqual(u"{0}|Staff ⏩ Holidays".format(self.subfolder.UID()), self.search("holi"))
        # the folders of the categories selected in the form come first
        self.assertEqual(
            u"{0}|Staff\n{1}|Staff ⏩ Holidays".format(self.folder.UID(), self.subfolder.UID()),
            self.search("st", categories=self.category_uid),
        )


class TestFolderAutocompleteMultiSelectionWidget(WidgetTestCase):

    def test_pl_items(self):
        """The view of the classified content links to its folders"""
        self.item.classification_folders = [self.folder.UID(), self.subfolder.UID()]
        view = self.item.restrictedTraverse("@@view")
        view.update()
        items = view.w["IClassificationFolder.classification_folders"].pl_items()
        self.assertEqual(2, len(items))
        self.assertEqual(1, items[0].count(u"<a "))
        self.assertIn(u"http://nohost/plone/folders/folder", items[0])
        self.assertIn(u">Staff<", items[0])
        # a subfolder is shown after its folder
        self.assertEqual(2, items[1].count(u"<a "))
        self.assertIn(u">Staff<", items[1])
        self.assertIn(u"http://nohost/plone/folders/folder/subfolder", items[1])
        self.assertIn(u">Holidays<", items[1])
        self.assertIn(u"_blank", items[1])
        self.assertIn(items[1], self.item())
