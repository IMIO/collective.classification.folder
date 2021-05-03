# -*- coding: utf-8 -*-

from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import TEST_USER_ID
from plone.app.testing import applyProfile
from plone.app.testing import setRoles
from plone.testing import z2

import collective.classification.folder


class CollectiveClassificationFolderLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import plone.app.dexterity

        self.loadZCML(package=plone.app.dexterity)
        import plone.restapi

        import plone.app.contenttypes
        self.loadZCML(package=plone.app.contenttypes)
        import plone.app.event.dx
        self.loadZCML(package=plone.app.event.dx)
        import Products.DateRecurringIndex
        z2.installProduct(app, 'Products.DateRecurringIndex')

        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=collective.classification.folder)
        self.loadZCML(package=collective.classification.tree)

    def tearDownZope(self, app):
        z2.uninstallProduct(app, 'Products.DateRecurringIndex')

    def setUpPloneSite(self, portal):
        applyProfile(portal, "plone.app.contenttypes:default")
        applyProfile(portal, "collective.classification.folder:default")
        setRoles(portal, TEST_USER_ID, ["Manager"])


COLLECTIVE_CLASSIFICATION_FOLDER_FIXTURE = CollectiveClassificationFolderLayer()


COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLECTIVE_CLASSIFICATION_FOLDER_FIXTURE,),
    name="CollectiveClassificationFolderLayer:IntegrationTesting",
)


COLLECTIVE_CLASSIFICATION_FOLDER_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_CLASSIFICATION_FOLDER_FIXTURE,),
    name="CollectiveClassificationFolderLayer:FunctionalTesting",
)


COLLECTIVE_CLASSIFICATION_FOLDER_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        COLLECTIVE_CLASSIFICATION_FOLDER_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name="CollectiveClassificationFolderLayer:AcceptanceTesting",
)
