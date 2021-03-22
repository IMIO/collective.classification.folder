# -*- coding: utf-8 -*-
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import (
    applyProfile,
    FunctionalTesting,
    IntegrationTesting,
    PLONE_FIXTURE,
    PloneSandboxLayer,
)
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

        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=collective.classification.folder)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "collective.classification.folder:default")


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
