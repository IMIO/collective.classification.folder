# -*- coding: utf-8 -*-

from AccessControl import getSecurityManager
from Acquisition import aq_parent
from operator import itemgetter
from plone import api
from z3c.formwidget.query.interfaces import IQuerySource
from zope.interface import Interface
from zope.interface import implementer
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


@implementer(IQuerySource)
class ClassificationFolderSource(object):

    def __init__(self, context):
        self.context = context
        self.results = self.get_results()
        terms = [
            SimpleTerm(value=pair[0], token=pair[0], title=pair[1]) for pair in self.results
        ]
        self.vocabulary = SimpleVocabulary(terms)

    def __contains__(self, term):
        return self.vocabulary.__contains__(term)

    def __iter__(self):
        return self.vocabulary.__iter__()

    def __len__(self):
        return self.vocabulary.__len__()

    def get_results(self):
        all_folders = ClassificationFolderGroups()

        if getSecurityManager().checkPermission("Manage Portal", self.context):
            accessible_folder_uids = [
                folder_uid
                for (folder_uid, folder_groups) in all_folders
            ]
        else:
            user = api.user.get_current()
            # `if group` is necessary because get_groups can return None values
            user_groups = set([group.id for group in api.group.get_groups(user=user) if group])
            accessible_folder_uids = [
                folder_uid
                for (folder_uid, folder_groups) in all_folders
                if user_groups.intersection(folder_groups)
            ]

        results = []
        for folder_uid in accessible_folder_uids:
            brains = api.content.find(UID=folder_uid)
            if brains:
                folder = brains[0].getObject()
                if folder.portal_type == "Classification Subfolder":
                    parent = aq_parent(folder)
                    title = u"{0} >> {1}".format(parent.title, folder.title)
                else:
                    title = folder.title
                categories = folder.classification_categories or []
                results.append((folder_uid, title, categories))  # TODO: fix title indexation

        return sorted(results, key=itemgetter(1))

    def getTerm(self, value):
        return self.vocabulary.getTerm(value)

    def getTermByToken(self, value):
        return self.vocabulary.getTermByToken(value)

    def search(self, query_string, categories_filter=None):
        if categories_filter is None:
            categories_filter = []
        q = query_string.lower()

        terms = []
        for (value, title, categories) in self.results:
            if categories_filter and set(categories_filter).isdisjoint(categories):
                continue
            if q in title.lower():
                terms.append(self.getTerm(value))
        return terms


@implementer(IContextSourceBinder)
class ClassificationFolderSourceBinder(object):

    def __call__(self, context):
        return ClassificationFolderSource(context)


class IClassificationFolderGroups(Interface):
    pass


@implementer(IClassificationFolderGroups)
class ClassificationFolderGroups(object):

    def __init__(self):
        self.folder_groups = self.build_folder_groups()

    def build_folder_groups(self):
        dic = {}
        portal_catalog = api.portal.get_tool('portal_catalog')
        folder_brains = portal_catalog.searchResults(
            object_provides="collective.classification.folder.content.classification_folder.IClassificationFolder",
            sort_on="getObjPositionInParent",
        )
        for folder_brain in folder_brains:
            folder_obj = folder_brain.getObject()
            groups = folder_obj.services_in_copy or []
            if folder_obj.portal_type == "Classification Subfolder":
                parent_groups = aq_parent(folder_obj).services_in_copy or []
                groups = list(set(groups).union(parent_groups))
            dic[folder_brain.UID] = groups

        return dic

    def __iter__(self):
        for (folder_uid, folder_groups) in self.folder_groups.items():
            yield (folder_uid, folder_groups)
