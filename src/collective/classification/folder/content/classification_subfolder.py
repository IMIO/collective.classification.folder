# -*- coding: utf-8 -*-

from .classification_folder import IClassificationFolder
from plone.dexterity.content import Item
from zope.interface import implementer
from zope.schema.fieldproperty import FieldProperty


class IClassificationSubfolder(IClassificationFolder):
    """ Marker interface and Dexterity Python Schema for ClassificationSubfolder
    """


@implementer(IClassificationSubfolder)
class ClassificationSubfolder(Item):
    """
    """

    service_in_charge = FieldProperty(IClassificationFolder[u"service_in_charge"])
    services_in_copy = FieldProperty(IClassificationFolder[u"services_in_copy"])
