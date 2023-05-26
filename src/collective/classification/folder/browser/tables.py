# -*- coding: utf-8 -*-

from collective.eeafaceted.z3ctable.columns import PrettyLinkColumn
from collective.eeafaceted.z3ctable.browser.views import FacetedTableView
from collective.eeafaceted.z3ctable.interfaces import IFacetedTable
from zope.interface import implementer


class ISubfolderFacetedTable(IFacetedTable):
    pass


@implementer(ISubfolderFacetedTable)
class SubFoldersFacetedTableView(FacetedTableView):
    ignoreColumnWeight = True

    def _getViewFields(self):
        """Returns fields we want to show in the table."""
        return [
            u"pretty_link",
            u"internal_reference_no",
            u"classification_tree_identifiers",
            u"classification_treating_group",
        ]


class SubfolderTitleColumn(PrettyLinkColumn):

    params = {
        "showIcons": True,
        "showContentIcon": True,
        "display_tag_title": False,
    }
