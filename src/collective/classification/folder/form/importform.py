# -*- coding: utf-8 -*-
from collective.classification.folder.content.vocabularies import services_in_charge_vocabulary
from collective.classification.tree.form.importform import GeneratedBool
from collective.classification.tree.form.importform import GeneratedChoice
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from collective.classification.folder import _
from collective.classification.folder import utils
from collective.classification.folder.content.vocabularies import ServiceInChargeSourceBinder
from collective.classification.tree import _ as _ct
from collective.classification.tree import utils as tree_utils
from collective.classification.tree.form import importform as baseform
from plone import api
from plone.z3cform.layout import FormWrapper
from zope.annotation import IAnnotations
from zope.component import getUtility
from zope.interface.exceptions import Invalid
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import invariant
from zope.schema.interfaces import IVocabularyFactory

import json
import re


ANNOTATION_KEY = baseform.ANNOTATION_KEY


class IImportFirstStep(baseform.IImportFirstStep):
    @invariant
    def validate_csv_data(obj):
        return tree_utils.validate_csv_data(obj, min_length=2)


def extract_required_columns(obj):
    """Return filled columns from obj"""
    columns = [e for e in obj._Data_schema___ if e.startswith("column_")]
    filled_columns = [getattr(obj, c) for c in columns if getattr(obj, c)]
    required = []
    if "title" in filled_columns:
        required.append("title")
    if "parent_identifier" in filled_columns:
        required.extend(["parent_identifier", "identifier"])
    if "subfolder_title" in filled_columns:
        required.extend(["folder_title"])  # subfolder_title can be empty but folder_title must be there to get parent
    if not required:
        required.append("title")
    return required


class IImportSecondStepBase(Interface):

    replace_slash = GeneratedBool(
        title=_ct(u"Replace slash in title"),
        default=True,
        required=False,
    )

    treating_groups = GeneratedChoice(  # this overrided Choice field is adapted to folders (see tree importform)
        title=_(u"Service in charge"),
        description=_(u"Service that will be set on all imported folders"),
        source=ServiceInChargeSourceBinder(),
        required=False,
    )

    @invariant
    def validate_columns(obj):
        columns = [v for k, v in obj._Data_data___.items() if k.startswith("column_")]
        if obj._Data_data___.get('treating_groups') is not None and u'treating_groups_title' in columns:
            raise Invalid(_("You can't select both a treating_groups and a column associated to treating groups title"))
        required = extract_required_columns(obj)
        return tree_utils.validate_csv_columns(obj, required)

    @invariant
    def validate_data(obj):
        annotations = IAnnotations(obj.__context__)
        required = extract_required_columns(obj)
        # required.remove("folder_title")  # folder title may be empty #TODO which case ??
        return tree_utils.validate_csv_content(
            obj,
            annotations[ANNOTATION_KEY],
            required,
        )


class ImportFormFirstStep(baseform.ImportFormFirstStep):
    pass


@implementer(baseform.IImportFormView)
class ImportFirstStepView(FormWrapper):
    form = ImportFormFirstStep


