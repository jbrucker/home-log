"""Estimate time needed to compute a scrypt hash."""

import time
import os
import hashlib
from typing import Tuple


def estimate_scrypt_time(password: str, n: int, r: int, p: int) -> Tuple[float, bytes]:
    """
    Estimate the time needed to compute a scrypt hash.

    Args:
        password (str): The password to hash.
        n (int): CPU/memory cost factor.
        r (int): Block size.
        p (int): Parallelization factor.

    Returns:
        estimated time in seconds to compute the scrypt hash,
        averaged over multiple invocations, and the last hashed password.
    """
    # Generate a random salt
    salt = os.urandom(16)

    # How many iterations?
    count = 20

    start_time = time.time()
    for _ in range(count):
        hash = hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, maxmem=0)
    end_time = time.time()

    return (end_time - start_time) / max(count, 1), hash


def run_experiment(password: str, n: int, r: int, p: int) -> None:
    """
    Run the scrypt time estimation experiment.

    Args:
        password (str): The password to hash.
        n (int): CPU/memory cost factor.
        r (int): Block size.
        p (int): Parallelization factor.
    """
    print(f"Estimating time for scrypt with n={n}, r={r}, p={p}  ")
    estimated_time, password_hash = estimate_scrypt_time(password, n, r, p)
    print(f"{estimated_time:.4f} seconds")
    print(f"Hashed password {password_hash.hex()}")


if __name__ == "__main__":
    # Example usage
    password = "10 characters"[:10]
    n = 16384  # CPU/memory cost factor
    r = 8      # Block size
    p = 1      # Parallelization factor
    run_experiment(password, n=16384, r=8, p=1)

    try:
        run_experiment(password, n=16384, r=16, p=1)   # runs out of memory
    except Exception as ex:
        print("Exception:", ex)

    try:
        run_experiment(password, n=2 * 16384, r=8, p=1)   # runs out of memory
    except Exception as ex:
        print("Exception:", ex)
