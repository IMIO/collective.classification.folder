*** Settings ***
Documentation  The control panel of the default references.
Resource  classification_folder.robot
Test Setup  Open the site as a manager
Test Teardown  Close the browser


*** Test Cases ***
Change the settings in the control panel
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click the configlet  @@collectiveclassificationfolder-settings
    Location should contain  ${PLONE_URL}/@@collectiveclassificationfolder-settings
    Input text  css=#form-widgets-folder_number  12
    Input text  css=#form-widgets-folder_talexpression  python:'D-%s' % number
    Click button  css=#form-buttons-save
    The status message contains  Changes saved
    A folders container
    Go to  ${PLONE_URL}/folders/++add++ClassificationFolder
    The default reference is  D-12
