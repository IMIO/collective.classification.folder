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

    service_in_charge = FieldProperty(IClassificationFolder[u"service_in_charge"])
    services_in_copy = FieldProperty(IClassificationFolder[u"services_in_copy"])

    def get_full_title(self):
        parent = aq_parent(self)
        if parent:
            return u"{0} / {1}".format(
                parent.Title().decode("utf8"), self.Title().decode("utf8")
            )
        return self.Title()

    def _increment_internal_reference(self):
        utils.increment_internal_reference("subfolder_number")
