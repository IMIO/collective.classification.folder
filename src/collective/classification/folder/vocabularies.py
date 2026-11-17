# -*- coding: utf-8 -*-

from collective.classification.folder import _
from collective.classification.tree.vocabularies import iterable_to_vocabulary


def import_keys_vocabulary_factory(context):
    values = (
        # common
        ("treating_groups_title", _("Treating groups title")),
        # _process_with_ref
        ("parent_identifier", _("Parent Identifier")),
        ("internal_reference_no", _("Identifier")),
        ("classification_categories", _("Classification categories")),
        ("title", _("Name")),
        ("classification_informations", _("Informations")),
        ("archived", _("Archived")),
        # _process_without_ref
        ("folder_internal_reference_no", _("Folder identifier")),
        ("subfolder_internal_reference_no", _("Subfolder identifier")),
        ("folder_categories", _("Folder classification categories")),
        ("subfolder_categories", _("Subfolder classification categories")),
        ("folder_title", _("Folder Name")),
        ("subfolder_title", _("Subfolder Name")),
        ("folder_informations", _("Folder Informations")),
        ("subfolder_informations", _("Subfolder Informations")),
        ("folder_archived", _("Archived folder")),
        ("subfolder_archived", _("Archived subfolder")),
    )
    return iterable_to_vocabulary(values)
