# -*- coding: utf-8 -*-

from .classification_folder import IClassificationFolder
from plone.dexterity.content import Item
from zope.interface import implementer


class IClassificationSubfolder(IClassificationFolder):
    """ Marker interface and Dexterity Python Schema for ClassificationSubfolder
    """


@implementer(IClassificationSubfolder)
class ClassificationSubfolder(Item):
    """
    """
