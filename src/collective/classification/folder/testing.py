# -*- coding: utf-8 -*-

from plone import api
from plone.app.robotframework.content import Content
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.robotframework.utils import disableCSRFProtection
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.testing.zope import WSGI_SERVER_FIXTURE
from zope.globalrequest import setLocal

import collective.classification.folder
import transaction


# users of the fixture: a site manager and a plain member (no user folder)
MANAGER_ID = "manager"
MEMBER_ID = "member"
PASSWORD = "Password-123"


def new_request(request, form=None):
    """Reuse the test request as a new browser request: GET, or POST of the form values."""
    for key in [k for k in request.other if k.startswith("form.")]:
        del request.other[key]
    request["REQUEST_METHOD"] = form and "POST" or "GET"
    request.form = form or {}
    request.response.setStatus(200)


class CollectiveClassificationFolderLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import plone.app.dexterity

        self.loadZCML(package=plone.app.dexterity)
        import plone.app.contenttypes
        import plone.restapi

        self.loadZCML(package=plone.app.contenttypes)
        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=collective.classification.folder, name="testing.zcml")
        self.loadZCML(package=collective.classification.tree)

    def setUpPloneSite(self, portal):
        setLocal("request", portal.REQUEST)  # set request for fingerpointing
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


def set_field_value(library, *args):
    """plone.app.robotframework 3.0 Set field value doesn't disable the CSRF protection: its change is aborted"""
    disableCSRFProtection()
    return Content._set_field_value(library, *args)


class AcceptanceTesting(FunctionalTesting):
    def setUp(self):
        super().setUp()
        Content._set_field_value, Content.set_field_value = Content.set_field_value, set_field_value

    def tearDown(self):
        Content.set_field_value = Content._set_field_value
        super().tearDown()

    def testSetUp(self):
        super().testSetUp()
        # "Enable autologin as  Manager" logs in as "Manager": a real user, or the sources using
        # api.env.adopt_user (collective.classification.tree) fail (MemberData has no "allowed")
        api.user.create(email="robot@example.com", username="Manager", password=PASSWORD, roles=["Manager"])
        transaction.commit()


ACCEPTANCE = AcceptanceTesting(
    bases=(
        COLLECTIVE_CLASSIFICATION_FOLDER_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        WSGI_SERVER_FIXTURE,
    ),
    name="CollectiveClassificationFolderLayer:AcceptanceTesting",
)
COLLECTIVE_CLASSIFICATION_FOLDER_ACCEPTANCE_TESTING = ACCEPTANCE  # former name
