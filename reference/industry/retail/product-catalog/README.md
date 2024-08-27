# Product Service API
The Product Service API provides access to product and category data within a retail system. It includes operations for managing products, product variants, and categories.


## Version: 2024-01-01

### /products

#### GET
##### Summary:

Lists the available products in the catalog.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| nextToken | query | Specifies the beginning of the next page of results. | No | string |
| pageSize | query | The maximum number of results to return at once. | No | integer |
| nameFilter | query | Filters products by name. | No | string |
| categoryFilter | query | Filters products by category. | No | string (uuid) |

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | A list of products. |

#### POST
##### Summary:

Creates a new product in the catalog.

##### Responses

| Code | Description |
| ---- | ----------- |
| 201 | The created product. |

### /products/{productId}

#### GET
##### Summary:

Retrieves details for a specific product in the catalog.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| productId | path | The unique identifier for the product being requested. | Yes | string (uuid) |

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | Product details. |

#### PATCH
##### Summary:

Updates an existing product in the catalog.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| productId | path | The unique identifier for the product being updated. | Yes | string (uuid) |

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | The updated product. |

#### DELETE
##### Summary:

Deletes a product from the catalog.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| productId | path | The unique identifier for the product being deleted. | Yes | string (uuid) |

##### Responses

| Code | Description |
| ---- | ----------- |
| 204 | Product deleted successfully. |

### /products/{productId}/variants

#### GET
##### Summary:

Lists all variants for a specific product.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| productId | path | The unique identifier for the product being requested. | Yes | string (uuid) |
| nextToken | query | Specifies the beginning of the next page of results. | No | string |
| pageSize | query | The maximum number of results to return at once. | No | integer |

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | A list of product variants. |

#### POST
##### Summary:

Creates a new product variant for a specific product.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| productId | path | The unique identifier for the product for which a variant is being created. | Yes | string (uuid) |

##### Responses

| Code | Description |
| ---- | ----------- |
| 201 | The created product variant. |

### /products/{productId}/variants/{variantId}

#### GET
##### Summary:

Retrieves details for a specific product variant.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| productId | path | The unique identifier for the product. | Yes | string (uuid) |
| variantId | path | The unique identifier for the product variant. | Yes | string (uuid) |

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | Product variant details. |

#### PATCH
##### Summary:

Updates an existing product variant.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| productId | path | The unique identifier for the product. | Yes | string (uuid) |
| variantId | path | The unique identifier for the product variant. | Yes | string (uuid) |

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | The updated product variant. |

#### DELETE
##### Summary:

Deletes a product variant.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| productId | path | The unique identifier for the product. | Yes | string (uuid) |
| variantId | path | The unique identifier for the product variant. | Yes | string (uuid) |

##### Responses

| Code | Description |
| ---- | ----------- |
| 204 | Product variant deleted successfully. |

### /categories

#### GET
##### Summary:

Lists all categories.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| nextToken | query | Specifies the beginning of the next page of results. | No | string |
| pageSize | query | The maximum number of results to return at once. | No | integer |
| nameFilter | query | Filters categories by name. | No | string |

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | A list of categories. |

#### POST
##### Summary:

Creates a new category.

##### Responses

| Code | Description |
| ---- | ----------- |
| 201 | The created category. |

### /categories/{categoryId}

#### GET
##### Summary:

Retrieves details for a specific category.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| categoryId | path | The unique identifier for the category being requested. | Yes | string (uuid) |

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | Category details. |

#### PATCH
##### Summary:

Updates an existing category.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| categoryId | path | The unique identifier for the category being updated. | Yes | string (uuid) |

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | The updated category. |

#### DELETE
##### Summary:

Deletes a category.

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| categoryId | path | The unique identifier for the category being deleted. | Yes | string (uuid) |

##### Responses

| Code | Description |
| ---- | ----------- |
| 204 | Category deleted successfully. |
