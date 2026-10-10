# -*- coding: utf-8 -*-

from Acquisition import aq_parent
from collective.classification.folder.content.classification_folder import IClassificationFolder
from collective.classification.folder.content.classification_subfolder import IClassificationSubfolder
from imio.helpers import EMPTY_STRING
from plone.app.dexterity.textindexer.interfaces import IDynamicTextIndexExtender
from plone.base.utils import base_hasattr
from plone.indexer.decorator import indexer
from zope.component import adapter
from zope.interface import implementer


@indexer(IClassificationFolder)
def archived_classification_folder_index(obj):
    """Indexer for the archived field of a classification folder using yesno_value index."""
    return obj.archived and "1" or "0"


@indexer(IClassificationFolder)
def classification_categories_index(obj):
    """Indexer of"""
    if base_hasattr(obj, "classification_categories") and obj.classification_categories:
        return obj.classification_categories
    return [EMPTY_STRING]


@indexer(IClassificationFolder)
def classification_folder_sort(folder):
    elements = []
    if folder.portal_type == "ClassificationSubfolder":
        elements.append(aq_parent(folder).title)
    elements.append(folder.title)
    return "|".join(elements)


@implementer(IDynamicTextIndexExtender)
@adapter(IClassificationSubfolder)
class ClassificationSubfolderSearchableText(object):
    def __init__(self, context):
        self.context = context

    def __call__(self):
        parent = aq_parent(self.context)
        if parent:
            return parent.Title()
        return ""
