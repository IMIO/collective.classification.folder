# -*- coding: utf-8 -*-

from collective.classification.folder import _
from collective.classification.tree.vocabularies import iterable_to_vocabulary


def import_keys_vocabulary_factory(context):
    values = (
        # common
        (u"treating_groups_title", _(u"Treating groups title")),
        # _process_with_ref
        (u"parent_identifier", _(u"Parent Identifier")),
        (u"internal_reference_no", _(u"Identifier")),
        (u"classification_categories", _(u"Classification categories")),
        (u"title", _(u"Name")),
        (u"classification_informations", _(u"Informations")),
        (u"archived", _(u"Archived")),
        # _process_without_ref
        (u"folder_internal_reference_no", _(u"Folder identifier")),
        (u"subfolder_internal_reference_no", _(u"Subfolder identifier")),
        (u"folder_categories", _(u"Folder classification categories")),
        (u"subfolder_categories", _(u"Subfolder classification categories")),
        (u"folder_title", _(u"Folder Name")),
        (u"subfolder_title", _(u"Subfolder Name")),
        (u"folder_informations", _(u"Folder Informations")),
        (u"subfolder_informations", _(u"Subfolder Informations")),
        (u"folder_archived", _(u"Archived folder")),
        (u"subfolder_archived", _(u"Archived subfolder")),
    )
    return iterable_to_vocabulary(values)
