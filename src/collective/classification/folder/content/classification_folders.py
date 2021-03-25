# -*- coding: utf-8 -*-
from plone.dexterity.content import Container
from plone.supermodel import model
from zope import schema
from zope.interface import implementer
from collective.classification.folder import _


class IClassificationFolders(model.Schema):
    """ Marker interface and Dexterity Python Schema for ClassificationFolders
    """

    title = schema.TextLine(
        title=_(u"Title"),
        description=_(u"Name of the folders container"),
    )


@implementer(IClassificationFolders)
class ClassificationFolders(Container):
    """
    """
