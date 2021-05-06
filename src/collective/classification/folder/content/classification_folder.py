# -*- coding: utf-8 -*-

from Products.statusmessages.interfaces import IStatusMessage
from collective import dexteritytextindexer
from collective.classification.folder import _
from collective.classification.folder.browser.faceted import IClassificationFacetedNavigable
from collective.classification.tree.vocabularies import ClassificationTreeSourceBinder
from dexterity.localrolesfield.field import LocalRoleField
from dexterity.localrolesfield.field import LocalRolesField
from eea.facetednavigation.events import FacetedEnabledEvent
from eea.facetednavigation.events import FacetedWillBeEnabledEvent
from eea.facetednavigation.layout.interfaces import IFacetedLayout
from eea.facetednavigation.settings.interfaces import IDisableSmartFacets
from eea.facetednavigation.settings.interfaces import IHidePloneLeftColumn
from eea.facetednavigation.settings.interfaces import IHidePloneRightColumn
from plone import api
from plone.autoform import directives as form
from plone.dexterity.content import Container
from plone.formwidget.autocomplete import AutocompleteMultiFieldWidget
from plone.supermodel import model
from zExceptions import Redirect
from zope import schema
from zope.component import getMultiAdapter
from zope.event import notify
from zope.interface import Invalid
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import invariant
from zope.schema.fieldproperty import FieldProperty


class IClassificationFolder(model.Schema):
    """ Marker interface and Dexterity Python Schema for ClassificationFolder
    """

    dexteritytextindexer.searchable("title")
    title = schema.TextLine(
        title=_(u"Name"),
        description=_(u"Name of the folder"),
    )

    dexteritytextindexer.searchable("classification_identifier")
    classification_identifier = schema.TextLine(
        title=_(u"Classification identifier"),
        description=_(u"Unique identifier of the folder"),
        required=False,
    )

    dexteritytextindexer.searchable("classification_categories")
    form.widget(classification_categories=AutocompleteMultiFieldWidget)
    classification_categories = schema.List(
        title=_(u"Classification categories"),
        description=_(u"List of categories / subcategories"),
        value_type=schema.Choice(
            source=ClassificationTreeSourceBinder(),
        ),
    )

    service_in_charge = LocalRoleField(
        title=_(u"Service in charge"),
        description=_(u"ID of the service that are in charge of this folder"),
        vocabulary="collective.classification.folder.vocabularies.services",
        required=False,
    )

    services_in_copy = LocalRolesField(
        title=_(u"Services in copy"),
        description=_(u"ID of the services that can access this folder"),
        value_type=schema.Choice(vocabulary="collective.classification.folder.vocabularies.services"),
        required=False,
    )

    dexteritytextindexer.searchable("classification_informations")
    classification_informations = schema.TextLine(
        title=_(u"Classification informations"),
        description=_(u"Informations"),
        required=False,
    )

    @invariant
    def unique_identifier_invariant(data):
        try:
            data_uuid = api.content.get_uuid(data)
        except TypeError:
            return

        brains = api.content.find(
            context=api.portal.get(),
            classification_identifier=data.classification_identifier,
        )
        if len(brains) != 0 and brains[0].UID != data_uuid:
            raise Invalid(
                _(u"The classification identifier must be unique to this folder.")
            )


@implementer(IClassificationFolder)
class ClassificationFolder(Container):
    """
    """

    service_in_charge = FieldProperty(IClassificationFolder[u"service_in_charge"])
    services_in_copy = FieldProperty(IClassificationFolder[u"services_in_copy"])


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


def on_delete(obj, event):
    obj_uid = api.content.get_uuid(obj)
    linked_content = api.content.find(classification_folders=obj_uid)
    if linked_content:
        IStatusMessage(obj.REQUEST).addStatusMessage(
            _(
                "cannot_delete_referenced_folder",
                default="This folder cannot be deleted because it is referenced elsewhere",
            ),
            type="warning",
        )
        view_url = getMultiAdapter(
            (obj, obj.REQUEST), name=u"plone_context_state"
        ).view_url()
        raise Redirect(view_url)
