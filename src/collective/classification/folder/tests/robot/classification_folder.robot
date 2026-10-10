*** Settings ***
Documentation  collective.classification.folder keywords, built on the ui_plone${PLONE_MAJOR}.robot keywords.
...            Robot Framework 3.0 syntax (shared with the Plone 4.3 environment).
Resource  ui_plone${PLONE_MAJOR}.robot


*** Keywords ***
Open the site as a manager
    Open test browser
    Enable autologin as  Manager

Close the browser
    Run keyword if test failed  Capture page screenshot
    Close all browsers

A folders container
    [Documentation]  Created with the add form (created by the remote library, the faceted setup redirects
    ...              the remote call), returns its uid
    Go to  ${PLONE_URL}/++add++ClassificationFolders
    Input text  css=#form-widgets-title  Folders
    Click button  css=#form-buttons-save
    The status message contains  Item created
    The faceted results are loaded
    ${uid}=  Path to uid  /plone/folders
    [Return]  ${uid}

The faceted results are loaded
    [Documentation]  The page is locked by an overlay while the faceted navigation loads the results
    Wait until element is not visible  css=.faceted-lock-overlay

A classification folder
    [Documentation]  Created by the remote library in the container, in charge of the Reviewers, returns its uid
    [Arguments]  ${container_uid}  ${id}  ${title}  ${reference}
    ${uid}=  Create content  type=ClassificationFolder  container=${container_uid}  id=${id}  title=${title}
    ...  internal_reference_no=${reference}
    Set field value  ${uid}  treating_groups  Reviewers  string
    [Return]  ${uid}

A category
    [Documentation]  Added in a new classification tree with its add form
    [Arguments]  ${identifier}  ${title}
    Create content  type=ClassificationContainer  id=tree  title=Tree
    Go to  ${PLONE_URL}/tree/add-ClassificationCategory
    Input text  css=#form-widgets-identifier  ${identifier}
    Input text  css=#form-widgets-title  ${title}
    Click button  css=#form-buttons-add
    The status message contains  Category added

The page title is
    [Arguments]  ${title}
    Element text should be  ${PAGE_TITLE}  ${title}

The default reference is
    [Documentation]  Value proposed by the add form
    [Arguments]  ${reference}
    Textfield value should be  css=#form-widgets-internal_reference_no  ${reference}

Fill the folder form
    [Arguments]  ${title}  ${informations}=${EMPTY}
    Input text  css=#form-widgets-title  ${title}
    Select from list by value  css=#form-widgets-treating_groups  Reviewers
    Input text  css=#form-widgets-classification_informations  ${informations}

Save the add form
    Click button  css=#form-buttons-save
    The status message contains  Item created

The folder shows the field
    [Documentation]  Line of the fields table of the folder view, loaded by the faceted navigation
    [Arguments]  ${label}  ${value}
    Wait until page contains element
    ...  xpath=//td[label="${label}"]/following-sibling::td[contains(normalize-space(.), "${value}")]

The table shows
    [Documentation]  Results table of the faceted navigation (after the subfolders table in a folder view)
    [Arguments]  ${text}
    Wait until element contains  xpath=(//table[@id="faceted_table"])[last()]  ${text}

The table does not show
    [Documentation]  Call it after a check that the table is loaded
    [Arguments]  ${text}
    Wait until keyword succeeds  10s  1s
    ...  Element should not contain  xpath=(//table[@id="faceted_table"])[last()]  ${text}

The table links to
    [Documentation]  The links of the folders open a new window
    [Arguments]  ${title}  ${url}
    ${link}=  Set variable  xpath=(//table[@id="faceted_table"])[last()]//a[normalize-space(.)="${title}"]
    Element attribute value should be  ${link}  href  ${url}
    Element attribute value should be  ${link}  target  _blank

Search the folders
    [Documentation]  Text criterion of the folders container
    [Arguments]  ${text}
    Input text  css=#c1  ${text}
    Click element  css=#c1_button

Open the subfolders
    [Documentation]  Collapsible block of the folder view
    Wait until page contains element  css=#container-collapsible .collapsibleHeader
    Click element  css=#container-collapsible .collapsibleHeader
    Wait until element is visible  css=#classification_subfolders
