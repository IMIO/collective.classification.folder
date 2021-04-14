from Acquisition._Acquisition import aq_parent
from collective.classification.folder.content.classification_folder import IClassificationFolder
from plone.indexer.decorator import indexer


@indexer(IClassificationFolder)
def classification_folder_sort(folder):
    elements = []
    if folder.portal_type == "Classification Subfolder":
        elements.append(folder.title)
        folder = aq_parent(folder)
    elements.append(folder.title)
    folders = aq_parent(folder)
    elements.append(folders.title)

    elements.reverse()
    return u"|".join(elements)
