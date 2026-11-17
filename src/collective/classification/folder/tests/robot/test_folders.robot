*** Settings ***
Documentation  The folders container: creation and faceted table of its folders.
Resource  classification_folder.robot
Test Setup  Open the site as a manager
Test Teardown  Close the browser


*** Test Cases ***
Create a folders container
    Go to  ${PLONE_URL}/++add++ClassificationFolders
    Input text  css=#form-widgets-title  My folders
    Click button  css=#form-buttons-save
    The status message contains  Item created
    The page title is  My folders
    Location should contain  ${PLONE_URL}/my-folders
    Page should contain element  css=#faceted-form

The container lists its folders
    ${container_uid}=  A folders container
    ${budget_uid}=  A classification folder  ${container_uid}  budget  Budget  F0001
    A classification folder  ${container_uid}  staff  Staff  F0002
    Create content  type=ClassificationSubfolder  container=${budget_uid}  id=budget-2024  title=Budget 2024
    ...  internal_reference_no=F0001-01
    Go to  ${PLONE_URL}/folders
    The table shows  Budget ⏩ Budget 2024
    The table shows  F0002
    The table shows  Reviewers
    Search the folders  Staff
    The table shows  Staff
    The table does not show  Budget
    The table links to  Staff  ${PLONE_URL}/folders/staff
