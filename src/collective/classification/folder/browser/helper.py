# -*- coding: utf-8 -*-

from collective.classification.tree.browser import helper
from zope.interface import implementer


@implementer(helper.IClassificationHelper)
class ClassificationHelper(helper.ClassificationPublicHelper):
    def can_import(self):
        return True
