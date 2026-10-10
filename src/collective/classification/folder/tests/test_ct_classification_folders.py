# -*- coding: utf-8 -*-
from collective.classification.folder.content.classification_folders import (
    IClassificationFolders,
)  # NOQA E501
from collective.classification.folder.testing import (
    COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING,
)  # noqa
from eea.facetednavigation.interfaces import ICriteria
from eea.facetednavigation.interfaces import IFacetedNavigable
from eea.facetednavigation.layout.interfaces import IFacetedLayout
from plone import api
from plone.api.exc import InvalidParameterError
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility

import unittest


class ClassificationFoldersIntegrationTest(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def test_ct_classification_folders_schema(self):
        fti = queryUtility(IDexterityFTI, name="ClassificationFolders")
        schema = fti.lookupSchema()
        self.assertEqual(IClassificationFolders, schema)

    def test_ct_classification_folders_fti(self):
        fti = queryUtility(IDexterityFTI, name="ClassificationFolders")
        self.assertTrue(fti)

    def test_ct_classification_folders_factory(self):
        fti = queryUtility(IDexterityFTI, name="ClassificationFolders")
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            IClassificationFolders.providedBy(obj),
            u"IClassificationFolders not provided by {0}!".format(
                obj,
            ),
        )

    def test_ct_classification_folders_adding(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        obj = api.content.create(
            container=self.portal,
            type="ClassificationFolders",
            id="classification_folders",
        )

        self.assertTrue(
            IClassificationFolders.providedBy(obj),
            u"IClassificationFolders not provided by {0}!".format(
                obj.id,
            ),
        )

    def test_ct_classification_folders_globally_addable(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="ClassificationFolders")
        self.assertTrue(
            fti.global_allow, u"{0} is not globally addable!".format(fti.id)
        )

    def test_ct_classification_folders_filter_content_type_true(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="ClassificationFolders")
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            fti.id,
            self.portal,
            "classification_folders_id",
            title="ClassificationFolders container",
        )
        self.parent = self.portal[parent_id]
        with self.assertRaises(InvalidParameterError):
            api.content.create(
                container=self.parent,
                type="Document",
                title="My Content",
            )


class TestClassificationFoldersModule(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING

    def test_on_create(self):
        """The container is a faceted table of its folders"""
        portal = self.layer["portal"]
        setRoles(portal, TEST_USER_ID, ["Manager"])
        folders = api.content.create(container=portal, type="ClassificationFolders", id="folders", title=u"Folders")
        self.assertTrue(IFacetedNavigable.providedBy(folders))
        self.assertEqual("faceted-table-items", IFacetedLayout(folders).layout)
        criteria = {c.__name__: c for c in ICriteria(folders).values()}
        self.assertEqual(
            [
                ("c0", u"resultsperpage", None),
                ("c1", u"text", u"SearchableText"),
                ("c2", u"sorting", None),
                ("c3", u"criteria", None),
                ("c4", u"path", u"path"),
                ("c5", u"checkbox", u"portal_type"),
                ("c6", u"autocomplete", u"classification_categories"),
            ],
            sorted((k, c.widget, c.get("index") or None) for k, c in criteria.items()),
        )
        self.assertEqual(u"/folders", criteria["c4"].default)
        self.assertEqual([u"ClassificationFolder", u"ClassificationSubfolder"], criteria["c5"].default)
        self.assertEqual(u"ClassificationFolderSort", criteria["c2"].default)
        self.assertEqual(u"classificationcategory-autocomplete-suggest", criteria["c6"].autocomplete_view)
        # Plone 4 bug: enabling the faceted navigation leaves a redirect on the response (a REST call is redirected)
        self.assertEqual(302, self.layer["request"].response.getStatus())
        # the table is shown
        self.assertIn('id="faceted-form"', folders())
