# -*- coding: utf-8 -*-

from collective.classification.folder import _
from collective.classification.tree.vocabularies import iterable_to_vocabulary


def import_keys_vocabulary_factory(context):
    values = (
        (u"parent_identifier", _(u"Parent Identifier")),
        (u"classification_identifier", _(u"Identifier")),
        (u"title", _(u"Name")),
        (u"classification_categories", _(u"Classification categories")),
        (u"classification_informations", _(u"Informations")),
    )
    return iterable_to_vocabulary(values)
