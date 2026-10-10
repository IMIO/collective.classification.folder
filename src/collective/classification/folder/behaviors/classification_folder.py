# -*- coding: utf-8 -*-

from Acquisition import aq_base
from Acquisition import aq_parent
from collective.classification.folder import _
from collective.classification.folder.browser.widget import FolderAjaxSelectFieldWidget
from collective.classification.folder.browser.widget import SourceAjaxSelectFieldWidget
from collective.classification.folder.content.vocabularies import ClassificationFolderSourceBinder
from collective.classification.tree.behaviors.classification import IClassificationCategory
from collective.classification.tree.behaviors.classification import IClassificationCategoryMarker
from imio.helpers import EMPTY_STRING
from imio.helpers.content import uuidToObject
from plone import schema
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.base.utils import base_hasattr
from plone.indexer.decorator import indexer
from zope.component import adapter
from zope.interface import implementer
from zope.interface import provider


class IClassificationFolderMarker(IClassificationCategoryMarker):
    pass


@provider(IFormFieldProvider)
class IClassificationFolder(IClassificationCategory):
    """ """

    form.widget(classification_categories=SourceAjaxSelectFieldWidget)
    form.widget(classification_folders=FolderAjaxSelectFieldWidget)
    classification_folders = schema.List(
        title=_("Classification folders"),
        description=_("List of folders / subfolders in which this content is filed"),
        value_type=schema.Choice(
            source=ClassificationFolderSourceBinder(),
        ),
        required=False,
    )


@implementer(IClassificationFolder)
@adapter(IClassificationFolderMarker)
class ClassificationFolder(object):
    def __init__(self, context):
        self.context = context

    @property
    def classification_folders(self):
        if hasattr(self.context, "classification_folders"):
            return self.context.classification_folders
        return None

    @classification_folders.setter
    def classification_folders(self, value):
        self.context.classification_folders = value

    @property
    def classification_categories(self):
        if hasattr(self.context, "classification_categories"):
            return self.context.classification_categories
        return None

    @classification_categories.setter
    def classification_categories(self, value):
        self.context.classification_categories = value


@indexer(IClassificationFolderMarker)
def classification_folders_indexer(obj):
    """Custom indexer to ensure that folder are also indexed for subfolder"""
    if not base_hasattr(obj, "classification_folders") or not obj.classification_folders:
        return [EMPTY_STRING]
    values = []
    obj = aq_base(obj)
    for uid in obj.classification_folders:
        values.append(uid)
        related_obj = uuidToObject(uid, unrestricted=True)
        if related_obj.portal_type == "ClassificationSubfolder":
            values.append("p:{0}".format(aq_parent(related_obj).UID()))
    return values
