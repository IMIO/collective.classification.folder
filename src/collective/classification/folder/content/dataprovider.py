# -*- coding: utf-8 -*-

from collective.classification.folder import utils
from collective.classification.folder.content.classification_folder import (
    IClassificationFolder,
)
from collective.classification.folder.content.classification_folders import (
    IClassificationFolders,
)
from z3c.form.interfaces import IAddForm
from z3c.form.interfaces import IFormLayer
from z3c.form.interfaces import IValue
from z3c.form.interfaces import IWidget
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


class BaseDataProvider(object):
    def __init__(self, context, request, form, field, widget):
        self.context = context
        self.request = request
        self.form = form
        self.field = field
        self.widget = widget


@adapter(IClassificationFolders, IFormLayer, IAddForm, Interface, IWidget)
@implementer(IValue)
class FolderDataProvider(BaseDataProvider):
    def get(self):
        if self.field.__name__ == "internal_reference_no":
            return utils.evaluate_internal_reference(
                self.context,
                self.request,
                "folder_number",
                "folder_talexpression",
            ).decode("utf8")
        else:
            return


@adapter(IClassificationFolder, IFormLayer, IAddForm, Interface, IWidget)
@implementer(IValue)
class SubfolderDataProvider(BaseDataProvider):
    def get(self):
        inherit_fields = (
            "classification_categories",
            "treating_groups",
            "recipient_groups",
        )
        if self.field.__name__ in inherit_fields:
            return getattr(self.context, self.field.__name__, None)
        elif self.field.__name__ == "internal_reference_no":
            return utils.evaluate_internal_reference(
                self.context,
                self.request,
                "subfolder_number",
                "subfolder_talexpression",
            ).decode("utf8")
        else:
            return
