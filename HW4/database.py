from classes.product import Product


def load_data(filename: str):
    products = []
    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            clean_line = line.strip()
            data = clean_line.split(",")
            product_dict = {
                "name": data[0],
                "category": data[1],
                "price": float(data[2]),
                "quantity": int(data[3]),
            }

            product = Product(**product_dict)
            products.append(product)
    return products


def save_data(filename: str, products: list[Product]):
    with open(filename, "w", encoding="utf-8") as file:
        for product in products:
            line = f"{product.name},{product.category},{product.price},{product.quantity}\n"
            file.write(line)
        print("Data successfully changed")
