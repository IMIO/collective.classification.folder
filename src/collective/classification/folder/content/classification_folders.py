# -*- coding: utf-8 -*-

from collective.classification.folder import _
from eea.facetednavigation.layout.interfaces import IFacetedLayout
from plone.dexterity.content import Container
from plone.supermodel import model
from zope import schema
from zope.interface import implementer


class IClassificationFolders(model.Schema):
    """ Marker interface and Dexterity Python Schema for ClassificationFolders
    """

    title = schema.TextLine(
        title=_(u"Title"),
        # description=_(u"Name of the folders container"),
    )


@implementer(IClassificationFolders)
class ClassificationFolders(Container):
    """
    """


def on_create(obj, event):
    faceted_subtyper = obj.unrestrictedTraverse("@@faceted_subtyper")
    faceted_subtyper.enable()

    faceted_exportimport = obj.unrestrictedTraverse("@@faceted_exportimport")
    xml = obj.unrestrictedTraverse("classification-folders-faceted.xml")()
    faceted_exportimport._import_xml(import_file=xml)

    IFacetedLayout(obj).update_layout("faceted-table-items")
