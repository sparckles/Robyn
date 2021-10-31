from pathos.pools import ProcessPool

import pathos

print(dir(pathos))

pool = ProcessPool(nodes=4)
results = pool.map(pow, [1,2,3,4], [5,6,7,8])
print(results)
