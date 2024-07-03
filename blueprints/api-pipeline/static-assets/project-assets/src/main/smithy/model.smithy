$version: "2"
namespace {{{ namespace }}}

use aws.protocols#restJson1

@documentation("{{{ description }}}")
@restJson1
@paginated(inputToken: "nextToken", outputToken: "nextToken", pageSize: "pageSize")
service {{{ serviceName }}} {

}