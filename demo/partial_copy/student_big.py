class InsufficientFunds(Exception):
    pass


class Account:
    interest_rate = 0.04

    def __init__(self, holder):
        self.holder = holder
        self.transactions = []

    @property
    def balance(self):
        return sum(self.transactions)

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        self.transactions.append(amount)

    def withdraw(self, amount):
        if amount > self.balance:
            raise InsufficientFunds(f"{self.holder} has only {self.balance}")
        self.transactions.append(-amount)

    def apply_interest(self):
        self.deposit(self.balance * Account.interest_rate)

    def __str__(self):
        lines = [f"{'+' if t > 0 else '-'}{abs(t)}" for t in self.transactions]
        return "\n".join(lines + [f"Balance: {self.balance}"])


def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

def print_sorted(items):
    sorted_items = bubble_sort(items)
    for item in sorted_items:
        print(item)

def fibonacci(n):
    if n <= 0:
        return []
    if n == 1:
        return [0]
    result = [0, 1]
    for i in range(2, n):
        result.append(result[i-1] + result[i-2])
    return result

def print_fib_sequence(count):
    seq = fibonacci(count)
    for num in seq:
        print(num)


def check(x):
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
