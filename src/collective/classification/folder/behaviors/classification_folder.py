# -*- coding: utf-8 -*-

from collective.classification.folder import _
from collective.classification.folder.browser.widget import (
    FolderAutocompleteMultiFieldWidget,
)
from collective.classification.folder.content.vocabularies import (
    ClassificationFolderSourceBinder,
)
from collective.classification.tree.behaviors.classification import (
    IClassificationCategory,
)
from plone import schema
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import provider


class IClassificationFolderMarker(Interface):
    pass


@provider(IFormFieldProvider)
class IClassificationFolder(IClassificationCategory):
    """ """

    form.widget(classification_folders=FolderAutocompleteMultiFieldWidget)
    classification_folders = schema.List(
        title=_(u"Classification folders"),
        description=_(u"List of folders / subfolders in which this content is filed"),
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
