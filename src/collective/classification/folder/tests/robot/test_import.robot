*** Settings ***
Documentation  Import of the folders from a CSV file, in 2 steps.
Resource  classification_folder.robot
Test Setup  Open the site as a manager
Test Teardown  Close the browser


*** Test Cases ***
Import a CSV file in 2 steps
    A category  001  Administration
    A folders container
    Click the content action  classification\\.import
    Choose file  css=#form-widgets-source-input  ${CURDIR}/folders.csv
    Select from list by value  css=#form-widgets-separator  ;
    Click button  css=#form-buttons-continue
    Page should contain  Sample data : 'Budget', 'Budget'
    Select from list by value  css=#form-widgets-column_0  folder_title
    Select from list by value  css=#form-widgets-column_1  subfolder_title
    Select from list by value  css=#form-widgets-column_2  folder_categories
    Select from list by value  css=#form-widgets-treating_groups  Reviewers
    Click button  css=#form-buttons-import
    Page should contain element  css=#progress
    # the page goes back to the container when the import is finished
    Wait until keyword succeeds  20s  1s  The page title is  Folders
    The table shows  Budget ⏩ Budget 2024
    The table shows  Staff
    The table shows  F0002
