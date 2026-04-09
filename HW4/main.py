from menu import choice_validator, show_menu, start_task
import time

def animation(text,x,delay):
    print(text, end="", flush=True) 
    for _ in range(x):      
        time.sleep(delay)     
        print(".", end="", flush=True) 
        time.sleep(0.1)
    print()


def start_shop():
    print("-"*15)
    print("SHOP MENU: ")
    show_menu()
    user_choice = choice_validator("Enter your choice: ")
    animation("Making your action",5,0.25)
    start_task(user_choice)

while True:
    start_shop()
