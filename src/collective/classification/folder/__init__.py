# -*- coding: utf-8 -*-
"""Init and utils."""
from plone import api
from zope.i18n import translate
from zope.i18nmessageid import MessageFactory


_ = MessageFactory("collective.classification.folder")


def _tr(msgid, domain="collective.classification.folder", mapping=None):
    # zope.i18n.translate falls back to the msgid when the domain has no catalog
    return translate(msgid, domain=domain, mapping=mapping, target_language=api.portal.get_current_language())
