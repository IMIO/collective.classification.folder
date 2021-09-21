# -*- coding: utf-8 -*-

from Acquisition._Acquisition import aq_parent
from collective.classification.folder.content.classification_folder import (
    IClassificationFolder,
)
from collective.classification.folder.content.classification_subfolder import (
    IClassificationSubfolder,
)
from collective.dexteritytextindexer import IDynamicTextIndexExtender
from plone.indexer.decorator import indexer
from zope.component import adapter
from zope.interface import implementer


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
