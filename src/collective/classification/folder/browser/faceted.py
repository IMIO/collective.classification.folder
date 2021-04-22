from collective.eeafaceted.z3ctable.browser.views import FacetedTableView
from collective.eeafaceted.z3ctable.columns import PrettyLinkColumn
from eea.facetednavigation.criteria.handler import Criteria as eeaCriteria
from eea.facetednavigation.interfaces import IFacetedNavigable
from eea.facetednavigation.widgets.storage import Criterion
from persistent.list import PersistentList
from plone import api


class IClassificationFacetedNavigable(IFacetedNavigable):
    """
    More specific IFacetedNavigable to be able to override
    ICriteria adapter only for specific content
    """


class Criteria(eeaCriteria):
    """ Handle criteria
    """

    def __init__(self, context):
        """ Handle criteria
        """
        original_context_uid = api.content.get_uuid(context)
        super(Criteria, self).__init__(context)

        portal = api.portal.get()
        self.context = portal["classification_folder_faceted_configuration"]
        self.criteria = PersistentList()

        for crit in self._criteria():
            if crit.index != u"classification_folders" or crit.widget != u"sorting":
                self.criteria.append(crit)

        select_criterion = Criterion(**{
            '_cid_': u'restrictfolder',
            "widget": u'select',
            "title": u'Classification folder',
            "index": u'classification_folders',
            "vocabulary": u'',
            "catalog": u'portal_catalog',
            "hidealloption": u'False',
            "position": u'right',
            "section": u'default',
            "hidden": u'True',
            "custom_css": u'',
            "count": u'False',
            "sortcountable": u'False',
            "hidezerocount": u'False',
            "sortreversed": u'False',
            "default": original_context_uid,
        })
        self.criteria.append(select_criterion)

        sort_criterion = Criterion(**{
            "_cid_": u"sorton",
            "title": u"Sort on",
            "position": u"top",
            "section": u"default",
            "hidden": u"True",
            "default": u"created(reverse)",
            "widget": u"sorting",
        })
        self.criteria.append(sort_criterion)


class FoldersFacetedTableView(FacetedTableView):
    def _getViewFields(self):
        """Returns fields we want to show in the table."""

        return [
            u"pretty_link",
            u"ModificationDate",
            u"CreationDate",
        ]


class FolderFacetedTableView(FacetedTableView):
    def _getViewFields(self):
        """Returns fields we want to show in the table."""

        return [
            u"pretty_link",
            u"ModificationDate",
            u"CreationDate",
        ]


class FolderTitleColumn(PrettyLinkColumn):

    params = {
        "showIcons": True,
        "showContentIcon": True,
        "display_tag_title": False,
    }
