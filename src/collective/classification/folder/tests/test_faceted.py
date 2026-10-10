# -*- coding: utf-8 -*-
from collective.classification.folder.browser.faceted import annex_classification_folders_indexer
from collective.classification.folder.browser.faceted import ClassificationFoldersColumn
from collective.classification.folder.testing import COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING
from eea.facetednavigation.interfaces import ICriteria
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.batching import Batch
from plone.namedfile.file import NamedBlobFile
from plone.namedfile.file import NamedBlobImage
from z3c.table.interfaces import IColumn
from zope.component import createObject
from zope.component import getMultiAdapter

import base64
import unittest


# a 1x1 PNG image
ICON = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


class FacetedTestCase(unittest.TestCase):
    """A folder with a subfolder, annexes and a classified item"""

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
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
        self.folder = api.content.create(
            container=self.folders,
            type="ClassificationFolder",
            id="folder",
            title=u"Budget",
            internal_reference_no=u"F0001",
            classification_categories=[self.category_uid],
            treating_groups=u"service-a",
            recipient_groups=[u"service-b"],
            classification_informations=u"Yearly budget",
        )
        self.subfolder = api.content.create(
            container=self.folder,
            type="ClassificationSubfolder",
            id="subfolder",
            title=u"Budget 2024",
            internal_reference_no=u"F0001-01",
            treating_groups=u"service-b",
            archived=True,
        )
        group = api.content.create(
            container=self.portal["annexes_types"], type="ContentCategoryGroup", id="annexes", title=u"Annexes"
        )
        api.content.create(
            container=group,
            type="ContentCategory",
            id="annex",
            title=u"Annex",
            icon=NamedBlobImage(ICON, filename=u"annex.png"),
        )
        self.annex = self.add_annex(self.folder, "annex", u"report.txt")
        self.subannex = self.add_annex(self.subfolder, "subannex", u"invoice.txt")
        self.item = api.content.create(
            container=self.portal,
            type="testingtype",
            id="item",
            title=u"Mail",
            classification_folders=[self.subfolder.UID()],
        )

    def add_annex(self, container, id, filename):
        return api.content.create(
            container=container,
            type="annex",
            id=id,
            title=id.capitalize(),
            file=NamedBlobFile(b"0123456789", filename=filename),
            content_category="annexes_types_-_annexes_-_annex",
        )

    def table(self, context, brains):
        """The table of the faceted view, updated with the results"""
        table = context.restrictedTraverse("@@faceted-table-view")
        table.update(Batch(brains, 20))
        return table

    def column(self, context, name, brains):
        """A column of the table of the context, as the dashboards of an application use them"""
        table = self.table(context, brains)
        return table.nameColumn(getMultiAdapter((context, self.request, table), IColumn, name=name), name)

    def brain(self, obj):
        return api.content.find(UID=obj.UID())[0]

    def folder_contents(self, folder):
        """The results of the faceted view of a folder: what is classified in it"""
        return api.content.find(classification_folders=[folder.UID(), "p:{0}".format(folder.UID())], sort_on="id")


class TestFacetedModule(FacetedTestCase):

    def test_annex_classification_folders_indexer(self):
        self.assertEqual([self.folder.UID()], annex_classification_folders_indexer(self.annex)())
        self.assertEqual(
            [self.subfolder.UID(), "p:{0}".format(self.folder.UID())],
            annex_classification_folders_indexer(self.subannex)(),
        )
        self.assertEqual(["annex", "item", "subannex"], [b.id for b in self.folder_contents(self.folder)])
        self.assertEqual(["item", "subannex"], [b.id for b in self.folder_contents(self.subfolder)])


class TestCriteria(FacetedTestCase):

    def test___init__(self):
        """The criteria of the folders come from the configuration folder, restricted to the folder"""
        criteria = ICriteria(self.subfolder)
        self.assertEqual(
            [u"criteria", u"resultsperpage", u"sorting", u"multiselect"], [c.widget for c in criteria.values()]
        )
        restrict = criteria.get("restrictfolder")
        self.assertEqual(u"classification_folders", restrict.index)
        self.assertEqual([self.subfolder.UID(), "p:{0}".format(self.subfolder.UID())], restrict.default)
        self.assertTrue(restrict.hidden)
        self.assertEqual(
            [self.folder.UID(), "p:{0}".format(self.folder.UID())], ICriteria(self.folder).get("restrictfolder").default
        )


class TestFoldersFacetedTableView(FacetedTestCase):

    def test__getViewFields(self):
        """The table of the folders container"""
        brains = api.content.find(
            path="/plone/folders",
            portal_type=["ClassificationFolder", "ClassificationSubfolder"],
            sort_on="ClassificationFolderSort",
        )
        table = self.table(self.folders, brains)
        self.assertEqual(
            [
                u"pretty_link",
                u"internal_reference_no",
                u"classification_tree_identifiers",
                u"classification_treating_group",
                u"ModificationDate",
                u"CreationDate",
            ],
            [c.__name__ for c in table.columns],
        )
        html = table.render()
        for text in (u"Budget", u"Budget ⏩ Budget 2024", u"F0001-01", u"001 - Administration", u"Service B"):
            self.assertIn(text, html)


