# -*- coding: utf-8 -*-

from plone import api
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory


def get_portal_type(parent):
    """Return the portal_type to create based on the parent portal_type"""
    mapping = {
        "ClassificationFolders": "ClassificationFolder",
        "ClassificationFolder": "ClassificationSubfolder",
        None: "ClassificationSubfolder",
    }
    portal_type = mapping.get(getattr(parent, "portal_type", None))
    if not portal_type:
        raise ValueError(
            u"There is content type that can be created on {0}".format(
                parent.portal_type
            )
        )
    return portal_type


def importer(
    context,
    parent_identifier,
    identifier,
    title,
    data=None,
    _children=None,
    vocabulary=None,
):
    """
    Expected structure for _children (iterable) with dict element that contains :
    * identifier (String)
        * title (String)
        * data (Dict) with extra arguments
        * _children (Iterable of dicts)

    Return a list with chain of elements that need to be added or updated
    """
    parent = context
    if parent_identifier:
        raise ValueError()
    if not vocabulary:
        vocabulary = getUtility(
            IVocabularyFactory,
            "collective.classification.vocabularies:tree_id_mapping",
        )(context)
    elements = element_importer(parent, identifier, title, data, _children, vocabulary)
    children = []
    if len(elements) > 1:
        root, children = elements[0], elements[1:]
    else:
        root = elements[0]
    method, root_element = root
    if children:
        if "internal_reference_no" not in root_element:
            root_element["internal_reference_no"] = identifier
        root_element["__children__"] = children
    return method and "PATCH" or "POST", {"data": root_element and [root_element] or []}


def check_value(existing_element, key, data):
    if not existing_element:
        return True
    if getattr(existing_element, key) != data.get(key):
        return True
    return False


def element_importer(parent, identifier, title, data, children, vocabulary):
    """Format an element for import"""
    if parent:
        existing_elements = api.content.find(
            context=parent, internal_reference_no=identifier
        )
    else:
        existing_elements = []

    exist = False
    has_change = False
    element = {}
    existing_element = None
    portal_type = get_portal_type(parent)
    if len(existing_elements) >= 1:
        existing_element = parent[existing_elements[0].id]
        exist = True
    else:
        element["@type"] = portal_type
        element["internal_reference_no"] = identifier

    if not existing_element or existing_element.title != title:
        element["title"] = title
        has_change = True

    key = "classification_informations"
    if not existing_element or getattr(existing_element, key) != data.get(key):
        element[key] = data.get(key)
        has_change = True

    key = "classification_categories"
    if not existing_element:
        values = [vocabulary.getTerm(e).title for e in data.get(key)]
        element[key] = values
        has_change = True
    else:
        values = [vocabulary.getTerm(e).title for e in data.get(key)]
        if getattr(existing_element, key) != values:
            element[key] = values
            has_change = True

    elements = []
    if exist is True and has_change is True:
        element["internal_reference_no"] = identifier

    if portal_type == "ClassificationFolder":
        element = (exist, element)

    if exist is True and has_change is True:
        elements.append(element)
    elif exist is False:
        elements.append(element)
    elif portal_type == "ClassificationFolder":
        elements.append(element)

    if children:
        for child in children:
            args = (
                exist and existing_element or None,
                child["internal_reference_no"],
                child["title"],
                child["data"],
                child.get("_children"),
                vocabulary,
            )
            elements.extend(element_importer(*args))
    return elements
