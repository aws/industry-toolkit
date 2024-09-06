# ProcurementService API

The **ProcurementService** API allows you to generate content for a Request for Information (RFI). This content can be used to build an RFI PDF that includes the necessary organizational context, key requirements, and other essential details.

## API Overview

The ProcurementService API provides a single operation, `GenerateRFI`, which is designed to generate a Request for Information (RFI) based on input from the organization. The response contains all the necessary sections for the RFI, including the purpose, key requirements, and instructions for vendors on how to respond.

### Operation: `POST /GenerateRFI`

This operation generates content for a Request for Information (RFI). The user sends input details such as the purpose of the RFI, key requirements, and a brief summary of the organization's mission, and the service responds with a well-structured RFI that includes legal disclaimers, instructions, and clarifications.

## Input Schema

The input for the `GenerateRFI` operation consists of the following fields:

### `GenerateRFIInput`

- **RFIPurpose** (`string`, required):  
  The purpose of the RFI, providing context for what the organization is trying to procure.

- **KeyRequirements** (`string`, required):  
  A set of key requirements that the RFI should use to generate the response.

- **OrganizationalMission** (`string`, required):  
  A brief summary of the organization's mission, which will be reflected in the RFI.

## Output Schema

The output from the `GenerateRFI` operation consists of several fields that can be used to generate the RFI document:

### `GenerateRFIOutput`

- **OrganizationalMission** (`string`):  
  A description of the organization based on the `OrganizationalMission` input, with additional context where applicable.

- **Introduction** (`string`):  
  A summary of the purpose of the RFI, meant for the reader.

- **Disclaimer** (`string`):  
  Legal disclaimer text to be included in the RFI.

- **ResponseInstructions** (`string`):  
  Instructions for vendors on how to respond to the RFI.

- **Clarifications** (`string`):  
  Any clarifications vendors need to be aware of when responding to the RFI.

- **KeyRequirements** (`array` of `KeyRequirement`):  
  A human-readable list of key requirements, generated from the `KeyRequirements` input. Each key requirement includes the index, name, and value.

### `KeyRequirement`

Each key requirement has the following fields:

- **Index** (`integer`, required):  
  The index number of the requirement.

- **RequirementName** (`string`, required):  
  The name of the requirement.

- **RequirementValue** (`string`, required):  
  The value for the requirement.

## Example Request

```json
POST /GenerateRFI
{
  "RFIPurpose": "Procure IT consulting services for cloud migration.",
  "KeyRequirements": "1. Vendor must be AWS certified, 2. Experience with hybrid cloud solutions.",
  "OrganizationalMission": "Our mission is to modernize our IT infrastructure to improve efficiency and reduce costs."
}
