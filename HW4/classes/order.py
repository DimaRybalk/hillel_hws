from classes.product import Product


class Order:

    def __init__(self):
        self.order_list: list[Product] = []
        self.total_cost: float = 0

    def add_product(self,product: "Product"):
        self.order_list.append(product)

    def show_order(self):
        if not self.order_list:
            print("Order list is empty")

        for index, item in enumerate(self.order_list, 1):
            print(f"{index}. {item.name}")

    def calculate_total_cost(self):
        self.total_cost = 0
        for item in self.order_list:
          self.total_cost += item.price  
        return self.total_cost

