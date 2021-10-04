# -*- coding: utf-8 -*-

from eea.faceted.vocabularies.autocomplete import IAutocompleteSuggest
from zope.interface import implementer
from Products.Five import BrowserView
from plone import api
from collective.classification.tree.vocabularies import ClassificationTreeSource

import json


def parse_query(text):
    """Copied from plone.app.vocabularies.catalog.parse_query but cleaned."""
    for char in "?-+*()":
        text = text.replace(char, " ")
    query = {"SearchableText": " AND ".join(x + "*" for x in text.split())}
    return query


@implementer(IAutocompleteSuggest)
class BaseSuggestView(BrowserView):
    def _return_result(self, result):
        self.request.response.setHeader("Content-type", "application/json")
        return json.dumps(result)


class ClassificationCategorySuggest(BaseSuggestView):
    label = u"Classification Category"

    def __call__(self):
        result = []
        query = self.request.get("term").decode("utf8").lower()
        if not query:
            return self._return_result(result)
        vocabulary = ClassificationTreeSource(self.context).vocabulary
        result = [
            {"id": e.value, "text": e.title}
            for e in vocabulary
            if query in e.title.lower()
        ]
        return self._return_result(result)


class FolderSuggest(BaseSuggestView):
    label = u"Classification Folder"

    def __call__(self):
        query = self.request.get("term")
        if not query:
            return self._return_result([])

        query = parse_query(query)
        query.update(
            {
                "portal_type": ("ClassificationFolder", "ClassificationSubfolder"),
                "sort_on": "sortable_title",
            }
        )
        brains = api.content.find(**query)
        result = [
            {"id": b.UID, "text": b.get_full_title and b.get_full_title or b.Title}
            for b in brains
        ]
        return self._return_result(result)
