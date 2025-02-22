a = 1000

def f1():
    nonlocal a
    a = 1

def f2():
    a = 2
    b = 3

    def f3():
        nonlocal b
        b = 5

    f1()
    f3()
    print(a)
    print(b)

f2()
