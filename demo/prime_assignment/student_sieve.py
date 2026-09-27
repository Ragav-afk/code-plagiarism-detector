def sieve_primes(n):
    is_prime_arr = [True] * (n + 1)
    is_prime_arr[0] = is_prime_arr[1] = False
    for i in range(2, int(n ** 0.5) + 1):
        if is_prime_arr[i]:
            for j in range(i * i, n + 1, i):
                is_prime_arr[j] = False
    primes = []
    for i in range(2, n + 1):
        if is_prime_arr[i]:
            primes.append(i)
    return primes

def show_primes(limit):
    result = sieve_primes(limit)
    for p in result:
        print(p)

limit = int(input("Enter upper limit: "))
show_primes(limit)