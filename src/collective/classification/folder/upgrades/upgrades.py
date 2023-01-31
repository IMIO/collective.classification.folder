from plone import api


def to1001(context):
    gs = api.portal.get_tool('portal_setup')
    gs.runAllImportStepsFromProfile('profile-collective.classification.folder.upgrades:to1001',
                                    dependency_strategy='new')
    gs.runAllImportStepsFromProfile('profile-collective.z3cform.select2:default',
                                    dependency_strategy='new')
