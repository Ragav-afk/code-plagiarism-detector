def check(x):
    if x <= 1:
        return False
    for i in range(2, int(x ** 0.5) + 1):
        if x % i == 0:
            return False
    return True

val = int(input("Enter a number: "))

if check(val):
    print(f"{val} is a prime number!")
else:
    print(f"{val} is not a prime number.")
