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
        all_reading_folder_groups = ClassificationFolderGroups().reader_groups

        if getSecurityManager().checkPermission("Manage Portal", self.context):
            accessible_folder_uids = [
                folder_uid
                for (folder_uid, folder_groups) in all_reading_folder_groups.items()
            ]
        else:
            user = api.user.get_current()
            # `if group` is necessary because get_groups can return None values
            user_groups = set([group.id for group in api.group.get_groups(user=user) if group])
            accessible_folder_uids = [
                folder_uid
                for (folder_uid, folder_groups) in all_reading_folder_groups.items()
                if user_groups.intersection(folder_groups)
            ]

        results = []
        for folder_uid in accessible_folder_uids:
            brains = api.content.find(UID=folder_uid)
            if brains:
                folder = brains[0].getObject()
                if folder.portal_type == "ClassificationSubfolder":
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
        self.reader_groups = {}
        self.editor_groups = {}
        self.enumerate_groups()

    def enumerate_groups(self):
        dic = {}
        portal_catalog = api.portal.get_tool('portal_catalog')
        folder_brains = portal_catalog.searchResults(
            object_provides="collective.classification.folder.content.classification_folder.IClassificationFolder",
            sort_on="getObjPositionInParent",
        )
        for folder_brain in folder_brains:
            folder_obj = folder_brain.getObject()
            reader_groups = folder_obj.services_in_copy or []
            editor_groups = [folder_obj.service_in_charge] if folder_obj.service_in_charge else []
            if folder_obj.portal_type == "ClassificationSubfolder":
                parent_obj = aq_parent(folder_obj)
                parent_reader_groups = parent_obj.services_in_copy or []
                reader_groups = list(set(reader_groups).union(parent_reader_groups))
                parent_editor_groups = [parent_obj.service_in_charge] if parent_obj.service_in_charge else []
                editor_groups = list(set(editor_groups).union(parent_editor_groups))
            self.reader_groups[folder_brain.UID] = reader_groups
            self.editor_groups[folder_brain.UID] = editor_groups
