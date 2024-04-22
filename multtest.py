import multiprocessing


def worker(a):
    print(a)


if __name__ == "__main__":
    a = []
    multiprocessing.set_start_method("spawn")
    p = multiprocessing.Process(target=worker, args=("hello",))
    p.start()
    a.append(p)
    p.join()
