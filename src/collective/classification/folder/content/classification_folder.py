# -*- coding: utf-8 -*-

from collective.classification.folder.browser.faceted import IClassificationFacetedNavigable
from collective.classification.folder import _
from eea.facetednavigation.events import FacetedEnabledEvent
from eea.facetednavigation.events import FacetedWillBeEnabledEvent
from eea.facetednavigation.layout.interfaces import IFacetedLayout
from eea.facetednavigation.settings.interfaces import IDisableSmartFacets
from eea.facetednavigation.settings.interfaces import IHidePloneLeftColumn
from eea.facetednavigation.settings.interfaces import IHidePloneRightColumn
from plone.dexterity.content import Container
from plone.supermodel import model
from zope import schema
from zope.event import notify
from zope.interface import implementer
from zope.interface import alsoProvides


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


def on_create(obj, event):
    notify(FacetedWillBeEnabledEvent(obj))
    alsoProvides(obj, IClassificationFacetedNavigable)
    if not IDisableSmartFacets.providedBy(obj):
        alsoProvides(obj, IDisableSmartFacets)
    if not IHidePloneLeftColumn.providedBy(obj):
        alsoProvides(obj, IHidePloneLeftColumn)
    if not IHidePloneRightColumn.providedBy(obj):
        alsoProvides(obj, IHidePloneRightColumn)
    notify(FacetedEnabledEvent(obj))

    IFacetedLayout(obj).update_layout("folder-listing-view")
