# -*- coding: utf-8 -*-

from collective.classification.folder.content.classification_folder import (
    IClassificationFolder,
)
from z3c.form.interfaces import IAddForm
from z3c.form.interfaces import IFormLayer
from z3c.form.interfaces import IValue
from z3c.form.interfaces import IWidget
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@adapter(IClassificationFolder, IFormLayer, IAddForm, Interface, IWidget)
@implementer(IValue)
class SubfolderDataProvider(object):
    def __init__(self, context, request, form, field, widget):
        self.context = context
        self.request = request
        self.form = form
        self.field = field
        self.widget = widget

    def get(self):
        inherit_fields = (
            "classification_categories",
            "service_in_charge",
            "services_in_copy",
        )
        if self.field.__name__ in inherit_fields:
            return getattr(self.context, self.field.__name__, None)
        else:
            return
