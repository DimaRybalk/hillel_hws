from classes.customer import Customer
from classes.order import Order
from database import load_data, save_data

DATA_FILENAME = "products.txt"

products = load_data(DATA_FILENAME)
current_order = Order()
current_customer = Customer("Новий користувач", "testmail@gmail.com")


def show_products():
    print("-" * 15)
    print("СПИСОК ТОВАРІВ НА СКЛАДІ:")
    print("-" * 15)
    for number, product in enumerate(products, 1):
        print(
            f"{number}. {product.name} | Категорія: {product.category} | Ціна: {product.price} | Залишок: {product.quantity}"
        )


def exit_shop():
    return exit()


def get_current_product(prompt):
    print("-" * 15)
    user_choice = int(input(prompt))
    if 0 < user_choice <= len(products):
        target_product = products[user_choice - 1]
        return target_product
    else:
        print("There are no such products")


def add_product_to_order():
    show_products()
    while True:
        try:
            target_product = get_current_product(
                "Which product you want to add to order?: "
            )
            if target_product.quantity > 0:
                new_quantity = target_product.quantity - 1
                target_product.set_new_quantity(new_quantity)
                save_data(DATA_FILENAME, products)
                current_order.add_product(target_product)
                print(f"The cost of this product is: {target_product.price}")
                break
            else:
                print("This product is out of stock")
                break

        except ValueError:
            print("You should type only numbers")


def delete_product_from_order():
    current_order.show_order()

    if not current_order.order_list:
        return

    while True:
        try:
            user_choice = int(input("Which product you want to remove?: "))

            if 0 < user_choice <= len(current_order.order_list):
                target_product = current_order.order_list[user_choice - 1]
                new_quantity = target_product.quantity + 1
                target_product.set_new_quantity(new_quantity)
                current_order.delete_product(target_product)
                save_data(DATA_FILENAME, products)
                current_order.calculate_total_cost()
                print(f"{target_product.name} was removed")
                break
            else:
                print("This order doesn't have this product")
        except ValueError:
            print("You should type only numbers")


def show_order():
    print("-" * 15)
    current_order.show_order()
    total_cost = current_order.calculate_total_cost()
    print(f"Total cost of your order: {total_cost}")


def add_new_order():
    print("-" * 15)
    global current_order

    if not current_order.order_list:
        print("Nothing to add")
        return

    current_customer.add_new_order(current_order)
    current_order = Order()

    for number, order in enumerate(current_customer.orders, 1):
        actual_total = order.calculate_total_cost()
        print(
            f"Order #{number}: Number of products: {len(order.order_list)} | Total cost: {actual_total} "
        )


def change_price():
    show_products()

    while True:
        try:
            target_product = get_current_product(
                "For which product you want to change price?: "
            )
            while True:
                try:
                    new_price = float(input("What is new price?: "))
                    if new_price > 0:
                        target_product.set_new_price(new_price)
                        save_data(DATA_FILENAME, products)
                        return
                    else:
                        print("Price should be greater than 0")
                except ValueError:
                    print("You should type only numbers")

        except ValueError:
            print("You should type only numbers")


def change_quantity():
    show_products()

    while True:
        try:
            target_product = get_current_product(
                "For which product you want to change quantity?: "
            )
            while True:
                try:
                    new_quantity = int(input("What is new quantity?: "))
                    if new_quantity > 0:
                        target_product.set_new_quantity(new_quantity)
                        save_data(DATA_FILENAME, products)
                        return
                    else:
                        print("quantity should be greater than 0")
                except ValueError:
                    print("You should type only numbers")
        except ValueError:
            print("You should type only numbers")
