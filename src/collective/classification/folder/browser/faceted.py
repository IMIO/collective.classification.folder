# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from Acquisition import aq_parent
from collective.classification.folder import _
from collective.classification.folder.browser.tables import SubFoldersFacetedTableView
from collective.classification.folder.content.vocabularies import ClassificationFolderSource
from collective.classification.folder.content.vocabularies import ServiceInChargeSource
from collective.classification.folder.content.vocabularies import ServiceInCopySource
from collective.eeafaceted.z3ctable.browser.views import FacetedTableView
from collective.eeafaceted.z3ctable.columns import BaseColumn
from collective.eeafaceted.z3ctable.columns import ColorColumn
from collective.eeafaceted.z3ctable.columns import PrettyLinkColumn
from collective.eeafaceted.z3ctable.columns import VocabularyColumn
from collective.iconifiedcategory import utils
from eea.facetednavigation.criteria.handler import Criteria as eeaCriteria
from eea.facetednavigation.interfaces import IFacetedNavigable
from eea.facetednavigation.widgets.storage import Criterion
from imio.annex.content.annex import IAnnex
from imio.prettylink.interfaces import IPrettyLink
from persistent.list import PersistentList
from plone import api
from plone.base.utils import base_hasattr
from plone.base.utils import safe_text
from plone.batching import Batch
from plone.indexer import indexer
from Products.Five.browser import BrowserView
from zope.component import getUtility
from zope.i18n import translate
from zope.schema.interfaces import IVocabularyFactory


class IClassificationFacetedNavigable(IFacetedNavigable):
    """
    More specific IFacetedNavigable to be able to override
    ICriteria adapter only for specific content
    """


@indexer(IAnnex)
def annex_classification_folders_indexer(obj):
    """Custom indexer on annex, so an annex can be used in faceted criteria"""
    parent = aq_parent(obj)
    parent_pt = parent.portal_type
    values = []
    if parent_pt == "ClassificationFolder":
        values.append(parent.UID())
    elif parent_pt == "ClassificationSubfolder":
        values.append(parent.UID())
        values.append("p:{0}".format(aq_parent(parent).UID()))
    return values


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
            if crit.index != "classification_folders":
                self.criteria.append(crit)

        default = [
            original_context_uid,
            "p:{0}".format(original_context_uid),
        ]
        select_criterion = Criterion(
            **{
                "_cid_": "restrictfolder",
                "widget": "multiselect",
                "title": "Classification folder",
                "index": "classification_folders",
                "vocabulary": "",
                "catalog": "portal_catalog",
                "hidealloption": "False",
                "position": "right",
                "section": "default",
                "hidden": "True",
                "custom_css": "",
                "count": "False",
                "sortcountable": "False",
                "hidezerocount": "False",
                "sortreversed": "False",
                "operator": "or",
                "multiple": True,
                "default": default,
            }
        )
        self.criteria.append(select_criterion)


class FoldersFacetedTableView(FacetedTableView):
    ignoreColumnWeight = True

    def _getViewFields(self):
        """Returns fields we want to show in the table."""
        return [
            "pretty_link",
            "internal_reference_no",
            "classification_tree_identifiers",
            "classification_treating_group",
            "ModificationDate",
            "CreationDate",
        ]


class FolderFacetedTableView(FacetedTableView):
    ignoreColumnWeight = True

    def _getViewFields(self):
        """Returns fields we want to show in the table."""
        if self.context.portal_type == "ClassificationSubfolder":
            return [
                "pretty_link",
                "state_filesize",
                "ModificationDate",
                "CreationDate",
                "actions",
            ]
        else:
            return [
                "pretty_link",
                "subfolder_classification_folders",
                "state_filesize",
                "ModificationDate",
                "CreationDate",
                "actions",
            ]


class FolderListingView(BrowserView):
    def categories_vocabulary(self):
        return getUtility(IVocabularyFactory, "collective.classification.vocabularies:tree")(self.context)

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

    def get_subfolder_table(self):
        view = SubFoldersFacetedTableView(self.context, self.request)
        data = api.content.find(
            context=self.context,
            portal_type="ClassificationSubfolder",
        )
        return view.render_table(Batch(data, 9999))


class FolderTitleColumn(PrettyLinkColumn):
    """Prettylink column for combined titles. If contentValue is None, Title is used."""

    params = {
        "showIcons": True,
        "showContentIcon": True,
        "display_tag_title": False,
        "target": "_blank",
    }

    def getPrettyLink(self, obj):
        pl = IPrettyLink(obj)
        for k, v in self.params.items():
            setattr(pl, k, v)
        infos = ""
        if obj.portal_type == "annex":
            pl.showContentIcon = False
            infos += '<p class="discreet"></p>'
            # display description if any
            # description = safe_text(obj.Description() or u'').replace('\n', '<br/>')
            # if description:
            #     infos += u'<p class="discreet">{0}</p>'.format(description)
            # display filename
            infos += '<div class="discreet type-text-widget annex-filename">{0}</div>'.format(obj.file.filename)

        pl.contentValue = self.contentValue(obj)
        return pl.getLink() + infos

    def contentValue(self, item):
        if base_hasattr(item, "get_full_title"):
            return item.get_full_title()
        return None


class ClassificationFolderTitleColumn(PrettyLinkColumn):
    """Prettylink title column for ClassificationFolder"""

    header = _("Classification Folder")
    params = {
        "showIcons": True,
        "display_tag_title": False,
    }

    def renderCell(self, item):
        obj = self._getObject(item)
        if obj.portal_type == "ClassificationSubfolder":
            obj = obj.cf_parent()
        return self.getPrettyLink(obj)


