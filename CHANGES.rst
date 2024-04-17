Changelog
=========

1.1.3 (2024-04-17)
------------------

- Set maxRssults to 50 to enlarge folders selection behavior search results.
  [sgeulette]

1.1.2 (2024-04-12)
------------------

- Do not update folder children when modify event is ContainerModifiedEvent.
  [sgeulette]

1.1.1 (2024-02-26)
------------------

- Corrected `on_will_move` to avoid error on delete.
  [sgeulette]
- Removed `collective.z3cform.chosen` dependency.
  [sgeulette]
- Removed folder rename restriction (now well handled in iconifiedcategory).
  [sgeulette]
- Added INextPrevNotNavigable on folder classes (in zcml).
  [sgeulette]

1.1.0 (2024-02-19)
------------------

- Corrected tests.
  [sgeulette]
- Corrected bug in indexer when the stored folders cannot be seen by the current user.
  [sgeulette]
- Used imio.annex product so it is possible to add categorized annexe in folder and subfolder.
  [sgeulette]
- Added `yesno_value` index to store archived value and possibly use it in a faceted widget.
  [sgeulette]
- Added `state_filesize` column in `FolderFacetedTableView`.
  [sgeulette]
- Removed fixed created sorting on IClassificationFacetedNavigable.
  [sgeulette]
- Defined sort_index on subfolder column.
  [sgeulette]
- Avoided folder rename
  [sgeulette]

1.0.2 (2023-11-28)
------------------

- Added `collective.classification.folder.vocabularies:folder_portal_types` vocabulary to be used in faceted criteria.
  [sgeulette]
- Added separate ClassificationFolder title and ClassificationSubfolder title columns.
  [sgeulette]

1.0.1 (2023-09-08)
------------------

- Removed python_requires causing problem to download from pypi.
  [sgeulette]

1.0.0 (2023-09-07)
------------------

- Set really `classification_categories` field on folders as not mandatory
  [sgeulette]
- Set `treating_groups` field as required
  [sgeulette]

1.0a2 (2023-07-20)
------------------

- Set `classification_categories` field on folders as not required
  [sgeulette]

1.0a1 (2023-03-29)
------------------

- Initial release.
  [mpeeters, sgeulette]
- Replaced collective.z3cform.chosen widget by collective.z3cform.select2.
  Must remove "chosen" packages in next release.
  [sgeulette]
