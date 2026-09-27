def check(x):
    # checks prime
    if x <= 1:
        return False
    if x == 2:
        return True
    if x % 2 == 0:
        return False
    for d in range(3, int(x ** 0.5) + 1, 2):
        if x % d == 0:
            return False
    return True

def show_all(upto):
    for v in range(2, upto + 1):
        if check(v):
            print(v)

upto = int(input("Enter upper limit: "))
show_all(upto)
