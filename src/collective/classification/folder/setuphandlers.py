# -*- coding: utf-8 -*-
from Products.CMFPlone.interfaces import INonInstallable
from collective.classification.folder import _
from plone import api
from zope.interface import implementer


def create_classification_folder_facet():
    portal = api.portal.get()
    folder_id = "classification_folder_faceted_configuration"
    if folder_id in portal:
        return
    folder = api.content.create(
        container=portal,
        id=folder_id,
        title=_(u"Classification folder faceted configuration"),
        type="Folder",
    )
    folder.exclude_from_nav = True

    # backup location to avoid redirection after enabling the facets
    response_status = folder.REQUEST.RESPONSE.getStatus()
    response_location = folder.REQUEST.RESPONSE.getHeader("location")

    faceted_subtyper = folder.unrestrictedTraverse("@@faceted_subtyper")
    faceted_subtyper.enable()
    faceted_exportimport = folder.unrestrictedTraverse("@@faceted_exportimport")
    xml = folder.unrestrictedTraverse("classification-folder-faceted.xml")()
    faceted_exportimport._import_xml(import_file=xml)

    folder.REQUEST.RESPONSE.status = response_status
    folder.REQUEST.RESPONSE.setHeader("location", response_location or "")


@implementer(INonInstallable)
class HiddenProfiles(object):
    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return ["collective.classification.folder:uninstall"]


def post_install(context):
    """Post install script"""
    # Do something at the end of the installation of this package.

    create_classification_folder_facet()


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.
