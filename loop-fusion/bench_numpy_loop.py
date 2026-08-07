import numpy as np

from time import time

size = 1000000

arr = np.ones(size)

print("add1:")
t_start = time()
for _ in range(100):
    ret = np.empty_like(arr)
    for i in range(size):
        ret[i] = arr[i] + arr[i]
print(f"{time() - t_start:.3f} s")

print("add4:")
t_start = time()
for _ in range(100):
    ret = np.empty_like(arr)
    for i in range(size):
        ret[i] = arr[i] + arr[i] + arr[i] + arr[i] + arr[i]
print(f"{time() - t_start:.3f} s")
