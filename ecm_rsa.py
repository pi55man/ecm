import random
import math
import time


def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return abs(a)


def is_prime(n):
    if n < 2:
        return False
    small = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    for p in small:
        if n % p == 0:
            return n == p
    d = n - 1
    s = 0
    while d % 2 == 0:
        d = d // 2
        s = s + 1
    for a in small:
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        composite = True
        for i in range(s - 1):
            x = x * x % n
            if x == n - 1:
                composite = False
                break
        if composite:
            return False
    return True


def primes_up_to(n):
    is_p = [True] * (n + 1)
    is_p[0] = False
    is_p[1] = False
    i = 2
    while i * i <= n:
        if is_p[i]:
            for j in range(i * i, n + 1, i):
                is_p[j] = False
        i = i + 1
    result = []
    for i in range(n + 1):
        if is_p[i]:
            result.append(i)
    return result


def random_prime(bits):
    while True:
        x = random.getrandbits(bits)
        x = x | (1 << (bits - 1)) | 1
        if is_prime(x):
            return x


def make_curve(n):
    sigma = random.randint(6, n - 1)
    u = (sigma * sigma - 5) % n
    v = 4 * sigma % n
    x = pow(u, 3, n)
    z = pow(v, 3, n)
    top = pow(v - u, 3, n) * (3 * u + v) % n
    bottom = 16 * x * v % n
    g = gcd(bottom, n)
    if g != 1:
        return g, 0, 0, 0
    a24 = top * pow(bottom, -1, n) % n
    return 1, a24, x, z


def point_double(x, z, a24, n):
    s = (x + z) * (x + z) % n
    d = (x - z) * (x - z) % n
    t = s - d
    x2 = s * d % n
    z2 = t * (d + a24 * t) % n
    return x2, z2


def point_add(x1, z1, x2, z2, xd, zd, n):
    a = (x1 - z1) * (x2 + z2) % n
    b = (x1 + z1) * (x2 - z2) % n
    x3 = zd * (a + b) * (a + b) % n
    z3 = xd * (a - b) * (a - b) % n
    return x3, z3


def ladder(k, x, z, a24, n):
    if k == 1:
        return x, z
    x0, z0 = x, z
    x1, z1 = point_double(x, z, a24, n)
    bits = bin(k)[3:]
    for bit in bits:
        if bit == "1":
            x0, z0 = point_add(x0, z0, x1, z1, x, z, n)
            x1, z1 = point_double(x1, z1, a24, n)
        else:
            x1, z1 = point_add(x0, z0, x1, z1, x, z, n)
            x0, z0 = point_double(x0, z0, a24, n)
    return x0, z0


def ecm_stage1(n, B1, primes):
    g, a24, x, z = make_curve(n)
    if g != 1:
        if g < n:
            return g
        return 1
    for p in primes:
        if p > B1:
            break
        pk = p
        while pk * p <= B1:
            pk = pk * p
        x, z = ladder(pk, x, z, a24, n)
    g = gcd(z, n)
    if g > 1 and g < n:
        return g
    return 1


def ecm(n, B1, max_curves):
    if n % 2 == 0:
        return 2, 0
    primes = primes_up_to(B1)
    for curve in range(1, max_curves + 1):
        f = ecm_stage1(n, B1, primes)
        if f != 1:
            return f, curve
    return 1, max_curves


def trial_division(n, limit):
    if n % 2 == 0:
        return 2
    d = 3
    while d <= limit:
        if n % d == 0:
            return d
        d = d + 2
    return 1


def make_weak_key(small_bits, big_bits):
    e = 65537
    while True:
        p = random_prime(small_bits)
        q = random_prime(big_bits)
        phi = (p - 1) * (q - 1)
        if gcd(e, phi) == 1:
            break
    n = p * q
    d = pow(e, -1, phi)
    return n, e, d, p, q


def pick_b1(bits):
    if bits <= 30:
        return 500
    if bits <= 40:
        return 2000
    if bits <= 50:
        return 11000
    return 50000


