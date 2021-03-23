# -*- coding: utf-8 -*-
from plone.dexterity.content import Item
from plone.supermodel import model
from zope import schema
from zope.interface import implementer
from collective.classification.folder import _


class IClassificationSubfolder(model.Schema):
    """ Marker interface and Dexterity Python Schema for ClassificationSubfolder
    """


@implementer(IClassificationSubfolder)
class ClassificationSubfolder(Item):
    """
    """
