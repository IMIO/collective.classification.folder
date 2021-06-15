# -*- coding: utf-8 -*-

from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser import BrowserView
from collective.classification.folder import _
from collective.classification.folder.content.vocabularies import ServiceInChargeSource
from collective.classification.folder.content.vocabularies import ServiceInCopySource
from collective.classification.folder.content.vocabularies import (
    ClassificationFolderSource,
)
from collective.eeafaceted.z3ctable.browser.views import FacetedTableView
from collective.eeafaceted.z3ctable.columns import BaseColumn
from collective.eeafaceted.z3ctable.columns import VocabularyColumn
from collective.eeafaceted.z3ctable.columns import PrettyLinkColumn
from eea.facetednavigation.criteria.handler import Criteria as eeaCriteria
from eea.facetednavigation.interfaces import IFacetedNavigable
from eea.facetednavigation.widgets.storage import Criterion
from persistent.list import PersistentList
from plone import api
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory


class IClassificationFacetedNavigable(IFacetedNavigable):
    """
    More specific IFacetedNavigable to be able to override
    ICriteria adapter only for specific content
    """


class Criteria(eeaCriteria):
    """Handle criteria"""

    def __init__(self, context):
        """Handle criteria"""
        original_context_uid = api.content.get_uuid(context)
        super(Criteria, self).__init__(context)

        portal = api.portal.get()
        self.context = portal["classification_folder_faceted_configuration"]
        self.criteria = PersistentList()

        for crit in self._criteria():
            if crit.index != u"classification_folders" or crit.widget != u"sorting":
                self.criteria.append(crit)

        select_criterion = Criterion(
            **{
                "_cid_": u"restrictfolder",
                "widget": u"select",
                "title": u"Classification folder",
                "index": u"classification_folders",
                "vocabulary": u"",
                "catalog": u"portal_catalog",
                "hidealloption": u"False",
                "position": u"right",
                "section": u"default",
                "hidden": u"True",
                "custom_css": u"",
                "count": u"False",
                "sortcountable": u"False",
                "hidezerocount": u"False",
                "sortreversed": u"False",
                "default": original_context_uid,
            }
        )
        self.criteria.append(select_criterion)

        sort_criterion = Criterion(
            **{
                "_cid_": u"sorton",
                "title": u"Sort on",
                "position": u"top",
                "section": u"default",
                "hidden": u"True",
                "default": u"created(reverse)",
                "widget": u"sorting",
            }
        )
        self.criteria.append(sort_criterion)


class FoldersFacetedTableView(FacetedTableView):
    ignoreColumnWeight = True

    def _getViewFields(self):
        """Returns fields we want to show in the table."""
        return [
            u"pretty_link",
            u"internal_reference_no",
            u"classification_tree_identifiers",
            u"classification_treating_group",
            u"ModificationDate",
            u"CreationDate",
        ]


class FolderFacetedTableView(FacetedTableView):
    ignoreColumnWeight = True

    def _getViewFields(self):
        """Returns fields we want to show in the table."""
        return [
            u"pretty_link",
            u"review_state",
            u"ModificationDate",
            u"CreationDate",
            u"actions",
        ]


class FolderListingView(BrowserView):
    def categories_vocabulary(self):
        return getUtility(
            IVocabularyFactory, "collective.classification.vocabularies:tree"
        )(self.context)

    @property
    def service_in_charge_vocabulary(self):
        if not hasattr(self, "_service_in_charge"):
            self._service_in_charge = ServiceInChargeSource(self.context).vocabulary
        return self._service_in_charge

    @property
    def service_in_copy_vocabulary(self):
        if not hasattr(self, "_service_in_copy"):
            self._service_in_copy = ServiceInCopySource(self.context).vocabulary
        return self._service_in_copy

    def get_service_in_charge(self, value):
        if not value:
            return
        try:
            return self.service_in_charge_vocabulary.getTerm(value).title
        except LookupError:
            return

    def get_service_in_copy(self, value):
        if not value:
            return
        try:
            return self.service_in_copy_vocabulary.getTerm(value).title
        except LookupError:
            return


class FolderTitleColumn(PrettyLinkColumn):

    params = {
        "showIcons": True,
        "showContentIcon": True,
        "display_tag_title": False,
    }

    def contentValue(self, item):
        if hasattr(item, "get_full_title"):
            return item.get_full_title()
        return None


class ClassificationFolderIdColumn(BaseColumn):
    header = _(u"Classification identifier")
    sort_index = "internal_reference_no"

    def renderCell(self, item):
        value = self.getValue(item)
        if not value:
            value = u"-"
        value = safe_unicode(value)
        return value


class ClassificationTreatingGroupColumn(VocabularyColumn):
    header = _(u"Service in charge")
    attrName = u"treating_groups"

    @property
    def _cached_vocab_instance(self):
        if not hasattr(self, "_cached_vocab_instance_value"):
            vocabulary = ServiceInChargeSource(self.context).vocabulary
            self._cached_vocab_instance_value = vocabulary
        return self._cached_vocab_instance_value


class ClassificationTreeIdentifiersColumn(VocabularyColumn):
    header = _(u"Classification categories")
    attrName = u"classification_categories"
    vocabulary = u"collective.classification.vocabularies:tree"


class ClassificationFoldersColumn(VocabularyColumn):
    header = _(u"Classification folders")
    attrName = u"classification_folders"

    @property
    def _cached_vocab_instance(self):
        if not hasattr(self, "_cached_vocab_instance_value"):
            vocabulary = ClassificationFolderSource(self.context).vocabulary
            self._cached_vocab_instance_value = vocabulary
        return self._cached_vocab_instance_value

    def _render_link(self, value):
        return u"<a href='{url}' target='_blank'>{value}</a>".format(
            url=api.content.get(UID=value).absolute_url(),
            value=safe_unicode(self._cached_vocab_instance.getTerm(value).title),
        )

    def renderCell(self, item):
        value = self.getValue(item)
        if not value or value == self.ignored_value:
            return u"-"

        # caching when several same values in same column
        if self.use_caching:
            res = self._get_cached_result(value)
            if res:
                return res

        # make sure we have an iterable
        if not hasattr(value, "__iter__"):
            value = [value]
        res = []
        for v in value:
            try:
                res.append(safe_unicode(self._render_link(v)))
            except LookupError:
                # in case an element is not in the vocabulary, add the value
                res.append(safe_unicode(v))
        res = ", ".join(res)
        if self.use_caching:
            self._store_cached_result(value, res)
        return res