def find_factor(n):
    f = trial_division(n, 1000)
    if f != 1:
        return f, 0
    levels = [[500, 25], [2000, 90], [11000, 300], [50000, 200]]
    total = 0
    for level in levels:
        B1 = level[0]
        curves = level[1]
        print("B1 =", B1)
        f, used = ecm(n, B1, curves)
        total = total + used
        if f != 1:
            return f, total
    return 1, total


def break_key(n, e, c):
    p, curves = find_factor(n)
    if p == 1:
        return 0, 0, 0, 0, curves
    q = n // p
    phi = (p - 1) * (q - 1)
    d = pow(e, -1, phi)
    m = pow(c, d, n)
    return m, p, q, d, curves


def read_message():
    msg = input("message: ")
    if msg == "":
        msg = "attack at dawn"
    return msg


def read_number(text):
    while True:
        s = input(text).strip()
        try:
            return int(s)
        except ValueError:
            print("invalid number")


def attack(p, q, message):
    e = 65537
    n = p * q
    phi = (p - 1) * (q - 1)
    d = pow(e, -1, phi)

    m = int.from_bytes(message.encode(), "big")
    if m >= n:
        print("message too long")
        return
    c = pow(m, e, n)

    print()
    print("n =", n)
    print("bits:", n.bit_length())
    print("e =", e)
    print("c =", c)
    print()

    start = time.time()
    m2, found_p, found_q, found_d, curves = break_key(n, e, c)
    elapsed = time.time() - start
    print()

    if found_p == 0:
        print("no factor found")
        print("curves:", curves)
        print("time: %.2f s" % elapsed)
        print()
        return

    text = m2.to_bytes((m2.bit_length() + 7) // 8, "big").decode(errors="replace")
    print("p =", found_p, "(" + str(found_p.bit_length()) + " bits)")
    print("q =", found_q, "(" + str(found_q.bit_length()) + " bits)")
    print("d correct:", found_d == d)
    print("message:", text)
    print("curves:", curves)
    print("time: %.2f s" % elapsed)
    print()


def random_demo():
    bits = input("bits of p: ").strip()
    if bits.isdigit() and int(bits) >= 2:
        bits = int(bits)
    else:
        bits = 40
    n, e, d, p, q = make_weak_key(bits, 500)
    message = read_message()
    attack(p, q, message)


def custom_demo():
    e = 65537
    p = read_number("p: ")
    q = read_number("q: ")
    if not is_prime(p):
        print("p is not prime")
        return
    if not is_prime(q):
        print("q is not prime")
        return
    if p == q:
        print("p and q are equal")
        return
    if gcd(e, (p - 1) * (q - 1)) != 1:
        print("gcd(e, phi) != 1")
        return
    message = read_message()
    attack(p, q, message)


def prime_helper():
    bits = read_number("bits: ")
    if bits < 2:
        print("too small")
        return
    print(random_prime(bits))
    print()


def timing_table():
    print("%-8s %-10s %-10s %-8s" % ("bits", "trial", "ecm", "curves"))
    for bits in [16, 20, 24, 32, 40, 48]:
        n, e, d, p, q = make_weak_key(bits, 500)

        if bits <= 24:
            start = time.time()
            f = trial_division(n, p)
            t1 = time.time() - start
            trial_text = "%.3f s" % t1
        else:
            trial_text = "-"

        start = time.time()
        f, curves = ecm(n, pick_b1(bits), 5000)
        t2 = time.time() - start
        if f == p:
            ecm_text = "%.3f s" % t2
        else:
            ecm_text = "-"

        print("%-8d %-10s %-10s %-8d" % (bits, trial_text, ecm_text, curves))
    print()


def main():
    while True:
        print("1. random key")
        print("2. enter p and q")
        print("3. random prime")
        print("4. timing table")
        print("5. exit")
        choice = input("> ").strip()
        print()
        try:
            if choice == "1":
                random_demo()
            elif choice == "2":
                custom_demo()
            elif choice == "3":
                prime_helper()
            elif choice == "4":
                timing_table()
            elif choice == "5":
                break
            else:
                print("invalid option")
                print()
        except KeyboardInterrupt:
            print()
            print("interrupted")
            print()


main()

