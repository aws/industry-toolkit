$version: "2"
namespace retail.reference.framework

use aws.protocols#restJson1

@restJson1
service ExampleService {
    version: "2024-01-01"
    resources: [
        ExampleResource
    ]
}

resource ExampleResource {
    identifiers: { exampleId: ExampleId }
    create: CreateExample
    read: GetExample
    update: UpdateExample
    delete: DeleteExample
}

@pattern("^[A-Za-z0-9]+$")
@documentation("The unique identifier for the example resource. This is a string field that only allows alphanumeric characters.")
string ExampleId

@http(code: 201, method: "POST", uri: "/examples")
@documentation("Creates a new example.")
operation CreateExample {
    input: CreateExampleRequest
    output: CreateExampleResponse
}

@input
@documentation("This is the input for the CreateExample operation.")
structure CreateExampleRequest for ExampleResource {

}

@output
@documentation("This is the output for the CreateExample operation.")
structure CreateExampleResponse for ExampleResource {

}

@http(code: 200, method: "GET", uri: "/examples/{exampleId}")
@documentation("Retrieves details for a specific example.")
@readonly
operation GetExample {
    input: GetExampleRequest
    output: GetExampleResponse
}

@input
@documentation("This is the input for the GetExample operation.")
structure GetExampleRequest for ExampleResource {
    @httpLabel
    @required
    @documentation("The unique identifier for the example. This is a string field that only allows alphanumeric characters.")
    $exampleId
}

@output
@documentation("This is the output for the GetExample operation.")
structure GetExampleResponse for ExampleResource {
    
}

@http(code: 200, method: "PATCH", uri: "/examples/{exampleId}")
@documentation("Updates an existing example record.")
@idempotent
operation UpdateExample {
    input: UpdateExampleRequest
    output: UpdateExampleResponse
}

@input
@documentation("This is the input for the UpdateExample operation.")
structure UpdateExampleRequest for ExampleResource {
    @httpLabel
    @required
    @documentation("The unique identifier for the customer. This is a string field that only allows alphanumeric characters.")
    $exampleId
}

@output
@documentation("This is the output for the UpdateExample operation.")
structure UpdateExampleResponse for ExampleResource {

}

@http(code: 204, method: "DELETE", uri: "/examples/{exampleId}")
@documentation("Deletes an example record.")
@idempotent
operation DeleteExample {
    input: DeleteExampleRequest
    output: DeleteExampleResponse
}

@input
@documentation("This is the input for the DeleteExample operation.")
structure DeleteExampleRequest for ExampleResource {
    @httpLabel
    @required
    @documentation("The unique identifier for the customer. This is a string field that only allows alphanumeric characters.")
    $exampleId
}

@output
@documentation("This is the output for the DeleteExample operation.")
structure DeleteExampleResponse for ExampleResource {

}