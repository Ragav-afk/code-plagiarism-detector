def fact(x):
    if x < 0:
        return None
    val = 1
    for i in range(1, x + 1):
        val *= i
    return val

num = int(input("Enter a number: "))
print(f"The factorial is: {fact(num)}")
