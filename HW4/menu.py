from menu_fucntions import (
    add_new_order,
    add_product_to_order,
    change_price,
    change_quantity,
    delete_product_from_order,
    exit_shop,
    show_order,
    show_products,
)


def show_menu():
    for key, value in menu.items():
        print(f"{key}: {value[0]}")


def choice_validator(prompt: str):
    choices_list = [choice for choice in menu]
    while True:
        try:
            choice = int(input(prompt))
            if choice in choices_list:
                return choice
            else:
                print("You need to choose only from menu options")
        except ValueError:
            print("Please enter a number")


def start_task(user_choice):
    return menu[user_choice][1]()


menu = {
    1: ("Show products", show_products),
    2: ("Change price", change_price),
    3: ("Change quantity", change_quantity),
    4: ("Add product to order", add_product_to_order),
    5: ("Delete product from order", delete_product_from_order),
    6: ("Show order", show_order),
    7: ("Add new order", add_new_order),
    0: ("Exit", exit_shop),
}
