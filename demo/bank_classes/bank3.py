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


if __name__ == "__main__":
    a = Account("Ravi")
    a.deposit(1000)
    try:
        a.withdraw(5000)
    except InsufficientFunds as e:
        print("Error:", e)
    a.apply_interest()
    print(a)
