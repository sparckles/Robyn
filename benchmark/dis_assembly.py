import dis


def myfn():
    return "Hello world"


def myfn1():
    return f"Hello world"


def myfn2():
    return f"Hello world {1}"


a = 1


def myfn3():
    global a
    return "Hello world " + str(a)


def myfn4():
    return f"Hello" + " world"


dis.dis(myfn)
dis.dis(myfn1)
dis.dis(myfn2)
dis.dis(myfn3)
dis.dis(myfn4)
