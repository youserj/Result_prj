import timeit
from src.StructResult.result import OK, Error, Simple

# test data
ok_result = Simple(value=1)
error_result = Error(ValueError("fail"))


# var 1: if not result.is_ok()
def check_is_ok(result):
    return not result.is_ok()


# var 2: if not isinstance(result, Error)
def check_isinstance(result):
    return not isinstance(result, Error)


# OK_result speed
time_is_ok_ok = timeit.timeit(lambda: check_is_ok(ok_result), number=1_000_000)
time_isinstance_ok = timeit.timeit(lambda: check_isinstance(ok_result), number=1_000_000)


# Error_result speed
time_is_ok_err = timeit.timeit(lambda: check_is_ok(error_result), number=1_000_000)
time_isinstance_err = timeit.timeit(lambda: check_isinstance(error_result), number=1_000_000)

print(f"Ok-res:")
print(f"  is_ok():      {time_is_ok_ok:.6f} sec (1M calls)")
print(f"  isinstance(): {time_isinstance_ok:.6f} sec (1M calls)")

print(f"\nError-res:")
print(f"  is_ok():      {time_is_ok_err:.6f} sec (1M calls)")
print(f"  isinstance(): {time_isinstance_err:.6f} sec (1M calls)")