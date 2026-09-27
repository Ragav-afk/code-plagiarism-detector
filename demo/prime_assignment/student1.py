def is_prime(n):
    if n <= 1:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n ** 0.5) + 1, 2):
        if n % i == 0:
            return False
    return True

def print_primes_up_to(limit):
    for num in range(2, limit + 1):
        if is_prime(num):
            print(num)

num = int(input("Enter upper limit: "))
print_primes_up_to(num)