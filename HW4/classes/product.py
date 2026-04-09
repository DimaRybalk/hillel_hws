class Product:

    def __init__(self,name: str,category: str,price: float,quantity: int):
        self.name = name
        self.category = category
        self.price = price
        self.quantity = quantity

    def __repr__(self):
        return f"Товар: {self.name}, Категорія:{self.category}, Ціна: {self.price}, Кількість: {self.quantity} "

    def set_new_price(self, new_price: float):
        self.price = new_price

    def set_new_quantity(self,new_quantity: int):
        self.quantity = new_quantity