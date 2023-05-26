from plone import api
from Products.GenericSetup.interfaces import IUpgradeSteps
from Products.GenericSetup.registry import GlobalRegistryStorage


def to1001(context):
    pqi = api.portal.get_tool("portal_quickinstaller")
    inst_prd = [dic['id'] for dic in pqi.listInstalledProducts() if dic['status'] == 'installed']
    for prd in ('collective.z3cform.chosen', 'collective.js.chosen'):
        if prd in inst_prd:
            pqi.uninstallProducts([prd])
    gs = api.portal.get_tool('portal_setup')
    gs.runAllImportStepsFromProfile('profile-collective.classification.folder.upgrades:to1001',
                                    dependency_strategy='new')
    gs.runAllImportStepsFromProfile('profile-collective.z3cform.select2:default',
                                    dependency_strategy='new')
    upgrade_registry = GlobalRegistryStorage(IUpgradeSteps)
    for profile in (u'collective.js.chosen:default', u'collective.z3cform.chosen:default'):
        if profile in list(upgrade_registry.keys()):
            del upgrade_registry[profile]