class TestFolderFacetedTableView(FacetedTestCase):

    def test__getViewFields(self):
        """The table of a folder: what is classified in it"""
        table = self.table(self.folder, self.folder_contents(self.folder))
        self.assertEqual(
            [u"pretty_link", u"subfolder_classification_folders", u"state_filesize", u"ModificationDate",
             u"CreationDate", u"actions"],
            [c.__name__ for c in table.columns],
        )
        html = table.render()
        for text in (u"Annex", u"report.txt", u"Mail", u"Budget 2024", u"10 B"):
            self.assertIn(text, html)
        # a subfolder doesn't show the subfolder column
        table = self.table(self.subfolder, self.folder_contents(self.subfolder))
        self.assertEqual(
            [u"pretty_link", u"state_filesize", u"ModificationDate", u"CreationDate", u"actions"],
            [c.__name__ for c in table.columns],
        )


class TestFolderListingView(FacetedTestCase):

    def view(self, folder):
        return folder.restrictedTraverse("@@folder-listing-view")

    def test_categories_vocabulary(self):
        self.assertEqual(u"001 - Administration", self.view(self.folder).categories_vocabulary().getTerm(
            self.category_uid).title)

    def test_service_in_charge_vocabulary(self):
        self.assertIn(u"service-a", [t.value for t in self.view(self.folder).service_in_charge_vocabulary])

    def test_service_in_copy_vocabulary(self):
        self.assertIn(u"service-b", [t.value for t in self.view(self.folder).service_in_copy_vocabulary])

    def test_get_service_in_charge(self):
        view = self.view(self.folder)
        self.assertEqual(u"Service A", view.get_service_in_charge(u"service-a"))
        self.assertIsNone(view.get_service_in_charge(None))
        self.assertIsNone(view.get_service_in_charge(u"unknown"))

    def test_get_service_in_copy(self):
        view = self.view(self.folder)
        self.assertEqual(u"Service B", view.get_service_in_copy(u"service-b"))
        self.assertIsNone(view.get_service_in_copy(None))
        self.assertIsNone(view.get_service_in_copy(u"unknown"))

    def test_get_subfolder_table(self):
        html = self.view(self.folder).get_subfolder_table()
        for text in (u"Budget 2024", u"F0001-01", u"Service B"):
            self.assertIn(text, html)
        self.assertNotIn(u"Holidays", html)

    def test___call__(self):
        """The view of a folder, as shown by the faceted navigation: its fields, its subfolders, its content"""
        html = self.folder.restrictedTraverse("@@faceted_query")()
        for text in (u"F0001", u"001 - Administration", u"Service A", u"Service B", u"Yearly budget",
                     u'id="classification_subfolders"', u"Budget 2024", u"report.txt", u"Mail", u"Total: 20 B"):
            self.assertIn(text, html)
        self.assertNotIn(u'id="classification_folder_details"', html)
        # a subfolder shows the details of its folder
        html = self.subfolder.restrictedTraverse("@@faceted_query")()
        for text in (u"F0001-01", u'id="classification_folder_details"', u"Yearly budget", u"invoice.txt", u"Mail"):
            self.assertIn(text, html)
        self.assertNotIn(u"report.txt", html)
        self.assertNotIn(u'id="classification_subfolders"', html)


class TestFolderTitleColumn(FacetedTestCase):

    def test_getPrettyLink(self):
        column = self.column(self.folder, "pretty_link", self.folder_contents(self.folder))
        link = column.getPrettyLink(self.annex)
        self.assertIn(u"http://nohost/plone/folders/folder/annex", link)
        self.assertIn(u'<div class="discreet type-text-widget annex-filename">report.txt</div>', link)
        self.assertIn(u"_blank", link)
        link = column.getPrettyLink(self.subfolder)
        self.assertIn(u">Budget ⏩ Budget 2024<", link)

    def test_contentValue(self):
        column = self.column(self.folders, "pretty_link", [])
        self.assertIsNone(column.contentValue(self.folder))
        self.assertEqual(u"Budget ⏩ Budget 2024", column.contentValue(self.subfolder))


class TestClassificationFolderTitleColumn(FacetedTestCase):

    def test_renderCell(self):
        """In a dashboard of folders and subfolders: the folder"""
        column = self.column(self.folders, "classification_folder_title", [])
        self.assertIn(u">Budget<", column.renderCell(self.brain(self.folder)))
        cell = column.renderCell(self.brain(self.subfolder))
        self.assertIn(u">Budget<", cell)
        self.assertIn(u"http://nohost/plone/folders/folder'", cell.replace(u'"', u"'"))


