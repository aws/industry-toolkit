# Search Service API
Defines the SearchService which supports operations related to search indices and queries within the retail industry.


## Version: 2024-01-01

### /indexes/{indexId}/queries

#### POST
##### Summary:

Create a new query within an index and retrieve the initial set of results.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| indexId | path | Represents a unique identifier for an index. | Yes | string |

##### Responses

| Code | Description |
| ---- | ----------- |
| 201 | The created query and initial set of results. |
