# -*- coding: utf-8 -*-

from Acquisition import aq_parent
from collective.classification.folder import utils
from collective.classification.folder.content.classification_folder import (
    IClassificationFolder,
)
from plone.dexterity.content import Item
from zope.interface import implementer
from zope.schema.fieldproperty import FieldProperty


class IClassificationSubfolder(IClassificationFolder):
    """Marker interface and Dexterity Python Schema for ClassificationSubfolder"""


@implementer(IClassificationSubfolder)
class ClassificationSubfolder(Item):
    """ """

    __ac_local_roles_block__ = True
    treating_groups = FieldProperty(IClassificationFolder[u"treating_groups"])
    recipient_groups = FieldProperty(IClassificationFolder[u"recipient_groups"])

    def cf_parent(self):
        """Returns ClassificationFolder"""
        return aq_parent(self)

    def get_full_title(self):
        return u"{0} ⏩ {1}".format(self.cf_parent().Title().decode("utf8"), self.Title().decode("utf8"))

    def _increment_internal_reference(self):
        utils.increment_internal_reference("subfolder_number")


def on_move(obj, event):
    """Reindexes SearchableText and ClassificationFolderSort."""
    obj.reindexObject(idxs=["ClassificationFolderSort", "SearchableText"])
