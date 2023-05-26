# -*- coding: utf-8 -*-

from plone import api
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component.interfaces import ComponentLookupError
from zope.component.interfaces import Invalid
from zope.i18n import translate
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
    treating_groups_titles={},
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
    elements = element_importer(parent, identifier, title, data, _children, vocabulary, treating_groups_titles)
    children = []
    if len(elements) > 1:  # folder is first, then subfolders
        root, children = elements[0], elements[1:]
    else:
        root = elements[0]
    method, root_element = root  # method = exists (True, False), root_element = Folder
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


def element_importer(parent, identifier, title, data, children, vocabulary, treating_groups_titles):
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
    # csv_line = data.pop('_ln', 0)
    data.pop('_ln', 0)
    if len(existing_elements) >= 1:
        existing_element = parent[existing_elements[0].id]
        exist = True
    else:
        element["@type"] = portal_type
        element["internal_reference_no"] = identifier
    # if not exist:
    #     print(u"{}: '{}', '{}'".format(csv_line, identifier, title))

    if not existing_element or existing_element.title != title:
        element["title"] = title
        has_change = True

    key = "treating_groups"
    # we include treating_groups only if defined
    if data.get(key) and (not existing_element or getattr(existing_element, key) != data.get(key)):
        element[key] = data.get(key)
        has_change = True
    if data.get('treating_groups_title'):
        value = treating_groups_titles.get(data.get('treating_groups_title'))
        if value is None:
            sp = api.portal.get().portal_properties.site_properties
            raise Invalid(translate(u"Cannot find treating_groups title '${title}'",
                                    domain='collective.classification.folder',
                                    target_language=sp.getProperty('default_language', 'fr'),
                                    mapping={'title': data.get('treating_groups_title')}).encode('utf8'))
        elif not existing_element or getattr(existing_element, key) != value:
            element[key] = value
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

    key = "archived"
    if not existing_element or getattr(existing_element, key) != data.get(key, False):
        element[key] = data.get(key, False)
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
                treating_groups_titles,
            )
            elements.extend(element_importer(*args))
    return elements


def evaluate_internal_reference(context, request, number_name, expr_name, number=None):
    settings_iface = (
        "collective.classification.folder.browser.settings.IClassificationConfig.{0}"
    )
    if not number:
        number = api.portal.get_registry_record(
            settings_iface.format(number_name),
            default=1,
        )
    # we get the settings view
    try:
        portal_state = getMultiAdapter((context, request), name=u"plone_portal_state")
        settings_view = getMultiAdapter(
            (portal_state.portal(), request),
            name=u"collectiveclassificationfolder-settings",
        )
    except ComponentLookupError:
        return "Error getting view..."

    # we evaluate the expression
    expression = api.portal.get_registry_record(settings_iface.format(expr_name))
    value = settings_view.evaluate_tal_expression(
        expression,
        context,
        request,
        portal_state.portal(),
        number,
    )
    return value


def increment_internal_reference(number_name):
    settings_iface = (
        "collective.classification.folder.browser.settings.IClassificationConfig.{0}"
    )
    key = settings_iface.format(number_name)
    number = api.portal.get_registry_record(key, default=1)
    api.portal.set_registry_record(key, number + 1)
