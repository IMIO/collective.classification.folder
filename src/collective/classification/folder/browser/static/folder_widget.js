/* The classification folders search is filtered by the selected classification categories */
document.addEventListener("DOMContentLoaded", function () {
  var $ = window.jQuery;
  if (!$) {
    return;
  }
  $.ajaxPrefilter(function (options) {
    if (!options.url || options.url.indexOf(".classification_folders/@@getSource") === -1) {
      return;
    }
    var categories = $("input[name='form.widgets.IClassificationFolder.classification_categories']").val();
    if (categories) {
      options.url += (options.url.indexOf("?") === -1 ? "?" : "&") + "categories=" + encodeURIComponent(categories);
    }
  });
});
