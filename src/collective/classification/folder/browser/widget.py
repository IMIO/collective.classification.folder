# -*- coding: utf-8 -*-
from imio.helpers.content import uuidToObject
from imio.prettylink.adapters import PrettyLinkAdapter
from plone.app.z3cform.widgets.select import AjaxSelectWidget
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.interfaces import DISPLAY_MODE
from z3c.form.interfaces import IFieldWidget
from z3c.form.widget import FieldWidget
from zope.interface import implementer


class SourceAjaxSelectWidget(AjaxSelectWidget):
    """Select2 widget on a source, showing term titles (not tokens) as values"""

    def get_vocabulary(self):
        # plone.app.z3cform only looks up named vocabularies
        if getattr(self, "_source", None) is None:
            self._source = self.field.bind(self.context).value_type.vocabulary
        return self._source

    def get_pattern_options(self):
        options = super(SourceAjaxSelectWidget, self).get_pattern_options()
        if self.value:
            vocabulary = self.get_vocabulary()
            options["initialValues"] = {}
            for token in self.value.split(self.separator):
                try:
                    options["initialValues"][token] = vocabulary.getTermByToken(token).title
                except LookupError:
                    options["initialValues"][token] = token
        return options


class FolderAjaxSelectWidget(SourceAjaxSelectWidget):
    """Folders select2 widget, displaying pretty links"""

    display_template = ViewPageTemplateFile("templates/display.pt")

    def render(self):
        if self.mode == DISPLAY_MODE:
            return self.display_template(self)
        return super(FolderAjaxSelectWidget, self).render()

    def pl_items(self):
        """Inspired from z3c.form.widget displayValue method"""
        items = []
        for token in (self.value or "").split(self.separator):
            if not token:
                continue
            folder = uuidToObject(token, unrestricted=True)
            if not folder:
                items.append(token)
                continue
            adapted = PrettyLinkAdapter(
                folder, showLockedIcon=False, target="_blank", showIcons=True, showContentIcon=True
            )
            if folder.portal_type == "ClassificationSubfolder":
                cf_adapted = PrettyLinkAdapter(
                    folder.cf_parent(), showLockedIcon=False, target="_blank", showIcons=True, showContentIcon=True
                )
                items.append(cf_adapted.getLink() + adapted.getLink())
            else:
                items.append(adapted.getLink())
        return items


@implementer(IFieldWidget)
def SourceAjaxSelectFieldWidget(field, request):
    return FieldWidget(field, SourceAjaxSelectWidget(request))


@implementer(IFieldWidget)
def FolderAjaxSelectFieldWidget(field, request):
    return FieldWidget(field, FolderAjaxSelectWidget(request))
