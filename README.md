[comment]: # "Auto-generated SOAR connector documentation"
# PhishLabs

Publisher: Splunk  
Connector Version: 2\.0\.4  
Product Vendor: PhishLabs  
Product Name: PhishLabs  
Product Version Supported (regex): "\.\*"  
Minimum Product Version: 5\.1\.0  

This app implements investigative actions on the PhishLabs Casetracker Portal

### Configuration Variables
The below configuration variables are required for this Connector to operate.  These variables are specified when configuring a PhishLabs asset in SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**username** |  required  | string | Username
**password** |  required  | password | Password

### Supported Actions  
[test connectivity](#action-test-connectivity) - Validate the asset configuration for connectivity using supplied configuration  
[get ticket](#action-get-ticket) - Get case \(issue\) information  
[create ticket](#action-create-ticket) - Create a new case submission  
[list tickets](#action-list-tickets) - Get a list of cases in PhishLabs  
[get config](#action-get-config) - Return the list of brands and case types currently configured in PhishLabs  

## action: 'test connectivity'
Validate the asset configuration for connectivity using supplied configuration

Type: **test**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
No Output  

## action: 'get ticket'
Get case \(issue\) information

Type: **generic**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**case\_id** |  required  | Case Id | string |  `phishlabs case id` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.case\_id | string |  `phishlabs case id` 
action\_result\.data\.\*\.brand | string |  `phishlabs brand` 
action\_result\.data\.\*\.caseId | string |  `phishlabs case id` 
action\_result\.data\.\*\.caseNumber | numeric | 
action\_result\.data\.\*\.caseStatus | string | 
action\_result\.data\.\*\.caseType | string |  `phishlabs case type` 
action\_result\.data\.\*\.createdBy\.id | string | 
action\_result\.data\.\*\.createdBy\.name | string | 
action\_result\.data\.\*\.customer | string | 
action\_result\.data\.\*\.dateClosed | string | 
action\_result\.data\.\*\.dateCreated | string | 
action\_result\.data\.\*\.dateModified | string | 
action\_result\.data\.\*\.description | string | 
action\_result\.data\.\*\.formReceiver | boolean | 
action\_result\.data\.\*\.header\.id | string | 
action\_result\.data\.\*\.header\.queryParams\.format | string | 
action\_result\.data\.\*\.header\.requestDate | string | 
action\_result\.data\.\*\.header\.returnResult | numeric | 
action\_result\.data\.\*\.header\.totalResult | numeric | 
action\_result\.data\.\*\.header\.user | string | 
action\_result\.data\.\*\.notes\.\*\.author | string | 
action\_result\.data\.\*\.notes\.\*\.dateCreated | string | 
action\_result\.data\.\*\.notes\.\*\.dateModified | string | 
action\_result\.data\.\*\.notes\.\*\.note | string | 
action\_result\.data\.\*\.resolutionStatus | string | 
action\_result\.data\.\*\.title | string | 
action\_result\.summary\.case\_id | string |  `phishlabs case id` 
action\_result\.summary\.return\_result | numeric | 
action\_result\.summary\.total\_result | numeric | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric | 
action\_result\.data\.\*\.appDate | string | 
action\_result\.data\.\*\.createdBy\.displayName | string | 
action\_result\.data\.\*\.createdBy\.organization | string | 
action\_result\.data\.\*\.sourceName | string | 
action\_result\.data\.\*\.brandAbuseFlag | boolean | 
action\_result\.data\.\*\.sourcePhishlabs | boolean | 
action\_result\.data\.\*\.primaryMarketplace | boolean | 
action\_result\.data\.\*\.crimewareLoadFailure | boolean | 
action\_result\.data\.\*\.resolution | string |   

## action: 'create ticket'
Create a new case submission

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**title** |  required  | Title | string | 
**url** |  optional  | URL | string |  `url` 
**description** |  optional  | Description of the case | string | 
**case\_type** |  required  | Type of case | string |  `phishlabs case type` 
**brand** |  required  | Brand for the case | string |  `phishlabs brand` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.brand | string |  `phishlabs brand` 
action\_result\.parameter\.case\_type | string |  `phishlabs case type` 
action\_result\.parameter\.description | string | 
action\_result\.parameter\.title | string | 
action\_result\.parameter\.url | string |  `url` 
action\_result\.data\.\*\.createdCase\.caseId | string |  `phishlabs case id` 
action\_result\.data\.\*\.createdCase\.caseNumber | numeric | 
action\_result\.data\.\*\.createdCase\.status | string | 
action\_result\.summary\.case\_id | string |  `phishlabs case id` 
action\_result\.summary\.case\_number | numeric | 
action\_result\.summary\.status | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric | 
action\_result\.data\.\*\.updatedCase\.caseId | string | 
action\_result\.data\.\*\.updatedCase\.status | string | 
action\_result\.data\.\*\.updatedCase\.caseNumber | numeric |   

## action: 'list tickets'
Get a list of cases in PhishLabs

Type: **generic**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.data\.\*\.brand | string |  `phishlabs brand` 
action\_result\.data\.\*\.caseId | string |  `phishlabs case id` 
action\_result\.data\.\*\.caseNumber | numeric | 
action\_result\.data\.\*\.caseStatus | string | 
action\_result\.data\.\*\.caseType | string |  `phishlabs case type` 
action\_result\.data\.\*\.createdBy\.id | string | 
action\_result\.data\.\*\.createdBy\.name | string | 
action\_result\.data\.\*\.customer | string | 
action\_result\.data\.\*\.dateClosed | string | 
action\_result\.data\.\*\.dateCreated | string | 
action\_result\.data\.\*\.dateModified | string | 
action\_result\.data\.\*\.description | string | 
action\_result\.data\.\*\.formReceiver | boolean | 
action\_result\.data\.\*\.header\.id | string | 
action\_result\.data\.\*\.header\.queryParams\.format | string | 
action\_result\.data\.\*\.header\.requestDate | string | 
action\_result\.data\.\*\.header\.returnResult | numeric | 
action\_result\.data\.\*\.header\.totalResult | numeric | 
action\_result\.data\.\*\.header\.user | string | 
action\_result\.data\.\*\.notes\.\*\.author | string | 
action\_result\.data\.\*\.notes\.\*\.dateCreated | string | 
action\_result\.data\.\*\.notes\.\*\.dateModified | string | 
action\_result\.data\.\*\.notes\.\*\.note | string | 
action\_result\.data\.\*\.resolutionStatus | string | 
action\_result\.data\.\*\.title | string | 
action\_result\.summary\.total\_cases | numeric | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric | 
action\_result\.data\.\*\.appDate | string | 
action\_result\.data\.\*\.createdBy\.displayName | string | 
action\_result\.data\.\*\.createdBy\.organization | string | 
action\_result\.data\.\*\.sourceName | string | 
action\_result\.data\.\*\.brandAbuseFlag | boolean | 
action\_result\.data\.\*\.sourcePhishlabs | boolean | 
action\_result\.data\.\*\.primaryMarketplace | boolean | 
action\_result\.data\.\*\.crimewareLoadFailure | boolean | 
action\_result\.data\.\*\.attachments\.\*\.id | string | 
action\_result\.data\.\*\.attachments\.\*\.type | string | 
action\_result\.data\.\*\.attachments\.\*\.fileURL | string | 
action\_result\.data\.\*\.attachments\.\*\.fileName | string | 
action\_result\.data\.\*\.attachments\.\*\.dateAdded | string | 
action\_result\.data\.\*\.attachments\.\*\.description | string | 
action\_result\.data\.\*\.resolution | string | 
action\_result\.data\.\*\.caseLinks\.\*\.title | string | 
action\_result\.data\.\*\.caseLinks\.\*\.caseId | string | 
action\_result\.data\.\*\.caseLinks\.\*\.caseType | string | 
action\_result\.data\.\*\.caseLinks\.\*\.linkType | string | 
action\_result\.data\.\*\.caseLinks\.\*\.caseNumber | numeric | 
action\_result\.data\.\*\.caseLinks\.\*\.caseStatus | string | 
action\_result\.data\.\*\.caseLinks\.\*\.linkCreated | string |   

## action: 'get config'
Return the list of brands and case types currently configured in PhishLabs

Type: **investigate**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.data\.\*\.brands\.\*\.name | string |  `phishlabs brand` 
action\_result\.data\.\*\.case\_types\.\*\.name | string |  `phishlabs case type` 
action\_result\.summary\.num\_brands | numeric | 
action\_result\.summary\.num\_case\_types | numeric | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric | 