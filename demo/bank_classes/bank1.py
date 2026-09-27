class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance
        self.history = []

    def deposit(self, amount):
        if amount <= 0:
            print("Deposit must be positive")
            return False
        self.balance += amount
        self.history.append(("deposit", amount))
        return True

    def withdraw(self, amount):
        if amount > self.balance:
            print("Insufficient funds")
            return False
        self.balance -= amount
        self.history.append(("withdraw", amount))
        return True

    def statement(self):
        for kind, amount in self.history:
            print(kind, amount)
        print("Balance:", self.balance)


class SavingsAccount(BankAccount):
    def __init__(self, owner, balance=0, rate=0.04):
        super().__init__(owner, balance)
        self.rate = rate

    def add_interest(self):
        interest = self.balance * self.rate
        self.deposit(interest)
        return interest


acc = SavingsAccount("Ravi", 1000)
acc.deposit(500)
acc.withdraw(200)
acc.add_interest()
acc.statement()
