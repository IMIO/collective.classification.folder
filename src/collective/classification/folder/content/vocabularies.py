# -*- coding: utf-8 -*-

from z3c.formwidget.query.interfaces import IQuerySource
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
        return []  # TODO

    def getTerm(self, value):
        return self.vocabulary.getTerm(value)

    def getTermByToken(self, value):
        return self.vocabulary.getTermByToken(value)

    def search(self, query_string):
        q = query_string.lower()
        return [self.getTerm(value) for (value, title) in self.results if q in title.lower()]


@implementer(IContextSourceBinder)
class ClassificationFolderSourceBinder(object):

    def __call__(self, context):
        return ClassificationFolderSource(context)
