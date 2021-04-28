from collective.classification.folder.behaviors.classification_folder import IClassificationFolder
from collective.classification.folder.content.vocabularies import ClassificationFolderGroups


class LocalRoleAdapter(object):

    def __init__(self, context):
        self.context = context
        self.all_reading_groups = set([])
        self.all_editor_groups = set([])

        all_folder_groups = ClassificationFolderGroups()
        adapted_context = IClassificationFolder(self.context, None)
        context_folders = getattr(adapted_context, "classification_folders", []) or []

        for folder_uid in context_folders:
            reading_groups = all_folder_groups.reader_groups.get(folder_uid, [])
            self.all_reading_groups.update(reading_groups)
            editor_groups = all_folder_groups.editor_groups.get(folder_uid, [])
            self.all_editor_groups.update(editor_groups)

    def getRoles(self, principal_id):
        all_roles = []
        if principal_id in self.all_reading_groups:
            all_roles.append("Reader")
        if principal_id in self.all_editor_groups:
            all_roles.append("Editor")

        return all_roles

    def getAllRoles(self):
        all_roles = []
        for group in self.all_reading_groups.union(self.all_editor_groups):
            group_roles = []
            if group in self.all_reading_groups:
                group_roles.append("Reader")
            if group in self.all_editor_groups:
                group_roles.append("Editor")
            if group_roles:
                all_roles.append((group, group_roles))

        return all_roles
