# Strings

def calc_len(some_str):
    return len(some_str)

def add_strings(str1,str2):
    return str1+str2

# Integer

def square_int(some_int):
    return some_int**2
    # return int(some_int)*int(some_int)

def sum_nums(num1,num2):
    return num1+num2

def divide_nums(num1,num2):
    res = num1/num2
    return float(res)

# Lists

def average_num(list_of_nums):
    res = sum(list_of_nums)/len(list_of_nums)
    return float(res)

def common_values(list1,list2):
    res = set(list1) & set(list2)
    return list(res)

# Dicts

def print_keys(some_dict):
    return dict(some_dict).keys()

def add_dicts(dict1,dict2):
    return dict1 | dict2
    

# Sets

def add_sets(set1,set2):
    return set1 | set2

def check_subset(set1,set2):
    s1, s2 = set(set1), set(set2)

    if s1.issubset(s2):
        return f"{s1} є підмножиною {s2}"
    elif s2.issubset(s1):
        return f"{s2} є підмножиною {s1}"
    else:
        return "Множини не є підмножинами одна одної"

# Cycles and If's

def check_even(value):
    if value%2 == 0:
        return "Число парне"
    else:
        return "Число непарне"
    
def only_evens(some_list):
   return [i for i in some_list if i%2 == 0]

# lambda

check_even_with_lambda = lambda x: "парне" if x%2 == 0 else "не парне"
