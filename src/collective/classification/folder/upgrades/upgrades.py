from collective.classification.folder.setuphandlers import create_annexes_config
from plone import api
from plone.app.contenttypes.migration.dxmigration import migrate_base_class_to_new_class
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2Base
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
        if profile in upgrade_registry.keys():
            del upgrade_registry[profile]


def to1002(context):
    gs = api.portal.get_tool('portal_setup')
    gs.runAllImportStepsFromProfile('profile-imio.annex:default', dependency_strategy='new')
    gs.runImportStepFromProfile('profile-collective.classification.folder:default', 'catalog', run_dependencies=False)
    gs.runImportStepFromProfile('profile-collective.classification.folder:default', 'typeinfo', run_dependencies=False)
    gs.runImportStepFromProfile('profile-collective.classification.folder:default', 'cssregistry',
                                run_dependencies=False)
    create_annexes_config()
    catalog = api.portal.get_tool('portal_catalog')
    for brain in catalog(portal_type=['ClassificationFolder', 'ClassificationSubfolder']):
        obj = brain.getObject()
        if brain.portal_type == 'ClassificationSubfolder':
            # from plone/app/contenttypes/migration/dxmigration.py, migrate_base_class_to_new_class
            # migrate_base_class_to_new_class breaks object if called a second time
            # was_item test doesn't work the first time
            if obj._tree is None:
                BTreeFolder2Base._initBTrees(obj)
        obj.reindexObject(idxs=['yesno_value', 'is_folderish', 'object_provides'])
