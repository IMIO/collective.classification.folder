# -*- coding: utf-8 -*-
from collective.classification.folder import _
from collective.classification.folder.interfaces import IServiceInCharge
from collective.classification.folder.interfaces import IServiceInCopy
from persistent.dict import PersistentDict
from plone import api
from unidecode import unidecode
from z3c.form import util
from z3c.form.i18n import MessageFactory as _zf
from z3c.formwidget.query.interfaces import IQuerySource
from zope.annotation import IAnnotations
from zope.component import getUtility
from zope.component import queryAdapter
from zope.interface import implementer
from zope.interface import Interface
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

import logging


logger = logging.getLogger('folder.content.vocabularies')


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


def full_title_categories(folder, tree_voc=None, with_irn=True, with_cat=True):
    """Get full title and full categories"""
    categories = set([])
    cf_parent = folder.cf_parent()
    if cf_parent:
        title = u"{0} ⏩ {1}".format(cf_parent.title, folder.title)
        categories.update(with_cat and cf_parent.classification_categories or [])
    else:
        title = u"{0}".format(folder.title)
    if with_irn and folder.internal_reference_no:
        title = u'{} ({})'.format(title, folder.internal_reference_no)
    categories.update(with_cat and folder.classification_categories or [])
    if with_cat and categories and not tree_voc:
        tree_voc = getUtility(IVocabularyFactory, "collective.classification.vocabularies:tree",)(None)
    try:
        categories = {uid: tree_voc.getTerm(uid) for uid in categories}
    except (LookupError, KeyError) as em:
        logger.error("category no more found ! Folder is '{}', error: '{}'".format(folder.absolute_url(), em))
        categories = {}
    return title, categories


def set_folders_tree(portal):
    """Dict containing uid: (title, categories)"""
    dic = PersistentDict()
    annot = IAnnotations(portal)
    key = u'classification.folder.dic'
    crits = {'object_provides': 'collective.classification.folder.content.classification_folder.'
                                'IClassificationFolder',
             'sort_on': 'ClassificationFolderSort'}
    tree_voc = getUtility(IVocabularyFactory, "collective.classification.vocabularies:fulltree", )(portal)
    for brain in portal.portal_catalog.unrestrictedSearchResults(**crits):
        folder = brain._unrestrictedGetObject()
        dic[brain.UID] = full_title_categories(folder, tree_voc)
    annot[key] = dic


def get_folders_tree():
    """Dict containing uid: (title, categories)"""
    portal = api.portal.get()
    annot = IAnnotations(portal)
    key = u'classification.folder.dic'
    if key not in annot:
        set_folders_tree(portal)
    return annot[key]


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
        all_folders = get_folders_tree()
        results = []
        uids = []
        for brain in folder_brains:
            uids.append(brain.UID)
            infos = all_folders[brain.UID]
            results.append((brain.UID, infos[0], infos[1]))  # title, categories
        # check if all stored values are in the results, so view and edit are possible
        # we assume the concerned field is 'classification_folders'
        for uid in getattr(self.context, 'classification_folders', None) or []:
            if uid in uids:
                continue
            infos = all_folders[uid]
            results.append((uid, infos[0], infos[1]))
        return results

    def search(self, query_string, categories_filter=None):
        if categories_filter is None:
            categories_filter = []
        query_parts = unidecode(query_string).lower().split()

        terms_matching_query = []
        terms_matching_query_and_category = []
        for (value, title, categories) in self.results:
            search_in = '{} {}'.format(unidecode(title).lower(),
                                       ' '.join([unidecode(term.title).lower() for term in categories.values()]))
            if all([part in search_in for part in query_parts]):
                term = self.getTerm(value)
                if categories_filter and categories and set(categories.keys()).intersection(categories_filter):
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
            if self._verified_user:
                with api.env.adopt_user(user=self._verified_user):
                    self._vocabulary = services_in_copy_vocabulary(self.context)
            else:
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
            if self._verified_user:
                with api.env.adopt_user(user=self._verified_user):
                    self._vocabulary = services_in_charge_vocabulary(self.context)
            else:
                self._vocabulary = services_in_charge_vocabulary(self.context)
        return self._vocabulary


@implementer(IContextSourceBinder)
class ServiceInChargeSourceBinder(object):
    def __call__(self, context):
        return ServiceInChargeSource(context)


@implementer(IVocabularyFactory)
class ClassificationFolderPortalTypesVocabulary(object):
    """ Classification folders portal types vocabulary """

    def __call__(self, context):
        terms = []
        for typ, title in ((u'ClassificationFolder', u'Classification Folder'),
                           (u'ClassificationSubfolder', u'Classification Subfolder')):
            terms.append(SimpleVocabulary.createTerm(typ, typ, _(title)))
        return SimpleVocabulary(terms)
