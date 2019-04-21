# coding=utf-8
import random

"""Generate pseudorandom number."""
num1 = [str(random.randint(0, 9)) for i in range(7)]
num2 = [str(random.randint(0, 9)) for i in range(7)]
num3 = [str(random.randint(0, 9)) for i in range(7)]
print ''.join(num1) + '-' + ''.join(num2) + '-' + ''.join(num3)
