# -*- coding: utf-8 -*-

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.formwidget.autocomplete.interfaces import IAutocompleteWidget
from plone.formwidget.autocomplete.widget import AutocompleteMultiSelectionWidget
from plone.formwidget.autocomplete.widget import AutocompleteSearch
from z3c.form.interfaces import IFieldWidget
from z3c.form.widget import FieldWidget
from zope.interface import implementer


class IFolderAutocompleteWidget(IAutocompleteWidget):
    """Marker interface for the folder autocomplete widget"""


class FolderAutocompleteSearch(AutocompleteSearch):
    def __call__(self):

        # We want to check that the user was indeed allowed to access the
        # form for this widget. We can only this now, since security isn't
        # applied yet during traversal.
        self.validate_access()

        query = self.request.get("q", None)
        if not query:
            return ""

        # Update the widget before accessing the source.
        # The source was only bound without security applied
        # during traversal before.
        self.context.update()
        source = self.context.bound_source
        # TODO: use limit?

        if query:
            categories = (
                self.request.get("categories").split("|")
                if self.request.get("categories")
                else None
            )
            terms = set(source.search(query, categories_filter=categories))
        else:
            terms = set()

        return "\n".join(
            [
                "%s|%s" % (t.token, t.title or t.token)
                for t in sorted(terms, key=lambda t: t.title)
            ]
        )


@implementer(IFolderAutocompleteWidget)
class FolderAutocompleteMultiSelectionWidget(AutocompleteMultiSelectionWidget):

    js_template = """\
    (function($) {
        $().ready(function() {
            $('#%(id)s-input-fields').data('klass','%(klass)s').data('title','%(title)s').data('input_type','%(input_type)s').data('multiple', %(multiple)s);
            $('#%(id)s-buttons-search').remove();
            $('#%(id)s-widgets-query').autocomplete('%(url)s', {
                autoFill: %(autoFill)s,
                minChars: %(minChars)d,
                max: %(maxResults)d,
                mustMatch: %(mustMatch)s,
                matchContains: %(matchContains)s,
                formatItem: %(formatItem)s,
                formatResult: %(formatResult)s,
                parse: %(parseFunction)s,
                extraParams: {'categories':
                    function() {
                        return $("input[name='form.widgets.IClassificationFolder.classification_categories:list']")
                            .map(function() {
                                return this.value;
                            }).get().join("|");
                    }
                }
            }).result(%(js_callback)s);
            %(js_extra)s
        });
    })(jQuery);
    """

    display_template = ViewPageTemplateFile('templates/display.pt')


@implementer(IFieldWidget)
def FolderAutocompleteMultiFieldWidget(field, request):
    return FieldWidget(field, FolderAutocompleteMultiSelectionWidget(request))