class TestClassificationSubfolderTitleColumn(FacetedTestCase):

    def test_getPrettyLink(self):
        column = self.column(self.folders, "classification_subfolder_title", [])
        self.assertEqual("-", column.getPrettyLink(self.folder))
        self.assertIn(u">Budget 2024<", column.getPrettyLink(self.subfolder))


class TestClassificationFolderIdColumn(FacetedTestCase):

    def test_renderCell(self):
        column = self.column(self.folders, "internal_reference_no", [])
        self.assertEqual(u"F0001-01", column.renderCell(self.brain(self.subfolder)))
        self.folder.internal_reference_no = None
        self.folder.reindexObject()
        self.assertEqual(u"-", column.renderCell(self.brain(self.folder)))


class TestClassificationTreatingGroupColumn(FacetedTestCase):

    def test_renderCell(self):
        """The title of the service in charge"""
        column = self.column(self.folders, "classification_treating_group", [])
        self.assertEqual(u"Service A", column.renderCell(self.brain(self.folder)))
        self.assertEqual(u"Service B", column.renderCell(self.brain(self.subfolder)))


class TestClassificationTreeIdentifiersColumn(FacetedTestCase):

    def test_renderCell(self):
        """The titles of the categories"""
        column = self.column(self.folders, "classification_tree_identifiers", [])
        self.assertEqual(u"001 - Administration", column.renderCell(self.brain(self.folder)))
        self.assertEqual(u"-", column.renderCell(self.brain(self.subfolder)))


class TestClassificationFolderArchivedColumn(FacetedTestCase):

    def test_getValue(self):
        """The archived state of the folder, also on its subfolders"""
        column = self.column(self.folders, "classification_folder_archived", [])
        self.assertEqual("0", column.getValue(self.brain(self.folder)))
        self.assertEqual("0", column.getValue(self.brain(self.subfolder)))
        self.folder.archived = True
        self.assertEqual("1", column.getValue(self.brain(self.subfolder)))


class TestClassificationSubfolderArchivedColumn(FacetedTestCase):

    def test_getValue(self):
        column = self.column(self.folders, "classification_subfolder_archived", [])
        self.assertEqual("", column.getValue(self.brain(self.folder)))
        self.assertEqual("1", column.getValue(self.brain(self.subfolder)))


class TestClassificationFoldersColumn(FacetedTestCase):

    def test_renderCell(self):
        """The folders of a classified item, in the dashboards of an application (not registered here)"""
        column = ClassificationFoldersColumn(self.folders, self.request, self.table(self.folders, []))
        column.__name__ = column.attrName
        cell = column.renderCell(self.brain(self.item))
        self.assertEqual(1, cell.count(u"<a "))
        self.assertIn(u"http://nohost/plone/folders/folder/subfolder", cell)
        self.assertIn(u">Budget ⏩ Budget 2024<", cell)
        self.assertNotIn(u"p:" + self.folder.UID(), cell)  # the parent folder, indexed for the faceted view, is not shown
        self.item.classification_folders = [self.folder.UID(), self.subfolder.UID()]
        self.item.reindexObject()
        self.assertEqual(2, column.renderCell(self.brain(self.item)).count(u"<a "))
        self.item.classification_folders = []
        self.item.reindexObject()
        self.assertEqual(u"-", column.renderCell(self.brain(self.item)))


class TestSubfolderClassificationFoldersColumn(FacetedTestCase):

    def test__get_title(self):
        """In the table of a folder: the subfolder in which an element is classified"""
        column = self.column(self.folder, "subfolder_classification_folders", self.folder_contents(self.folder))
        self.assertIsNone(column._get_title(self.folder))
        self.assertEqual(u"Budget 2024", column._get_title(self.subfolder))
        self.assertEqual(u"Budget 2024", column.renderCell(self.brain(self.subannex)).split(u">")[1].split(u"<")[0])
        self.assertEqual(u"-", column.renderCell(self.brain(self.annex)))
        # a subfolder of another folder is shown with its full title
        other = api.content.create(container=self.folders, type="ClassificationFolder", id="other", title=u"Other")
        column = self.column(other, "subfolder_classification_folders", [])
        self.assertEqual(u"Budget ⏩ Budget 2024", column._get_title(self.subfolder))


class TestCombinedReviewstateSizeColumn(FacetedTestCase):

    def test_renderHeadCell(self):
        """The total size of the annexes of the page"""
        column = self.column(self.folder, "state_filesize", self.folder_contents(self.folder))
        self.assertIn(u"<p>(Total: 20 B)</p>", column.renderHeadCell())

    def test_renderCell(self):
        """The size of an annex, the state of other elements"""
        column = self.column(self.folder, "state_filesize", self.folder_contents(self.folder))
        self.assertEqual(u"10 B", column.renderCell(self.brain(self.annex)))
        self.assertEqual(u"Private", column.renderCell(self.brain(self.item)))
        # Plone 4 bug: an element without workflow (review_state Missing.Value) breaks the column
        self.assertRaises(TypeError, column.renderCell, self.brain(self.subfolder))
