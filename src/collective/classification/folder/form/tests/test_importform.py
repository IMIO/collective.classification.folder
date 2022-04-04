# -*- coding: utf-8 -*-

from StringIO import StringIO
from collective.classification.folder import testing
from collective.classification.folder.content.vocabularies import services_in_charge_vocabulary
from collective.classification.folder.form import importform
from operator import itemgetter
from persistent.dict import PersistentDict
from plone import api
from plone.namedfile import NamedBlobFile
from zope.annotation import IAnnotations
from zope.component import createObject
from zope.component import getUtility
from zope.component.interfaces import Invalid
from zope.schema.interfaces import IVocabularyFactory

import csv
import json
import unittest


class TestImportForm(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_FOLDER_FUNCTIONAL_TESTING
    maxDiff = 3000

    def setUp(self):
        self.portal = self.layer["portal"]
        self.folder = api.content.create(
            id="folder", type="Folder", container=self.portal
        )
        container = api.content.create(
            title="Container", type="ClassificationContainer", container=self.folder
        )
        structure = (
            (u"001", u"First", ((u"001.1", u"first 1"), (u"001.2", u"second 1"))),
            (u"002", u"Second", ((u"002.1", u"first"),)),
        )
        for id, title, subelements in structure:
            category = self._create_category(id, title)
            container._add_element(category)
            if subelements:
                for id, title in subelements:
                    subcategory = self._create_category(id, title)
                    category._add_element(subcategory)
        self.folders = api.content.create(
            title="Folders", type="ClassificationFolders", container=self.folder
        )
        api.group.create('group_1', 'My new group 1')

    def tearDown(self):
        api.content.delete(self.folder)

    def _create_category(self, id, title):
        category = createObject("ClassificationCategory")
        category.identifier = id
        category.title = title
        return category

    @property
    def _csv(self):
        """Return a fake csv with data"""
        csv = StringIO()
        lines = [
            ["", "001", "First", "", "F1", '"Folder \n1\n"'],
            ["001", "001.1", "first 1", "F1", "F1.1", "Folder 1.1 "],
            ["001", "001.2", "second 1", "F1", "F1.2", "Folder 1.2"],
            ["", "002", "Second", "", "F2", "Folder 2"],
            ["002", "002.1", "first 2", "F2", "F2.1A", "Folder 2.1 A"],
            ["002", "002.1", "first 2", "F2", "F2.1B", "Folder 2.1 B"],
        ]
        for line in lines:
            csv.write(";".join(line) + "\n")
        csv.seek(0)
        return csv

    @property
    def _complex_csv(self):
        """Return a fake csv with a more complex structure"""
        csv = StringIO()
        lines = [
            # ["Code Folder", "Code Subfolder", "Folder Title", "Subfolder Title"],
            ["001", "001, 001.1", '"Folder 1\n"', '"Subfolder \n1.1"'],
            ["001", "001.2", "", "Subfolder 1.2"],
            ["001", "", "", "Subfolder 1.3"],
            ["002", "002.1", "Folder 2", "Subfolder 2.1"],
            ["002", "002.1", "Folder 2", "Subfolder 2.2"],
            ["002", "", "", "Subfolder 2.3"],
        ]
        for line in lines:
            csv.write(";".join(line) + "\n")
        csv.seek(0)
        return csv

    def _sort_processed_data(self, data):
        """Ensure that processed data are correctly sorted before comparison"""
        data = sorted(data, key=itemgetter("internal_reference_no"))
        for element in data:
            if not element["_children"]:
                continue
            element["_children"] = self._sort_processed_data(element["_children"])
        return data

    def test_second_step_import_basic(self):
        """Test importing csv data"""
        form = importform.ImportFormSecondStep(self.folders, self.layer["request"])
        form.data = []
        annotations = IAnnotations(self.folders)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["separator"] = u";"
        annotation["has_header"] = False
        annotation["source"] = NamedBlobFile(
            data=self._csv.read(),
            contentType=u"text/csv",
            filename=u"test.csv",
        )
        data = {
            "treating_groups": None,
            "column_1": "classification_categories",
            "column_3": "parent_identifier",
            "column_4": "internal_reference_no",
            "column_5": "title",
        }
        self.assertEqual(0, len(self.folders))
        form.update()
        form._import(data)
        # direct_operation is now used
        # self.assertEqual(2, len(form.data))
        # self.assertEqual(["POST", "POST"], [e[0] for e in form.data])
        # self.assertEqual(
        #     [2, 2],
        #     [len(json.loads(e[1])["data"][0]["__children__"]) for e in form.data],
        # )

    def test_process_data_basic(self):
        """Tests _process_data with basic data structure"""
        form = importform.ImportFormSecondStep(self.folders, {})
        data = {
            None: {
                u"F1": (u"Folder 1", {"classification_categories": [u"001"]}),
                u"F2": (u"Folder 2", {"classification_categories": [u"002"]}),
            },
            u"F1": {
                u"F1.1": (u"Folder 1.1", {"classification_categories": [u"001.1"]}),
                u"F1.2": (u"Folder 1.2", {"classification_categories": [u"001.2"]}),
            },
            u"F2": {
                u"F2.1A": (u"Folder 2.1 A", {"classification_categories": [u"002.1"]}),
                u"F2.1B": (u"Folder 2.1 B", {"classification_categories": [u"002.1"]}),
            },
        }
        expected_results = [
            {
                "internal_reference_no": u"F1",
                "title": u"Folder 1",
                "data": {"classification_categories": [u"001"]},
                "_children": [
                    {
                        "internal_reference_no": u"F1.1",
                        "title": u"Folder 1.1",
                        "data": {"classification_categories": [u"001.1"]},
                        "_children": [],
                    },
                    {
                        "internal_reference_no": u"F1.2",
                        "title": u"Folder 1.2",
                        "data": {"classification_categories": [u"001.2"]},
                        "_children": [],
                    },
                ],
            },
            {
                "internal_reference_no": u"F2",
                "title": u"Folder 2",
                "data": {"classification_categories": [u"002"]},
                "_children": [
                    {
                        "internal_reference_no": u"F2.1A",
                        "title": u"Folder 2.1 A",
                        "data": {"classification_categories": [u"002.1"]},
                        "_children": [],
                    },
                    {
                        "internal_reference_no": u"F2.1B",
                        "title": u"Folder 2.1 B",
                        "data": {"classification_categories": [u"002.1"]},
                        "_children": [],
                    },
                ],
            },
        ]
        processed_data = form._process_data(data)
        self.assertEqual(self._sort_processed_data(processed_data), expected_results)

    def test_process_data_archived(self):
        """Tests _process_data with archived informations"""
        form = importform.ImportFormSecondStep(self.folders, {})
        data = {
            None: {
                u"F1": (
                    u"Folder 1",
                    {"classification_categories": [u"001"], "archived": False},
                ),
            },
            u"F1": {
                u"F1.1": (
                    u"Folder 1.1",
                    {"classification_categories": [u"001.1"], "archived": True},
                ),
                u"F1.2": (
                    u"Folder 1.2",
                    {"classification_categories": [u"001.2"], "archived": False},
                ),
            },
        }
        expected_results = [
            {
                "internal_reference_no": u"F1",
                "title": u"Folder 1",
                "data": {"classification_categories": [u"001"], "archived": False},
                "_children": [
                    {
                        "internal_reference_no": u"F1.1",
                        "title": u"Folder 1.1",
                        "data": {
                            "classification_categories": [u"001.1"],
                            "archived": True,
                        },
                        "_children": [],
                    },
                    {
                        "internal_reference_no": u"F1.2",
                        "title": u"Folder 1.2",
                        "data": {
                            "classification_categories": [u"001.2"],
                            "archived": False,
                        },
                        "_children": [],
                    },
                ],
            },
        ]
        processed_data = form._process_data(data)
        self.assertEqual(self._sort_processed_data(processed_data), expected_results)

    def test_process_csv_basic(self):
        """Test _process_csv with basic csv data"""
        form = importform.ImportFormSecondStep(self.folders, {})
        reader = csv.reader(self._csv, delimiter=";")
        data = {
            "column_1": "classification_categories",
            "column_3": "parent_identifier",
            "column_4": "internal_reference_no",
            "column_5": "title",
        }
        mapping = {int(k.replace("column_", "")): v for k, v in data.items()}
        result = form._process_csv(reader, mapping, "utf-8", {}, treating_groups='Administrators')
        expected_result = {
            None: {
                u"F1": (u"Folder 1", {"classification_categories": [u"001"], 'treating_groups': 'Administrators'}),
                u"F2": (u"Folder 2", {"classification_categories": [u"002"], 'treating_groups': 'Administrators'}),
            },
            u"F1": {
                u"F1.1": (u"Folder 1.1", {"classification_categories": [u"001.1"],
                                          'treating_groups': 'Administrators'}),
                u"F1.2": (u"Folder 1.2", {"classification_categories": [u"001.2"],
                                          'treating_groups': 'Administrators'}),
            },
            u"F2": {
                u"F2.1A": (u"Folder 2.1 A", {"classification_categories": [u"002.1"],
                                             'treating_groups': 'Administrators'}),
                u"F2.1B": (u"Folder 2.1 B", {"classification_categories": [u"002.1"],
                                             'treating_groups': 'Administrators'}),
            },
        }
        self.assertEqual(expected_result, result)

    def test_process_csv_empty_values(self):
        """Test _process_csv with csv data that contains lines without folder"""
        form = importform.ImportFormSecondStep(self.folders, {})
        _csv = StringIO()
        lines = [
            ["", "001", "First", "", "F1", "Folder 1"],
            ["001", "001.1", "first 1", "F1", "F1.1", "Folder 1/1"],
            ["", "003", "Third", "", "", ""],
        ]
        for line in lines:
            _csv.write(";".join(line) + "\n")
        _csv.seek(0)
        reader = csv.reader(_csv, delimiter=";")
        data = {
            "column_1": "classification_categories",
            "column_3": "parent_identifier",
            "column_4": "internal_reference_no",
            "column_5": "title",
        }
        mapping = {int(k.replace("column_", "")): v for k, v in data.items()}
        result = form._process_csv(reader, mapping, "utf-8", {}, treating_groups=None, replace_slash=True)
        expected_result = {
            None: {u"F1": (u"Folder 1", {"classification_categories": [u"001"]})},
            u"F1": {
                u"F1.1": (u"Folder 1-1", {"classification_categories": [u"001.1"]}),
            },
        }
        self.assertEqual(expected_result, result)

    def test_process_csv_archived_values(self):
        """Test _process_csv with csv data with archived informations"""
        form = importform.ImportFormSecondStep(self.folders, self.layer["request"])
        _csv = StringIO()
        lines = [
            ["", "001", "First", "", "F1", "Folder 1", "1"],
            ["001", "001.1, 001.2", "first 1", "F1", "F1.1", "Folder 1.1", " "],
            ["001", "001.2", "first 1", "F1", "F1.2", "Folder 1.2", "archived"],
        ]
        for line in lines:
            _csv.write(";".join(line) + "\n")
        _csv.seek(0)
        reader = csv.reader(_csv, delimiter=";")
        data = {
            "column_1": "classification_categories",
            "column_3": "parent_identifier",
            "column_4": "internal_reference_no",
            "column_5": "title",
            "column_6": "archived",
        }
        mapping = {int(k.replace("column_", "")): v for k, v in data.items()}
        result = form._process_csv(reader, mapping, "utf-8", {}, treating_groups=None)
        expected_result = {
            None: {
                u"F1": (
                    u"Folder 1",
                    {"classification_categories": [u"001"], "archived": True},
                )
            },
            u"F1": {
                u"F1.1": (
                    u"Folder 1.1",
                    {"classification_categories": [u"001.1", u"001.2"], "archived": False},
                ),
                u"F1.2": (
                    u"Folder 1.2",
                    {"classification_categories": [u"001.2"], "archived": True},
                ),
            },
        }
        self.assertEqual(expected_result, result)

    def test_process_csv_complex_archived_values(self):
        """Test _process_csv with csv data with archived informations"""
        form = importform.ImportFormSecondStep(self.folders, self.layer["request"])
        _csv = StringIO()
        lines = [
            ["Folder 1", "", "Folder 1.1", "1"],
            ["Folder 1", "", "Folder 1.2", " "],
            ["Folder 1", "", "Folder 1.3", "archived"],
        ]
        for line in lines:
            _csv.write(";".join(line) + "\n")
        _csv.seek(0)
        reader = csv.reader(_csv, delimiter=";")
        data = {
            "column_0": "folder_title",
            "column_1": "folder_archived",
            "column_2": "subfolder_title",
            "column_3": "subfolder_archived",
        }
        mapping = {int(k.replace("column_", "")): v for k, v in data.items()}
        result = form._process_csv(reader, mapping, "utf-8", {}, treating_groups='Administrators')
        expected_result = {
            None: {
                "F0001": (
                    u"Folder 1",
                    {'treating_groups': 'Administrators'},
                )
            },
            "F0001": {
                "F0001-01": (
                    u"Folder 1.1",
                    {"archived": True, 'treating_groups': 'Administrators'},
                ),
                "F0001-02": (
                    u"Folder 1.2",
                    {'treating_groups': 'Administrators'},
                ),
                "F0001-03": (
                    u"Folder 1.3",
                    {"archived": True, 'treating_groups': 'Administrators'},
                ),
            },
        }
        self.assertEqual(expected_result, result)

    def test_process_csv_complex_titles(self):
        """Test _process_csv for folder_title/subfolder_title"""
        form = importform.ImportFormSecondStep(self.folders, self.layer["request"])
        reader = csv.reader(self._complex_csv, delimiter=";")
        data = {
            "column_2": "folder_title",
            "column_3": "subfolder_title",
        }
        mapping = {int(k.replace("column_", "")): v for k, v in data.items()}
        result = form._process_csv(reader, mapping, "utf-8", {}, treating_groups=None)
        expected_result = {
            None: {
                "F0001": (u"Folder 1", {}),
                "F0002": (u"Folder 2", {}),
            },
            "F0001": {
                "F0001-01": (u"Subfolder 1.1", {}),
                "F0001-02": (u"Subfolder 1.2", {}),
                "F0001-03": (u"Subfolder 1.3", {}),
            },
            "F0002": {
                "F0002-01": (u"Subfolder 2.1", {}),
                "F0002-02": (u"Subfolder 2.2", {}),
                "F0002-03": (u"Subfolder 2.3", {}),
            },
        }
        self.assertEqual(expected_result, result)

    def test_process_csv_complex_categories(self):
        """Test _process_csv for folder_categories/subfolder_categories"""
        form = importform.ImportFormSecondStep(self.folders, self.layer["request"])
        reader = csv.reader(self._complex_csv, delimiter=";")
        data = {
            "column_0": "folder_categories",
            "column_1": "subfolder_categories",
            "column_2": "folder_title",
            "column_3": "subfolder_title",
        }
        mapping = {int(k.replace("column_", "")): v for k, v in data.items()}
        result = form._process_csv(reader, mapping, "utf-8", {}, treating_groups=None)
        expected_result = {
            None: {
                "F0001": (u"Folder 1", {"classification_categories": [u"001"]}),
                "F0002": (u"Folder 2", {"classification_categories": [u"002"]}),
            },
            "F0001": {
                "F0001-01": (
                    u"Subfolder 1.1",
                    {"classification_categories": [u"001", u"001.1"]},
                ),
                "F0001-02": (
                    u"Subfolder 1.2",
                    {"classification_categories": [u"001.2"]},
                ),
                "F0001-03": (
                    u"Subfolder 1.3",
                    {"classification_categories": [u"001"]},
                ),
            },
            "F0002": {
                "F0002-01": (
                    u"Subfolder 2.1",
                    {"classification_categories": [u"002.1"]},
                ),
                "F0002-02": (
                    u"Subfolder 2.2",
                    {"classification_categories": [u"002.1"]},
                ),
                "F0002-03": (
                    u"Subfolder 2.3",
                    {"classification_categories": [u"002"]},
                ),
            },
        }
        self.assertEqual(expected_result, result)

    def test_replace_newline(self):
        form = importform.ImportFormSecondStep(self.folders, self.layer["request"])
        self.assertEquals(form._replace_newline(u' \n '), u' ')
        self.assertEquals(form._replace_newline(u'\n'), u'')
        self.assertEquals(form._replace_newline(u'\n A'), u'A')
        self.assertEquals(form._replace_newline(u'B \n'), u'B')
        self.assertEquals(form._replace_newline(u' \n\n '), u' ')
        self.assertEquals(form._replace_newline(u'.\n '), u'. ')
        self.assertEquals(form._replace_newline(u' \nL'), u' L')
        self.assertEquals(form._replace_newline(u'x\nL'), u'x L')
        self.assertEquals(form._replace_newline(u'x\nLe\nf'), u'x Le f')
        self.assertEquals(form._replace_newline(u' \n.\n '), u' . ')

    def test_replace_newline_by_crlf(self):
        form = importform.ImportFormSecondStep(self.folders, self.layer["request"])
        self.assertEquals(form._replace_newline_by_crlf(u'\n A'), u'\r\nA')
        self.assertEquals(form._replace_newline_by_crlf(u'B\n'), u'B\r\n')
        self.assertEquals(form._replace_newline_by_crlf(u'B\r\nA'), u'B\r\nA')

    def test_process_csv_informations_values(self):
        """Test _process_csv with csv data with classification_informations"""
        form = importform.ImportFormSecondStep(self.folders, self.layer["request"])
        _csv = StringIO()
        lines = [
            ["", "001", "First", "", "F1", "Folder 1", "This is more informations."],
            ["001", "001.1, 001.2", "first 1", "F1", "F1.1", "Folder 1.1", '"Also\nbut with another line"'],
            ["001", "001.2", "first 1", "F1", "F1.2", "Folder 1.2", ""],
        ]
        for line in lines:
            _csv.write(";".join(line) + "\n")
        _csv.seek(0)
        reader = csv.reader(_csv, delimiter=";")
        data = {
            "column_1": "classification_categories",
            "column_3": "parent_identifier",
            "column_4": "internal_reference_no",
            "column_5": "title",
            "column_6": "classification_informations",
        }
        mapping = {int(k.replace("column_", "")): v for k, v in data.items()}
        result = form._process_csv(reader, mapping, "utf-8", {}, treating_groups=None)
        expected_result = {
            None: {
                u"F1": (
                    u"Folder 1",
                    {"classification_categories": [u"001"],
                     "classification_informations": u'This is more informations.'},
                )
            },
            u"F1": {
                u"F1.1": (
                    u"Folder 1.1",
                    {"classification_categories": [u"001.1", u"001.2"],
                     "classification_informations": u'Also\r\nbut with another line'},
                ),
                u"F1.2": (
                    u"Folder 1.2",
                    {"classification_categories": [u"001.2"],
                     "classification_informations": u''},
                ),
            },
        }
        self.assertEqual(expected_result, result)

    def test_process_csv_complex_informations_values(self):
        """Test _process_csv with csv data with classification_informations"""
        form = importform.ImportFormSecondStep(self.folders, self.layer["request"])
        _csv = StringIO()
        lines = [
            ["Folder 1", "", "Room A", "Folder 1.1", '"This is more informations.\n"'],
            ["Folder 1", "", "", "Folder 1.2", '"Yet\nAnother line\nAnd a third"'],
            ["Folder 1", "", "", "Folder 1.3", ""],
        ]
        for line in lines:
            _csv.write(";".join(line) + "\n")
        _csv.seek(0)
        reader = csv.reader(_csv, delimiter=";")
        data = {
            "column_0": "folder_title",
            "column_1": "folder_archived",
            "column_2": "folder_informations",
            "column_3": "subfolder_title",
            "column_4": "subfolder_informations",
        }
        mapping = {int(k.replace("column_", "")): v for k, v in data.items()}
        result = form._process_csv(reader, mapping, "utf-8", {}, treating_groups=None)
        expected_result = {
            None: {
                "F0001": (
                    u"Folder 1",
                    {'classification_informations': u'Room A'},
                )
            },
            "F0001": {
                "F0001-01": (
                    u"Folder 1.1",
                    {'classification_informations': u'This is more informations.'},
                ),
                "F0001-02": (
                    u"Folder 1.2",
                    {'classification_informations': u'Yet\r\nAnother line\r\nAnd a third'},
                ),
                "F0001-03": (
                    u"Folder 1.3",
                    {},
                ),
            },
        }
        self.assertEqual(expected_result, result)

    def test_process_csv_complex_irn(self):
        """Test _process_csv for internal_reference_no"""
        form = importform.ImportFormSecondStep(self.folders, self.layer["request"])
        _csv = StringIO()
        lines = [
            ["Folder 1", "1", "", ""],
            ["Folder 1", "1", "Subfolder 1.1", "11"],
            ["Folder 1", "1", "Subfolder 1.2", "12"],
            ["Folder 2/a", "2", "", ""],
            ["Folder 2/a", "2", "Subfolder 2/a.1", "21"],
            ["Folder 2/a", "2", "Subfolder 2/a.2", "22"],
        ]
        for line in lines:
            _csv.write(";".join(line) + "\n")
        _csv.seek(0)
        reader = csv.reader(_csv, delimiter=";")
        data = {
            "column_0": "folder_title",
            "column_1": "folder_internal_reference_no",
            "column_2": "subfolder_title",
            "column_3": "subfolder_internal_reference_no",
        }
        mapping = {int(k.replace("column_", "")): v for k, v in data.items()}
        result = form._process_csv(reader, mapping, "utf-8", {}, treating_groups=None, replace_slash=True)
        expected_result = {
            None: {
                "1": (u"Folder 1", {u'internal_reference_no': u'1'}),
                "2": (u"Folder 2-a", {u'internal_reference_no': u'2'}),
            },
            "1": {
                "11": (u"Subfolder 1.1", {u'internal_reference_no': u'11'}),
                "12": (u"Subfolder 1.2", {u'internal_reference_no': u'12'}),
            },
            "2": {
                "21": (u"Subfolder 2-a.1", {u'internal_reference_no': u'21'}),
                "22": (u"Subfolder 2-a.2", {u'internal_reference_no': u'22'}),
            },
        }
        self.assertEqual(expected_result, result)

    def test_process_csv_complex_treating_groups_title(self):
        """Test _process_csv with csv data with treating_groups_title column"""
        groups = [(t.value, t.title) for t in services_in_charge_vocabulary()
                  if t.value not in ('AuthenticatedUsers', 'Site Administrators')]
        self.assertListEqual(groups, [('Administrators', 'Administrators'), ('Reviewers', 'Reviewers'),
                                      ('group_1', 'My new group 1')])
        form = importform.ImportFormSecondStep(self.folders, self.layer["request"])
        _csv = StringIO()
        lines = [
            ["001", "Folder 1", "My new group 1", "001.1", "Folder 1.1"],
            ["001", "Folder 1", "Reviewers", "001.2", "Folder 1.2"],
        ]
        for line in lines:
            _csv.write(";".join(line) + "\n")
        _csv.seek(0)
        reader = csv.reader(_csv, delimiter=";")
        data = {
            "column_0": "folder_categories",
            "column_1": "folder_title",
            "column_2": "treating_groups_title",
            "column_3": "subfolder_categories",
            "column_4": "subfolder_title",
        }
        mapping = {int(k.replace("column_", "")): v for k, v in data.items()}
        result = form._process_csv(reader, mapping, "utf-8", {}, treating_groups=None)
        expected_result = {
            None: {
                "F0001": (
                    u"Folder 1",
                    {'treating_groups_title': u'My new group 1',
                     'classification_categories': [u'001']},
                )
            },
            "F0001": {
                "F0001-01": (
                    u"Folder 1.1",
                    {'treating_groups_title': u'My new group 1',
                     'classification_categories': [u'001.1']},
                ),
                "F0001-02": (
                    u"Folder 1.2",
                    {'treating_groups_title': u'Reviewers',
                     'classification_categories': [u'001.2']},
                ),
            },
        }
        self.assertEqual(expected_result, result)
        # import nodes
        form.vocabulary = getUtility(IVocabularyFactory,
                                     "collective.classification.vocabularies:tree_id_mapping")(self.folders)
        form.data = []
        form._import_node(form._process_data(result)[0])
        # now direct_operation is done
        # data_to_import = json.loads(form.data[0][1])['data']
        # folder_dic = data_to_import[0]
        # self.assertEqual(folder_dic[u'title'], u'Folder 1')
        # self.assertEqual(folder_dic[u'treating_groups'], u'group_1')
        # subfolders = folder_dic[u'__children__']
        # self.assertEqual(subfolders[0][u'title'], u'Folder 1.1')
        # self.assertEqual(subfolders[0][u'treating_groups'], u'group_1')
        # self.assertEqual(subfolders[1][u'title'], u'Folder 1.2')
        # self.assertEqual(subfolders[1][u'treating_groups'], u'Reviewers')
        # # treating_groups_title not found
        # result[None]['F0001'] = (u"Folder 1", {'treating_groups_title': u'Unknown group title',
        #                                        'classification_categories': [u'001']})
        # self.assertRaises(Invalid, form._import_node, form._process_data(result)[0])
        self.assertIn('folder-1', self.folders)
        self.assertIn('folder-1.1', self.folders['folder-1'])
        self.assertIn('folder-1.2', self.folders['folder-1'])

    def test_process_csv_replace_slash(self):
        """Test _process_csv with csv data that contains slashes"""
        form = importform.ImportFormSecondStep(self.folders, self.layer["request"])
        _csv = StringIO()
        lines = [
            ["Folder 1/a", "1", "", ""],
            ["Folder 1/a", "1", "Subfolder 1/a.1 // cor", "11"],
            ["Folder 1/a", "1", "Subfolder 1/a.2", "12"],
        ]
        for line in lines:
            _csv.write(";".join(line) + "\n")
        _csv.seek(0)
        reader = csv.reader(_csv, delimiter=";")
        data = {
            "column_0": "folder_title",
            "column_2": "subfolder_title",
        }
        mapping = {int(k.replace("column_", "")): v for k, v in data.items()}
        result = form._process_csv(reader, mapping, "utf-8", {}, replace_slash=True)
        expected_result = {
            None: {
                "F0001": (u"Folder 1-a", {}),
            },
            "F0001": {
                "F0001-01": (u"Subfolder 1-a.1 -- cor", {}),
                "F0001-02": (u"Subfolder 1-a.2", {}),
            },
        }
        self.assertEqual(expected_result, result)
