*** Settings ***
Documentation  The classification folders and subfolders: add forms and views.
Resource  classification_folder.robot
Test Setup  Open the site as a manager
Test Teardown  Close the browser


*** Test Cases ***
Add a classification folder
    A folders container
    Go to  ${PLONE_URL}/folders/++add++ClassificationFolder
    The default reference is  F0001
    Fill the folder form  Budget  Yearly budget
    Save the add form
    The page title is  Budget
    Location should contain  ${PLONE_URL}/folders/budget
    The folder shows the field  Classification identifier  F0001
    The folder shows the field  Service in charge  Reviewers
    The folder shows the field  Classification informations  Yearly budget
    The folder shows the field  Archived  No

Add a subfolder
    ${container_uid}=  A folders container
    A classification folder  ${container_uid}  budget  Budget  F0001
    Go to  ${PLONE_URL}/folders/budget/++add++ClassificationSubfolder
    The default reference is  F0001-xx
    Input text  css=#form-widgets-internal_reference_no  F0001-01
    Input text  css=#form-widgets-title  Budget 2024
    Save the add form
    The page title is  Budget 2024
    The folder shows the field  Service in charge  Reviewers
    Go to  ${PLONE_URL}/folders/budget
    Open the subfolders
    Element should contain  css=#classification_subfolders  F0001-01
    Click link  Budget 2024
    Location should contain  ${PLONE_URL}/folders/budget/budget-2024

View a folder with its classified content
    ${container_uid}=  A folders container
    ${folder_uid}=  A classification folder  ${container_uid}  budget  Budget  F0001
    ${mail_uid}=  Create content  type=testingtype  id=mail  title=Incoming mail
    Set field value  ${mail_uid}  classification_folders  ['${folder_uid}']  list
    Go to  ${PLONE_URL}/folders/budget
    The table shows  Incoming mail
    The table links to  Incoming mail  ${PLONE_URL}/mail
