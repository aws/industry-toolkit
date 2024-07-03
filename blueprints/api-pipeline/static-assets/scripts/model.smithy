```yaml
namespace com.example.one

@documentation("This API allows users to add and remove items from their cart. Also allows for the updating of quantities.")
@http(method: "POST", uri: "/shopping-cart", code: 201)
operation CreateShoppingCartRequest {
    input: CreateShoppingCartRequestInput,
    output: CreateShoppingCartResponseOutput
}

@documentation("Creates a new shopping cart.")
structure CreateShoppingCartRequestInput {
    @documentation("The unique identifier for the user creating the cart.")
    userId: String
}

@documentation("Response object for creating a new shopping cart.")
structure CreateShoppingCartResponseOutput {
    @documentation("The unique identifier for the newly created shopping cart.")
    cartId: String
}

@documentation("Retrieves the contents of a shopping cart.")
@http(method: "GET", uri: "/shopping-cart/{cartId}", code: 200)
operation GetShoppingCartRequest {
    input: GetShoppingCartRequestInput,
    output: GetShoppingCartResponseOutput
}

@documentation("Input object for retrieving a shopping cart.")
structure GetShoppingCartRequestInput {
    @documentation("The unique identifier for the shopping cart to retrieve.")
    @httpLabel
    cartId: String
}

@documentation("Response object for retrieving a shopping cart.")
structure GetShoppingCartResponseOutput {
    @documentation("The list of items in the shopping cart.")
    items: CartItemList
}

@documentation("Adds an item to a shopping cart.")
@http(method: "POST", uri: "/shopping-cart/{cartId}/items", code: 201)
operation AddItemToCartRequest {
    input: AddItemToCartRequestInput,
    output: AddItemToCartResponseOutput
}

@documentation("Input object for adding an item to a shopping cart.")
structure AddItemToCartRequestInput {
    @documentation("The unique identifier for the shopping cart.")
    @httpLabel
    cartId: String,
    @documentation("The unique identifier for the item to add.")
    itemId: String,
    @documentation("The quantity of the item to add.")
    quantity: Integer
}

@documentation("Response object for adding an item to a shopping cart.")
structure AddItemToCartResponseOutput {
    @documentation("The updated list of items in the shopping cart.")
    items: CartItemList
}

@documentation("Updates the quantity of an item in a shopping cart.")
@http(method: "PUT", uri: "/shopping-cart/{cartId}/items/{itemId}", code: 200)
operation UpdateItemQuantityRequest {
    input: UpdateItemQuantityRequestInput,
    output: UpdateItemQuantityResponseOutput
}

@documentation("Input object for updating the quantity of an item in a shopping cart.")
structure UpdateItemQuantityRequestInput {
    @documentation("The unique identifier for the shopping cart.")
    @httpLabel
    cartId: String,
    @documentation("The unique identifier for the item to update.")
    @httpLabel
    itemId: String,
    @documentation("The new quantity for the item.")
    quantity: Integer
}

@documentation("Response object for updating the quantity of an item in a shopping cart.")
structure UpdateItemQuantityResponseOutput {
    @documentation("The updated list of items in the shopping cart.")
    items: CartItemList
}

@documentation("Removes an item from a shopping cart.")
@http(method: "DELETE", uri: "/shopping-cart/{cartId}/items/{itemId}", code: 200)
operation RemoveItemFromCartRequest {
    input: RemoveItemFromCartRequestInput,
    output: RemoveItemFromCartResponseOutput
}

@documentation("Input object for removing an item from a shopping cart.")
structure RemoveItemFromCartRequestInput {
    @documentation("The unique identifier for the shopping cart.")
    @httpLabel
    cartId: String,
    @documentation("The unique identifier for the item to remove.")
    @httpLabel
    itemId: String
}

@documentation("Response object for removing an item from a shopping cart.")
structure RemoveItemFromCartResponseOutput {
    @documentation("The updated list of items in the shopping cart.")
    items: CartItemList
}

@documentation("Clears all items from a shopping cart.")
@http(method: "DELETE", uri: "/shopping-cart/{cartId}", code: 200)
operation ClearShoppingCartRequest {
    input: ClearShoppingCartRequestInput,
    output: ClearShoppingCartResponseOutput
}

@documentation("Input object for clearing a shopping cart.")
structure ClearShoppingCartRequestInput {
    @documentation("The unique identifier for the shopping cart to clear.")
    @httpLabel
    cartId: String
}

@documentation("Response object for clearing a shopping cart.")
structure ClearShoppingCartResponseOutput {
    @documentation("A boolean indicating if the shopping cart was successfully cleared.")
    success: Boolean
}

structure CartItemList {
    @documentation("The list of items in the shopping cart.")
    items: CartItem[]
}

structure CartItem {
    @documentation("The unique identifier for the item.")
    itemId: String,
    @documentation("The name of the item.")
    name: String,
    @documentation("The quantity of the item in the cart.")
    quantity: Integer,
    @documentation("The price of the item.")
    price: Double
}
```

This Smithy IDL document defines a RESTful API for a shopping cart service in the namespace `com.example.one`. The API is named `shopping-cart` and has a description explaining its purpose.

The API includes the following operations:

1. `CreateShoppingCartRequest`: Creates a new shopping cart for a user.
2. `GetShoppingCartRequest`: Retrieves the contents of a shopping cart.
3. `AddItemToCartRequest`: Adds an item to a shopping cart.
4. `UpdateItemQuantityRequest`: Updates the quantity of an item in a shopping cart.
5. `RemoveItemFromCartRequest`: Removes an item from a shopping cart.
6. `ClearShoppingCartRequest`: Clears all items from a shopping cart.

Each operation has a corresponding input and output structure, as well as documentation explaining its purpose and the meaning of each input and output field.

The API also defines two additional structures: `CartItemList` and `CartItem`. `CartItemList` represents a list of items in a shopping cart, and `CartItem` represents an individual item with its details such as item ID, name, quantity, and price.

The HTTP methods and URIs are defined for each operation, following RESTful conventions. The appropriate HTTP status codes are also specified for each operation's response.