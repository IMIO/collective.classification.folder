# -*- coding: utf-8 -*-

from StringIO import StringIO
from collective.classification.folder import testing
from collective.classification.folder.form import importform
from operator import itemgetter
from persistent.dict import PersistentDict
from plone import api
from plone.namedfile import NamedBlobFile
from zope.annotation import IAnnotations
from zope.component import createObject

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
            ["", "001", "First", "", "F1", "Folder 1"],
            ["001", "001.1", "first 1", "F1", "F1.1", "Folder 1.1"],
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
            ["001", "001.1", "Folder 1", "Subfolder 1.1"],
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
            "column_1": "classification_categories",
            "column_3": "parent_identifier",
            "column_4": "internal_reference_no",
            "column_5": "title",
        }
        self.assertEqual(0, len(self.folders))
        form.update()
        form._import(data)
        self.assertEqual(2, len(form.data))
        self.assertEqual(["POST", "POST"], [e[0] for e in form.data])
        self.assertEqual(
            [2, 2],
            [len(json.loads(e[1])["data"][0]["__children__"]) for e in form.data],
        )

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
        result = form._process_csv(reader, mapping, "utf-8", {})
        expected_result = {
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
        self.assertEqual(expected_result, result)

    def test_process_csv_empty_values(self):
        """Test _process_csv with csv data that contains lines without folder"""
        form = importform.ImportFormSecondStep(self.folders, {})
        _csv = StringIO()
        lines = [
            ["", "001", "First", "", "F1", "Folder 1"],
            ["001", "001.1", "first 1", "F1", "F1.1", "Folder 1.1"],
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
        result = form._process_csv(reader, mapping, "utf-8", {})
        expected_result = {
            None: {u"F1": (u"Folder 1", {"classification_categories": [u"001"]})},
            u"F1": {
                u"F1.1": (u"Folder 1.1", {"classification_categories": [u"001.1"]}),
            },
        }
        self.assertEqual(expected_result, result)

    def test_process_csv_archived_values(self):
        """Test _process_csv with csv data with archived informations"""
        form = importform.ImportFormSecondStep(self.folders, self.layer["request"])
        _csv = StringIO()
        lines = [
            ["", "001", "First", "", "F1", "Folder 1", "1"],
            ["001", "001.1", "first 1", "F1", "F1.1", "Folder 1.1", ""],
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
        result = form._process_csv(reader, mapping, "utf-8", {})
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
                    {"classification_categories": [u"001.1"], "archived": False},
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
            ["Folder 1", "", "Folder 1.2", ""],
            ["Folder 1", "", "Folder 1.3", "archived"],
        ]
        for line in lines:
            _csv.write(";".join(line) + "\n")
        _csv.seek(0)
        reader = csv.reader(_csv, delimiter=";")
        data = {
            "column_0": "title_folder",
            "column_1": "archived_folder",
            "column_2": "title_subfolder",
            "column_3": "archived_subfolder",
        }
        mapping = {int(k.replace("column_", "")): v for k, v in data.items()}
        result = form._process_csv(reader, mapping, "utf-8", {})
        expected_result = {
            None: {
                "F0001": (
                    u"Folder 1",
                    {},
                )
            },
            "F0001": {
                "F0001-01": (
                    u"Folder 1.1",
                    {"archived": True},
                ),
                "F0001-02": (
                    u"Folder 1.2",
                    {},
                ),
                "F0001-03": (
                    u"Folder 1.3",
                    {"archived": True},
                ),
            },
        }
        self.assertEqual(expected_result, result)

    def test_process_csv_complex_titles(self):
        """Test _process_csv for title_folder/title_subfolder"""
        form = importform.ImportFormSecondStep(self.folders, self.layer["request"])
        reader = csv.reader(self._complex_csv, delimiter=";")
        data = {
            "column_2": "title_folder",
            "column_3": "title_subfolder",
        }
        mapping = {int(k.replace("column_", "")): v for k, v in data.items()}
        result = form._process_csv(reader, mapping, "utf-8", {})
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
            "column_2": "title_folder",
            "column_3": "title_subfolder",
        }
        mapping = {int(k.replace("column_", "")): v for k, v in data.items()}
        result = form._process_csv(reader, mapping, "utf-8", {})
        expected_result = {
            None: {
                "F0001": (u"Folder 1", {"classification_categories": [u"001"]}),
                "F0002": (u"Folder 2", {"classification_categories": [u"002"]}),
            },
            "F0001": {
                "F0001-01": (
                    u"Subfolder 1.1",
                    {"classification_categories": [u"001.1"]},
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
