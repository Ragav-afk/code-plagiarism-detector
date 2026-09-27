limit = int(input("Enter upper limit: "))
primes = [p for p in range(2, limit + 1) if all(p % d for d in range(2, int(p ** 0.5) + 1))]
print(*primes, sep="\n")
