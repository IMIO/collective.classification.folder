# -*- coding: utf-8 -*-

from Acquisition import aq_parent
from collective.classification.folder.interfaces import IServiceInCharge
from collective.classification.folder.interfaces import IServiceInCopy
from imio.helpers.content import uuidToCatalogBrain
from plone import api
from z3c.form import util
from z3c.form.i18n import MessageFactory as _zf
from z3c.formwidget.query.interfaces import IQuerySource
from zope.component import getUtility
from zope.component import queryAdapter
from zope.interface import implementer
from zope.interface import Interface
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


@implementer(IQuerySource)
class BaseSourceVocabulary(object):
    def __init__(self, context):
        self.context = context
        self._vocabulary = None
        self._results = None

    def __contains__(self, term):
        return self.vocabulary.__contains__(term)

    def __iter__(self):
        return self.vocabulary.__iter__()

    def __len__(self):
        return self.vocabulary.__len__()

    @property
    def _verified_user(self):
        """Inspired by https://github.com/plone/plone.formwidget.autocomplete/issues/15
        Return the current request user based on cookie credentials"""
        if api.user.is_anonymous():
            portal = api.portal.get()
            app = portal.__parent__
            request = portal.REQUEST
            creds = portal.acl_users.credentials_cookie_auth.extractCredentials(request)
            user = None
            if "login" in creds and creds["login"]:
                # first try the portal (non-admin accounts)
                user = portal.acl_users.authenticate(
                    creds["login"], creds["password"], request
                )
                if not user:
                    # now try the app (i.e. the admin account)
                    user = app.acl_users.authenticate(
                        creds["login"], creds["password"], request
                    )
            return user
        else:
            return api.user.get_current()

    def getTerm(self, value):
        return self.vocabulary.getTerm(value)

    def getTermByToken(self, value):
        return self.vocabulary.getTermByToken(value)

    def search(self, query_string):
        q = query_string.lower()
        results = []
        for term in self.vocabulary:
            if q in term.title.lower():
                results.append(term)
        return results


@implementer(IQuerySource)
class ClassificationFolderSource(BaseSourceVocabulary):
    @property
    def vocabulary(self):
        if self._vocabulary is None:
            current_user = self._verified_user
            if current_user:
                with api.env.adopt_user(user=self._verified_user):
                    terms = [
                        SimpleTerm(value=pair[0], token=pair[0], title=pair[1])
                        for pair in self.results
                    ]
                self._vocabulary = SimpleVocabulary(terms)
            else:
                self._vocabulary = SimpleVocabulary([])
        return self._vocabulary

    @property
    def results(self):
        if self._results is None:
            self._results = self.get_results()
        return self._results

    def get_results(self):
        portal_catalog = api.portal.get_tool("portal_catalog")
        folder_brains = portal_catalog.searchResults(
            object_provides="collective.classification.folder.content.classification_folder.IClassificationFolder",
            sort_on="ClassificationFolderSort",
        )

        def make_tuple(br, folder):
            categories = set([])
            if folder.portal_type == "ClassificationSubfolder":
                parent = aq_parent(folder)
                title = u"{0} / {1}".format(parent.title, folder.title)
                categories.update(parent.classification_categories or [])
            else:
                title = folder.title
            categories.update(folder.classification_categories or [])
            return br.UID, title, categories

        results = []
        uids = []
        for brain in folder_brains:
            results.append(make_tuple(brain, brain.getObject()))
            uids.append(brain.UID)
        # check if all stored values are in the results, so view and edit are possible
        # we assume the concerned field is 'classification_folders'
        for uid in self.context.classification_folders or []:
            if uid in uids:
                continue
            # we found it unrestrictedly
            brain = uuidToCatalogBrain(uid, unrestricted=True)
            if brain:
                results.append(make_tuple(brain, brain._unrestrictedGetObject()))
        return results

    def search(self, query_string, categories_filter=None):
        if categories_filter is None:
            categories_filter = []
        q = query_string.lower()

        terms_matching_query = []
        terms_matching_query_and_category = []
        for (value, title, categories) in self.results:
            if q in title.lower():
                term = self.getTerm(value)
                if categories_filter and categories.intersection(categories_filter):
                    terms_matching_query_and_category.append(term)
                else:
                    terms_matching_query.append(term)

        return terms_matching_query_and_category or terms_matching_query

    def getTerm(self, value):
        try:
            return self.vocabulary.getTerm(value)
        except LookupError:
            # all form widgets are called when using plone.formwidget.masterselect on a form field
            # this is done as anonymous and the vocabulary is then empty
            # it's not necessary here to render the correct term
            # see z3c.form.term
            if '++widget++' in self.context.REQUEST.get('URL', ''):
                return SimpleTerm(value, util.createCSSId(util.toUnicode(value)),
                                  title=_zf(u'Missing: ${value}', mapping=dict(value=util.toUnicode(value))))
            raise


@implementer(IContextSourceBinder)
class ClassificationFolderSourceBinder(object):
    def __call__(self, context):
        return ClassificationFolderSource(context)


class IClassificationFolderGroups(Interface):
    pass


def services_in_charge_vocabulary(context=None):
    adapter = queryAdapter(context, IServiceInCharge)
    if adapter:
        return adapter()
    factory = getUtility(IVocabularyFactory, "plone.app.vocabularies.Groups")
    return factory(context)


def services_in_copy_vocabulary(context=None):
    adapter = queryAdapter(context, IServiceInCopy)
    if adapter:
        return adapter()
    factory = getUtility(IVocabularyFactory, "plone.app.vocabularies.Groups")
    return factory(context)


class ServiceInCopySource(BaseSourceVocabulary):
    @property
    def vocabulary(self):
        if not self._vocabulary:
            with api.env.adopt_user(user=self._verified_user):
                self._vocabulary = services_in_copy_vocabulary(self.context)
        return self._vocabulary


@implementer(IContextSourceBinder)
class ServiceInCopySourceBinder(object):
    def __call__(self, context):
        return ServiceInCopySource(context)


class ServiceInChargeSource(BaseSourceVocabulary):
    @property
    def vocabulary(self):
        if not self._vocabulary:
            with api.env.adopt_user(user=self._verified_user):
                self._vocabulary = services_in_charge_vocabulary(self.context)
        return self._vocabulary


@implementer(IContextSourceBinder)
class ServiceInChargeSourceBinder(object):
    def __call__(self, context):
        return ServiceInChargeSource(context)
