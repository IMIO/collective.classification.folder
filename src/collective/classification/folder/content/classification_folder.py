# -*- coding: utf-8 -*-

from collective.classification.folder import _
from collective.classification.folder.browser.faceted import IClassificationFacetedNavigable
from collective.classification.tree.vocabularies import ClassificationTreeSourceBinder
from eea.facetednavigation.events import FacetedEnabledEvent
from eea.facetednavigation.events import FacetedWillBeEnabledEvent
from eea.facetednavigation.layout.interfaces import IFacetedLayout
from eea.facetednavigation.settings.interfaces import IDisableSmartFacets
from eea.facetednavigation.settings.interfaces import IHidePloneLeftColumn
from eea.facetednavigation.settings.interfaces import IHidePloneRightColumn
from plone.autoform import directives as form
from plone.dexterity.content import Container
from plone.formwidget.autocomplete import AutocompleteMultiFieldWidget
from plone.supermodel import model
from zope import schema
from zope.event import notify
from zope.interface import alsoProvides
from zope.interface import implementer


class IClassificationFolder(model.Schema):
    """ Marker interface and Dexterity Python Schema for ClassificationFolder
    """

    title = schema.TextLine(
        title=_(u"Name"),
        description=_(u"Name of the folder"),
    )

    classification_identifier = schema.TextLine(
        title=_(u"Classification identifier"),
        description=_(u"Unique identifier of the folder"),
        required=False,
    )

    form.widget(classification_categories=AutocompleteMultiFieldWidget)
    classification_categories = schema.List(
        title=_(u"Classification categories"),
        description=_(u"List of categories / subcategories"),
        value_type=schema.Choice(
            source=ClassificationTreeSourceBinder(),
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