class ImportFormSecondStep(baseform.ImportFormSecondStep):
    _vocabulary = u"collective.classification.vocabularies:folders_import_keys"
    base_schema = IImportSecondStepBase

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
                "internal_reference_no": k,
                "title": v[0],
                "data": v[1],
                "_children": self._process_data(data, key=k),
            }
            for k, v in data[key].items()
        ]

    def _reference_generator(self):
        if not hasattr(self, "_ref_number"):
            number_key = (
                "collective.classification.folder.browser.settings."
                "IClassificationConfig.folder_number"
            )
            self._ref_number = api.portal.get_registry_record(number_key, default=1)
        reference = utils.evaluate_internal_reference(
            self.context,
            self.request,
            "folder_number",
            "folder_talexpression",
            number=self._ref_number,
        )
        self._ref_number += 1
        return reference

    def _find_next_available_subreference(self, data, reference):
        base = 1
        formatter = "{0}-{1:02d}"
        ref = formatter.format(reference, base)
        while ref in data[reference].keys():
            base += 1
            ref = formatter.format(reference, base)
        return ref

    def _replace_newline(self, string, replace_slash=False):
        """Replaced newline by a space or deleted it, following character before and after"""
        def repl(mo):
            if mo.group(0) in (u'\n', u' \n', u'\n '):
                return u''
            elif mo.group(1) == u' ' and mo.group(2) == u' ':
                return u' '
            elif mo.group(1) == u' ':
                return u' {}'.format(mo.group(2))
            elif mo.group(2) == u' ':
                return u'{} '.format(mo.group(1))
            else:
                return u'{} {}'.format(mo.group(1), mo.group(2))

        if replace_slash:
            string = string.replace('/', '-')
        str1 = re.sub('(^|.)\n+(.|$)', repl, string, re.UNICODE)
        # Need to call it a second time to resolve overlapping matches
        return re.sub('(^|.)\n+(.|$)', repl, str1, re.UNICODE)

    def _replace_newline_by_crlf(self, string):
        """Replaced newline by a cr lf for schema.Text field"""
        return re.sub('(^|[^\r])\n( *)', '\\1\r\n', string, re.UNICODE)

    def _process_multikey_values(self, line_data):
        multi_values_keys = ("classification_categories",)
        for key in multi_values_keys:
            if key in line_data:
                line_data[key] = [val.strip(' \n') for val in line_data[key].split(",")]

    def _process_boolean_values(self, line_data):
        boolean_values_keys = ("archived",)
        for key in boolean_values_keys:
            if key in line_data:
                line_data[key] = line_data[key] and True or False

    def _process_with_ref(self, data, line_data, replace_slash=False):
        parent_identifier = line_data.pop("parent_identifier", None) or None
        identifier = line_data.pop("internal_reference_no")
        title = self._replace_newline(line_data.pop("title"), replace_slash=replace_slash)
        if not identifier or not title:
            return
        self._process_multikey_values(line_data)
        self._process_boolean_values(line_data)
        if parent_identifier not in data:
            # Using dictionary avoid duplicated informations
            data[parent_identifier] = {}
        if line_data.get('classification_informations'):
            line_data['classification_informations'] = self._replace_newline_by_crlf(
                line_data['classification_informations'])
        data[parent_identifier][identifier] = (title, line_data)

    def _process_without_ref(self, data, line_data, last_ref, last_title, replace_slash=False):
        folder_title = line_data.pop("folder_title", None) or None
        subfolder_title = line_data.pop("subfolder_title", None) or None

        folder_mapping = {
            "folder_categories": "classification_categories",
            "folder_archived": "archived",
            "treating_groups": "treating_groups",
            "folder_informations": "classification_informations",
            "folder_internal_reference_no": "internal_reference_no",
            "treating_groups_title": "treating_groups_title",
        }
        subfolder_mapping = {
            "subfolder_categories": "classification_categories",
            "subfolder_archived": "archived",
            "subfolder_informations": "classification_informations",
            "treating_groups": "treating_groups",
            "subfolder_internal_reference_no": "internal_reference_no",
            "treating_groups_title": "treating_groups_title",
        }

        folder_data = {
            v: line_data.get(k) for k, v in folder_mapping.items() if line_data.get(k)
        }
        subfolder_data = {
            v: line_data.get(k)
            for k, v in subfolder_mapping.items()
            if line_data.get(k)
        }
        if folder_data.get('classification_informations'):
            folder_data['classification_informations'] = self._replace_newline_by_crlf(
                folder_data['classification_informations'])
        if subfolder_data.get('classification_informations'):
            subfolder_data['classification_informations'] = self._replace_newline_by_crlf(
                subfolder_data['classification_informations'])

        if folder_title is not None:
            folder_title = self._replace_newline(folder_title, replace_slash=replace_slash)
        # if there is a irn related to parent, we get it. Otherwise we generate it
        if folder_data.get('internal_reference_no'):
            last_ref = folder_data['internal_reference_no']
            last_title = folder_title
        elif folder_title is not None and folder_title != last_title:
            last_ref = self._reference_generator()
            last_title = folder_title

        if last_ref is None:
            # This should never happen
            return None, None

        if None not in data:
            # Initialize first level if necessary
            data[None] = {}
        self._process_multikey_values(folder_data)
        self._process_boolean_values(folder_data)
        if last_ref not in data[None]:
            # We need to create the folder before creating subfolders
            data[None][last_ref] = (folder_title, folder_data)

        # Handled the case when a line is defined for a folder and another for a folder and a subfolder
        if subfolder_title is None and not subfolder_data.get('internal_reference_no'):
            return last_ref, last_title

        subfolder_title = self._replace_newline(subfolder_title or u'', replace_slash=replace_slash)

        # Inherit categories from folder if relevant
        key = "classification_categories"
        if not subfolder_data.get(key) and folder_data.get(key):
            subfolder_data[key] = folder_data[key]
        else:
            self._process_multikey_values(subfolder_data)
        self._process_boolean_values(subfolder_data)

        if last_ref not in data:
            data[last_ref] = {}

        if subfolder_data.get('internal_reference_no'):
            subfolder_ref = subfolder_data['internal_reference_no']
        else:
            subfolder_ref = self._find_next_available_subreference(data, last_ref)
        data[last_ref][subfolder_ref] = (subfolder_title, subfolder_data)

        return last_ref, last_title

    def _process_csv(self, csv_reader, mapping, encoding, import_data, **kwargs):
        """Return a dict with every elements"""
        data = {}
        last_ref = None
        last_title = None
        for line in csv_reader:
            line_data = {v: line[k].strip(' \n').decode(encoding) for k, v in mapping.items()}
            if kwargs.get('treating_groups', None):
                line_data['treating_groups'] = kwargs['treating_groups']
            if "parent_identifier" in line_data or "internal_reference_no" in line_data:
                self._process_with_ref(data, line_data, replace_slash=kwargs.get('replace_slash', False))
            else:
                last_ref, last_title = self._process_without_ref(
                    data,
                    line_data,
                    last_ref,
                    last_title,
                    replace_slash=kwargs.get('replace_slash', False),
                )

        return data

    def _get_treating_groups_titles(self):
        voc = services_in_charge_vocabulary(self.context)
        return {t.title: t.value for t in voc}

    def _import_node(self, node):
        args = (None, node.pop("internal_reference_no"), node.pop("title"))
        raw_data = utils.importer(
            self.context, *args, vocabulary=self.vocabulary,
            treating_groups_titles=self._get_treating_groups_titles(),
            **node
        )
        if raw_data[1]["data"]:
            self.data.append((raw_data[0], json.dumps(raw_data[1])))

    def _after_import(self):
        self.finished = True


@implementer(baseform.IImportFormView)
class ImportSecondStepView(FormWrapper):
    form = ImportFormSecondStep
    index = ViewPageTemplateFile("import.pt")  # contains javascript to call rest methods

    @property
    def data(self):
        """Return form data or an empty list"""
        return getattr(self.form_instance, "data", [])

    @property
    def finished(self):
        return getattr(self.form_instance, "finished", False)
