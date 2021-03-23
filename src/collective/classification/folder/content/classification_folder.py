# -*- coding: utf-8 -*-
from plone.dexterity.content import Container
from plone.supermodel import model
from zope import schema
from zope.interface import implementer
from collective.classification.folder import _


class IClassificationFolder(model.Schema):
    """ Marker interface and Dexterity Python Schema for ClassificationFolder
    """


@implementer(IClassificationFolder)
class ClassificationFolder(Container):
    """
    """
