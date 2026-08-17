from classes.order import Order


class Customer:
    def __init__(self, name: str, mail: str):
        self.name = name
        self.mail = mail
        self.orders: list[Order] = []
        self.total_order_price = 0

    def add_new_order(self, order: "Order"):
        self.orders.append(order)
