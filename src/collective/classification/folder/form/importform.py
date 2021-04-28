# -*- coding: utf-8 -*-

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from collective.classification.folder import _
from collective.classification.folder import utils
from collective.classification.tree.form import importform as baseform
from plone.z3cform.layout import FormWrapper
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

import json


ANNOTATION_KEY = baseform.ANNOTATION_KEY


class ImportFormFirstStep(baseform.ImportFormFirstStep):
    pass


class ImportFirstStepView(FormWrapper):
    form = ImportFormFirstStep


class ImportFormSecondStep(baseform.ImportFormSecondStep):
    _vocabulary = u"collective.classification.vocabularies:folders_import_keys"

    @property
    def label(self):
        return _(u"Import folders")

    def update(self):
        self.data = []
        self.vocabulary = getUtility(
            IVocabularyFactory,
            "collective.classification.vocabularies:tree_id_mapping",
        )(self.context)
        super(ImportFormSecondStep, self).update()

    def _process_data(self, data, key=None):
        """Return a list of dict containing object keys and a special key
        `_children` for hierarchy"""
        if key not in data:
            return []
        return [
            {
                "classification_identifier": k,
                "title": v[0],
                "data": v[1],
                "_children": self._process_data(data, key=k),
            }
            for k, v in data[key].items()
        ]

    def _process_csv(self, csv_reader, mapping, encoding, import_data):
        """Return a dict with every elements"""
        data = {}
        for line in csv_reader:
            line_data = {v: line[k].decode(encoding) for k, v in mapping.items()}
            parent_identifier = line_data.pop("parent_identifier") or None
            identifier = line_data.pop("classification_identifier")
            title = line_data.pop("title")
            if not identifier or not title:
                continue
            multi_values_keys = ("classification_categories",)
            for key in multi_values_keys:
                if key in line_data:
                    line_data[key] = line_data[key].split(",")
            if parent_identifier not in data:
                # Using dictionary avoid duplicated informations
                data[parent_identifier] = {}
            data[parent_identifier][identifier] = (title, line_data)
        return data

    def _import_node(self, node):
        args = (None, node.pop("classification_identifier"), node.pop("title"))
        raw_data = utils.importer(
            self.context, *args, vocabulary=self.vocabulary, **node
        )
        if raw_data[1]["data"]:
            self.data.append((raw_data[0], json.dumps(raw_data[1])))

    def _after_import(self):
        self.finished = True


class ImportSecondStepView(FormWrapper):
    form = ImportFormSecondStep
    index = ViewPageTemplateFile("import.pt")

    @property
    def data(self):
        """Return form data or an empty list"""
        return getattr(self.form_instance, "data", [])

    @property
    def finished(self):
        return getattr(self.form_instance, "finished", False)
