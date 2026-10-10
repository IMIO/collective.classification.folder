# -*- coding: utf-8 -*-

from plone import api
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.globalrequest import setLocal
from Zope2.Startup.datatypes import default_zpublisher_encoding

import collective.classification.folder


try:  # Plone 5.2+
    from plone.testing.zope import installProduct
    from plone.testing.zope import uninstallProduct
    from plone.testing.zope import WSGI_SERVER_FIXTURE as SERVER_FIXTURE
except ImportError:  # Plone 4.3
    from plone.testing.z2 import installProduct
    from plone.testing.z2 import uninstallProduct
    from plone.testing.z2 import ZSERVER_FIXTURE as SERVER_FIXTURE


PLONE_VERSION = api.env.plone_version()[:3]
# users of the fixture: a site manager and a plain member (no user folder)
MANAGER_ID = "manager"
MEMBER_ID = "member"
PASSWORD = "Password-123"


def new_request(request, form=None):
    """Reuse the test request as a new browser request: GET, or POST of the form values.
    Plone 4 copies the submitted values in request.other, read first by request.get"""
    for key in [k for k in request.other if k.startswith("form.")]:
        del request.other[key]
    request["REQUEST_METHOD"] = form and "POST" or "GET"
    request.form = form or {}
    request.response.setStatus(200)


class CollectiveClassificationFolderLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # as the instance (zope.conf): Zope 2 encodes the pages in iso-8859-15 by default ("⏩" shown as "?")
        default_zpublisher_encoding("utf-8")
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

        import Products.DateRecurringIndex  # noqa
        installProduct(app, "Products.DateRecurringIndex")

        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=collective.classification.folder, name="testing.zcml")
        self.loadZCML(package=collective.classification.tree)

    def tearDownZope(self, app):
        uninstallProduct(app, "Products.DateRecurringIndex")

    def setUpPloneSite(self, portal):
        setLocal('request', portal.REQUEST)  # set request for fingerpointing
        applyProfile(portal, "plone.app.contenttypes:default")
        applyProfile(portal, "collective.classification.folder:testing")
        setRoles(portal, TEST_USER_ID, ["Manager"])
        api.user.create(email="manager@example.com", username=MANAGER_ID, password=PASSWORD, roles=["Manager"])
        api.user.create(email="member@example.com", username=MEMBER_ID, password=PASSWORD)


COLLECTIVE_CLASSIFICATION_FOLDER_FIXTURE = CollectiveClassificationFolderLayer()


COLLECTIVE_CLASSIFICATION_FOLDER_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLECTIVE_CLASSIFICATION_FOLDER_FIXTURE,),
    name="CollectiveClassificationFolderLayer:IntegrationTesting",
)


COLLECTIVE_CLASSIFICATION_FOLDER_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_CLASSIFICATION_FOLDER_FIXTURE,),
    name="CollectiveClassificationFolderLayer:FunctionalTesting",
)


ACCEPTANCE = FunctionalTesting(
    bases=(
        COLLECTIVE_CLASSIFICATION_FOLDER_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        SERVER_FIXTURE,
    ),
    name="CollectiveClassificationFolderLayer:AcceptanceTesting",
)
COLLECTIVE_CLASSIFICATION_FOLDER_ACCEPTANCE_TESTING = ACCEPTANCE  # former name
