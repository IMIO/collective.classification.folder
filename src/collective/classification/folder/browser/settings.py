# -*- coding: utf-8 -*-

from collective.classification.folder import _
from DateTime import DateTime
from plone.app.registry.browser import controlpanel
from plone.supermodel import model
from Products.CMFCore.Expression import Expression
from Products.PageTemplates.Expressions import getEngine
from zope import schema


class IClassificationConfig(model.Schema):

    folder_number = schema.Int(
        title=_(u"Number of next folder"),
        description=_(
            u"This value is used as 'number' variable in linked tal expression"
        ),
    )

    folder_talexpression = schema.TextLine(
        title=_(u"Folder internal reference default value expression"),
        description=_(
            u"Tal expression where you can use portal, number, context, request, "
            "date as variable"
        ),
    )

    subfolder_number = schema.Int(
        title=_(u"Number of next subfolder"),
        description=_(
            u"This value is used as 'number' variable in linked tal expression"
        ),
    )

    subfolder_talexpression = schema.TextLine(
        title=_(u"Subfolder internal reference default value expression"),
        description=_(
            u"Tal expression where you can use portal, number, context, request, "
            "date as variable"
        ),
    )


class SettingsEditForm(controlpanel.RegistryEditForm):
    """
    Define form logic
    """

    schema = IClassificationConfig
    label = _(u"Classification Config")


class SettingsView(controlpanel.ControlPanelFormWrapper):
    form = SettingsEditForm

    def evaluate_tal_expression(
        self, expression, context, request, portal, number, **kwargs
    ):
        """evaluate the expression, considering portal and number in context"""
        data = {
            "tool": self,
            "number": str(number),
            "context": context,
            "request": request,
            "portal": portal,
            "date": DateTime(),
        }
        data.update(kwargs)
        res = ""
        try:
            ctx = getEngine().getContext(data)
            res = Expression(expression)(ctx)
        except Exception as msg:
            return "Error in expression: %s" % msg
        return res
