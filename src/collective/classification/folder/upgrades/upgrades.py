from plone import api
from Products.GenericSetup.interfaces import IUpgradeSteps
from Products.GenericSetup.registry import GlobalRegistryStorage


def to1001(context):
    gs = api.portal.get_tool('portal_setup')
    gs.runAllImportStepsFromProfile('profile-collective.classification.folder.upgrades:to1001',
                                    dependency_strategy='new')
    gs.runAllImportStepsFromProfile('profile-collective.z3cform.select2:default',
                                    dependency_strategy='new')
    upgrade_registry = GlobalRegistryStorage(IUpgradeSteps)
    for profile in (u'collective.js.chosen:default', u'collective.z3cform.chosen:default'):
        if profile in upgrade_registry.keys():
            del upgrade_registry[profile]
