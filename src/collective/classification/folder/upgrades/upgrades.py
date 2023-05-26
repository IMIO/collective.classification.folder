from collective.classification.folder import PLONE_VERSION
from plone import api
from Products.GenericSetup.interfaces import IUpgradeSteps
from Products.GenericSetup.registry import GlobalRegistryStorage


def to1001(context):
    if PLONE_VERSION >= '5.1':
        from Products.CMFPlone.utils import get_installer  # noqa
        installer = get_installer(context, context.REQUEST)
        ipi = installer.is_product_installed
        uni = installer.uninstall_product
    else:
        installer = api.portal.get_tool('portal_quickinstaller')  # noqa
        ipi = installer.isProductInstalled
        uni = installer.uninstallProducts
    for prd in ('collective.z3cform.chosen', 'collective.js.chosen'):
        if ipi(prd):
            uni(PLONE_VERSION >= '5.1' and prd or [prd])
    gs = api.portal.get_tool('portal_setup')
    gs.runAllImportStepsFromProfile('profile-collective.classification.folder.upgrades:to1001',
                                    dependency_strategy='new')
    gs.runAllImportStepsFromProfile('profile-collective.z3cform.select2:default',
                                    dependency_strategy='new')
    upgrade_registry = GlobalRegistryStorage(IUpgradeSteps)
    for profile in (u'collective.js.chosen:default', u'collective.z3cform.chosen:default'):
        if profile in list(upgrade_registry.keys()):
            del upgrade_registry[profile]
