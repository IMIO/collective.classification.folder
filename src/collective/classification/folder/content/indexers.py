# -*- coding: utf-8 -*-

from Acquisition._Acquisition import aq_parent  # noqa
from collective.classification.folder.content.classification_folder import IClassificationFolder
from collective.classification.folder.content.classification_subfolder import IClassificationSubfolder
from collective.dexteritytextindexer.interfaces import IDynamicTextIndexExtender
from plone.indexer.decorator import indexer
from zope.component import adapter
from zope.interface import implementer


@indexer(IClassificationFolder)
def archived_classification_folder_index(obj):
    """Indexer for the archived field of a classification folder using yesno_value index. """
    return obj.archived and '1' or '0'


@indexer(IClassificationFolder)
def classification_folder_sort(folder):
    elements = []
    if folder.portal_type == "ClassificationSubfolder":
        elements.append(aq_parent(folder).title)
    elements.append(folder.title)
    return u"|".join(elements)


@implementer(IDynamicTextIndexExtender)
@adapter(IClassificationSubfolder)
class ClassificationSubfolderSearchableText(object):
    def __init__(self, context):
        self.context = context

    def __call__(self):
        parent = aq_parent(self.context)
        if parent:
            return parent.Title()
        return u""
