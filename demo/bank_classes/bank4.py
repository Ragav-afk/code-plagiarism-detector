owner = "Ravi"
balance = 1000
history = []
amount = 500
if amount <= 0:
    print("Deposit must be positive")
else:
    balance += amount
    history.append(("deposit", amount))
amount = 200
if amount > balance:
    print("Insufficient funds")
else:
    balance -= amount
    history.append(("withdraw", amount))
for kind, amt in history:
    print(kind, amt)
print("Balance:", balance)
