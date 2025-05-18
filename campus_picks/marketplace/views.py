from acid_db.views import create_record, read_record, update_record, delete_record, query_records


def createProduct(data: dict) -> str:
    return create_record('product', data)


def getProduct(productId: str) -> dict:
    return read_record('product', productId)


def updateProduct(productId: str, data: dict) -> None:
    update_record('product', productId, data)


def deleteProduct(productId: str) -> None:
    delete_record('product', productId)


def listProducts() -> list:
    return query_records('product', {})