class ClassificationSubfolderTitleColumn(PrettyLinkColumn):
    """Title column for ClassificationFolder"""

    header = _("Classification Subfolder")
    params = {
        "showIcons": True,
        "display_tag_title": False,
    }

    def getPrettyLink(self, obj):
        if obj.portal_type == "ClassificationFolder":
            return "-"
        return super(ClassificationSubfolderTitleColumn, self).getPrettyLink(obj)


class ClassificationFolderIdColumn(BaseColumn):
    header = _("Classification identifier")
    sort_index = "internal_reference_no"

    def renderCell(self, item):
        value = self.getValue(item)
        if not value:
            value = "-"
        value = safe_text(value)
        return value


class ClassificationTreatingGroupColumn(VocabularyColumn):
    header = _("Service in charge")
    attrName = "treating_groups"

    @property
    def _cached_vocab_instance(self):
        if not hasattr(self, "_cached_vocab_instance_value"):
            vocabulary = ServiceInChargeSource(self.context).vocabulary
            self._cached_vocab_instance_value = vocabulary
        return self._cached_vocab_instance_value


class ClassificationTreeIdentifiersColumn(VocabularyColumn):
    header = _("Classification categories")
    attrName = "classification_categories"
    vocabulary = "collective.classification.vocabularies:tree"


class ClassificationFolderArchivedColumn(ColorColumn):
    attrName = "archived"
    i18n_domain = "collective.classification.folder"
    sort_index = -1  # not sortable
    the_object = True
    header = "&nbsp;"
    msgid_prefix = "archived_"

    def getValue(self, item):
        obj = self._getObject(item)
        if obj.portal_type == "ClassificationSubfolder":
            obj = obj.aq_parent
        return obj.archived and "1" or "0"


class ClassificationSubfolderArchivedColumn(ColorColumn):
    attrName = "archived"
    i18n_domain = "collective.classification.folder"
    sort_index = -1  # not sortable
    the_object = True
    header = "&nbsp;"
    msgid_prefix = "archived_"

    def getValue(self, item):
        obj = self._getObject(item)
        if obj.portal_type == "ClassificationFolder":
            return ""
        return obj.archived and "1" or "0"


class ClassificationFoldersColumn(VocabularyColumn):
    header = _("Classification folders")
    attrName = "classification_folders"

    @property
    def _cached_vocab_instance(self):
        if not hasattr(self, "_cached_vocab_instance_value"):
            vocabulary = ClassificationFolderSource(self.context).vocabulary
            self._cached_vocab_instance_value = vocabulary
        return self._cached_vocab_instance_value

    def _render_link(self, value):
        try:
            obj = api.content.get(UID=value)
        except Unauthorized:  # Plone 6: raised instead of returning None
            return
        if not obj:
            return
        title = self._get_title(obj)
        if not title:
            return
        return "<a href='{url}' target='_blank'>{obj}</a>".format(
            url=obj.absolute_url(),
            obj=safe_text(title),
        )

    def _get_title(self, obj):
        """Extract title from object"""
        if hasattr(obj, "get_full_title"):
            title = obj.get_full_title()
        else:
            title = obj.title
        return title

    def _filter_values(self, value):
        if value.startswith("p:"):
            # We don't want to display indexed parents
            return True
        return False

    def renderCell(self, item):
        value = self.getValue(item)
        if not value or value in self.ignored_values:
            return "-"

        # caching when several same values in same column
        if self.use_caching:
            res = self._get_cached_result(value)
            if res:
                return res

        # make sure we have an iterable
        if isinstance(value, str):
            value = [value]
        res = []
        for v in value:
            if self._filter_values(v):
                continue
            try:
                link = self._render_link(v)
                if link:
                    res.append(safe_text(link))
            except Exception:
                # in case an error occured during link creation
                res.append(safe_text(v))
        res = ", ".join(res)
        if not res:
            return "-"
        if self.use_caching:
            self._store_cached_result(value, res)
        return res


class SubfolderClassificationFoldersColumn(ClassificationFoldersColumn):
    header = _("Classification Subfolder")
    sort_index = "classification_folders"

    def _get_title(self, obj):
        """Extract title from object"""
        if obj.portal_type == "ClassificationFolder":
            return
        if aq_parent(obj).UID() == self.context.UID():
            return obj.title
        if hasattr(obj, "get_full_title"):
            title = obj.get_full_title()
        else:
            title = obj.title
        return title


class CombinedReviewstateSizeColumn(BaseColumn):
    """Column showing workflow state (for folders) or filesize (for annexes).

    escape=False because renderCell returns HTML from render_filesize().
    Subclasses overriding renderCell must escape user-supplied content manually.
    """

    header = _("State or Filesize")
    i18n_domain = "plone"
    sort_index = -1  # not sortable
    escape = False

    def __init__(self, context, request, table):
        super(CombinedReviewstateSizeColumn, self).__init__(context, request, table)
        self.wtool = api.portal.get_tool("portal_workflow")

    def renderHeadCell(self):
        """ """
        header = super(CombinedReviewstateSizeColumn, self).renderHeadCell()
        [self._getObject(v) for v in self.table.values]
        total = sum(
            [
                v.aq_parent.categorized_elements.get(k, {}).get("filesize", 0)
                for k, v in self.table._v_cached_objects.items()
                if v.portal_type == "annex"
            ]
        )
        header += "<p>(Total: {0})</p>".format(utils.render_filesize(total))
        return header

    def renderCell(self, item):
        if item.portal_type == "annex":
            obj = self._getObject(item)
            value = obj.aq_parent.categorized_elements.get(item.UID, {}).get("filesize", None)
            if value is None:
                return ""
            return utils.render_filesize(value)
        else:
            state_title = self.wtool.getTitleForStateOnType(item.review_state, item.portal_type)
            return translate(safe_text(state_title), domain=self.i18n_domain, context=self.request)
