# Assignment 3 - my own implementation
class Wallet:
    def __init__(self, name, amt=0):
        self.name = name
        self.amt = amt
        self.log = []

    # show all transactions
    def show(self):
        for t, a in self.log:
            print(t, a)
        print("Balance:", self.amt)

    def take_out(self, value):
        if value > self.amt:
            print("Not enough money")
            return False
        self.amt -= value
        self.log.append(("withdraw", value))
        return True

    def put_in(self, value):
        if value <= 0:
            print("Amount should be positive")
            return False
        self.amt += value
        self.log.append(("deposit", value))
        return True


class InterestWallet(Wallet):
    def __init__(self, name, amt=0, r=0.04):
        super().__init__(name, amt)
        self.r = r

    def grow(self):
        extra = self.amt * self.r
        self.put_in(extra)
        return extra


w = InterestWallet("Kumar", 1000)
w.put_in(500)
w.take_out(200)
w.grow()
w.show()
