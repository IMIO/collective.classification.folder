# -*- coding: utf-8 -*-

from Products.CMFPlone.interfaces import INonInstallable
from plone import api
from plone.registry import field
from plone.registry import Record
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.i18n import translate as _
from zope.interface import implementer


def create_classification_folder_facet():
    """Used to configure faceted table on folder and subfolder views"""
    portal = api.portal.get()
    folder_id = "classification_folder_faceted_configuration"
    if folder_id in portal:
        return
    folder = api.content.create(
        container=portal,
        id=folder_id,
        title=_(u"Classification folder faceted configuration",
                domain='collective.classification.folder',
                target_language=portal.portal_properties.site_properties.getProperty('default_language', 'fr'),
                ),
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


def set_registry():
    registry = getUtility(IRegistry)
    settings_iface = (
        "collective.classification.folder.browser.settings.IClassificationConfig.{0}"
    )

    key = settings_iface.format("folder_number")
    if not registry.get(key):
        registry_field = field.Int(title=u"folder_number")
        registry_record = Record(registry_field)
        registry_record.value = 1
        registry.records[key] = registry_record

    key = settings_iface.format("folder_talexpression")
    if not registry.get(key):
        registry_field = field.TextLine(title=u"folder_talexpression")
        registry_record = Record(registry_field)
        registry_record.value = u"python:'F%04d'%int(number)"
        registry.records[key] = registry_record

    key = settings_iface.format("subfolder_number")
    if not registry.get(key):
        registry_field = field.Int(title=u"subfolder_number")
        registry_record = Record(registry_field)
        registry_record.value = 1
        registry.records[key] = registry_record

    key = settings_iface.format("subfolder_talexpression")
    if not registry.get(key):
        registry_field = field.TextLine(title=u"subfolder_talexpression")
        registry_record = Record(registry_field)
        registry_record.value = u"python:'%s-xx'%(context.internal_reference_no)"
        registry.records[key] = registry_record


def create_annexes_config():
    portal = api.portal.get()
    if 'annexes_types' not in portal:
        folder = api.content.create(
            container=portal,
            id='annexes_types',
            title=_(u"Annexes Types",
                    domain='collective.classification.folder',
                    target_language=portal.portal_properties.site_properties.getProperty('default_language', 'fr'),
                    ),
            type="ContentCategoryConfiguration",
        )
        folder.exclude_from_nav = True
        folder.reindexObject()


@implementer(INonInstallable)
class HiddenProfiles(object):
    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return ["collective.classification.folder:uninstall"]


def post_install(context):
    """Post install script"""
    # Do something at the end of the installation of this package.
    create_classification_folder_facet()
    set_registry()


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.
