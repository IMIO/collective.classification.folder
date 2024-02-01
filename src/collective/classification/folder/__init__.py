# -*- coding: utf-8 -*-
"""Init and utils."""
from plone import api
from zope.component import queryUtility
from zope.i18n import ITranslationDomain
from zope.i18nmessageid import MessageFactory


_ = MessageFactory("collective.classification.folder")

def _tr(msgid, domain='collective.classification.folder', mapping=None):
    translation_domain = queryUtility(ITranslationDomain, domain)
    return translation_domain.translate(msgid, target_language=api.portal.get_current_language(),
                                        mapping=mapping)
