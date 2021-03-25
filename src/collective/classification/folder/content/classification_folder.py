# -*- coding: utf-8 -*-

from plone.dexterity.content import Container
from plone.supermodel import model
from zope import schema
from zope.interface import implementer
from collective.classification.folder import _


class IClassificationFolder(model.Schema):
    """ Marker interface and Dexterity Python Schema for ClassificationFolder
    """

    title = schema.TextLine(
        title=_(u"Title"),
        description=_(u"Name of the folders container"),
    )

    classification_identifier = schema.TextLine(
        title=_(u"Classification identifier"),
        description=_(u"Unique identifier of the folder"),
        required=False,
    )

    classification_categories = schema.List(
        title=_(u"Classification categories"),
        description=_(u"List of categories / subcategories"),
        value_type=schema.Choice(
            values=[]  # TODO: get source from collective.classification.tree
        ),
    )

    service_in_charge = schema.Choice(
        title=_(u"Service in charge"),
        description=_(u"ID of the service that are in charge of this folder"),
        vocabulary="plone.app.vocabularies.Groups",
        required=False,
    )

    services_in_copy = schema.List(
        title=_(u"Services in copy"),
        description=_(u"ID of the services that can access this folder"),
        value_type=schema.Choice(
            vocabulary="plone.app.vocabularies.Groups"
        ),
        required=False,
    )

    classification_informations = schema.TextLine(
        title=_(u"Classification informations"),
        description=_(u"Informations"),
        required=False,
    )


@implementer(IClassificationFolder)
class ClassificationFolder(Container):
    """
    """
