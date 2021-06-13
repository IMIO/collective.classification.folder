# -*- coding: utf-8 -*-

from AccessControl import getSecurityManager
from Acquisition import aq_parent
from collective.classification.folder.interfaces import IServiceInCharge
from collective.classification.folder.interfaces import IServiceInCopy
from operator import itemgetter
from plone import api
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
            with api.env.adopt_user(user=self._verified_user):
                terms = [
                    SimpleTerm(value=pair[0], token=pair[0], title=pair[1])
                    for pair in self.results
                ]
                self._vocabulary = SimpleVocabulary(terms)
        return self._vocabulary

    @property
    def results(self):
        if self._results is None:
            self._results = self.get_results()
        return self._results

    def get_results(self):
        all_reading_folder_groups = ClassificationFolderGroups().reader_groups

        if getSecurityManager().checkPermission("Manage Portal", self.context):
            accessible_folder_uids = [
                folder_uid
                for (folder_uid, folder_groups) in all_reading_folder_groups.items()
            ]
        else:
            user = api.user.get_current()
            # `if group` is necessary because get_groups can return None values
            user_groups = set(
                [group.id for group in api.group.get_groups(user=user) if group]
            )
            accessible_folder_uids = [
                folder_uid
                for (folder_uid, folder_groups) in all_reading_folder_groups.items()
                if user_groups.intersection(folder_groups)
            ]

        results = []
        for folder_uid in accessible_folder_uids:
            brains = api.content.find(UID=folder_uid)
            if brains:
                categories = set([])
                folder = brains[0].getObject()
                if folder.portal_type == "ClassificationSubfolder":
                    parent = aq_parent(folder)
                    title = u"{0} / {1}".format(parent.title, folder.title)
                    categories.update(parent.classification_categories or [])
                else:
                    title = folder.title
                categories.update(folder.classification_categories or [])
                results.append((folder_uid, title, categories))

        return sorted(results, key=itemgetter(1))

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


@implementer(IContextSourceBinder)
class ClassificationFolderSourceBinder(object):
    def __call__(self, context):
        return ClassificationFolderSource(context)


class IClassificationFolderGroups(Interface):
    pass


@implementer(IClassificationFolderGroups)
class ClassificationFolderGroups(object):
    def __init__(self):
        self.reader_groups = {}
        self.editor_groups = {}
        self.enumerate_groups()

    def enumerate_groups(self):
        portal_catalog = api.portal.get_tool("portal_catalog")
        folder_brains = portal_catalog.searchResults(
            object_provides="collective.classification.folder.content.classification_folder.IClassificationFolder",
            sort_on="getObjPositionInParent",
        )
        for folder_brain in folder_brains:
            folder_obj = folder_brain.getObject()
            reader_groups = folder_obj.services_in_copy or []
            editor_groups = (
                [folder_obj.service_in_charge] if folder_obj.service_in_charge else []
            )
            if folder_obj.portal_type == "ClassificationSubfolder":
                parent_obj = aq_parent(folder_obj)
                parent_reader_groups = parent_obj.services_in_copy or []
                reader_groups = list(set(reader_groups).union(parent_reader_groups))
                parent_editor_groups = (
                    [parent_obj.service_in_charge]
                    if parent_obj.service_in_charge
                    else []
                )
                editor_groups = list(set(editor_groups).union(parent_editor_groups))
            self.reader_groups[folder_brain.UID] = reader_groups
            self.editor_groups[folder_brain.UID] = editor_groups


def services_in_charge_vocabulary(context=None):
    adapter = queryAdapter(context, IServiceInCharge)
    if adapter:
        return adapter()
    factory = getUtility(IVocabularyFactory, "plone.app.vocabularies.Groups")
    return factory


def services_in_copy_vocabulary(context=None):
    adapter = queryAdapter(context, IServiceInCopy)
    if adapter:
        return adapter()
    factory = getUtility(IVocabularyFactory, "plone.app.vocabularies.Groups")
    return factory


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
