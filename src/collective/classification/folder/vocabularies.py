# -*- coding: utf-8 -*-

from collective.classification.folder import _
from collective.classification.tree.vocabularies import iterable_to_vocabulary


def import_keys_vocabulary_factory(context):
    values = (
        (u"parent_identifier", _(u"Parent Identifier")),
        (u"internal_reference_no", _(u"Identifier")),
        (u"classification_categories", _(u"Classification categories")),
        (u"title", _(u"Name")),
        (u"classification_informations", _(u"Informations")),
        (u"archived", _(u"Archived")),
        (u"folder_categories", _(u"Folder classification categories")),
        (u"subfolder_categories", _(u"Subfolder classification categories")),
        (u"title_folder", _(u"Folder Name")),
        (u"title_subfolder", _(u"Subfolder Name")),
        (u"archived_folder", _(u"Archived folder")),
        (u"archived_subfolder", _(u"Archived subfolder")),
    )
    return iterable_to_vocabulary(values)
