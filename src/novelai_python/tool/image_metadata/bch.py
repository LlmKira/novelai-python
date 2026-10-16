"""Binary BCH codec compatible with Linux-kernel ``lib/bch.c`` / ``bchlib``.

NovelAI protects the LSB stealth metadata of its images with
``bchlib.BCH(16, prim_poly=17475)`` (GF(2^14), t=16, 28 ECC bytes per
2019-byte chunk). ``bchlib`` is a C extension without Python 3.14 wheels, so
this module re-implements the same code in NumPy. Bit layout matches the
kernel exactly (checked against vectors produced by bchlib 2.1.3, see
``tests/fixtures/bch_vectors.json``): data bytes MSB-first, followed by the
ECC bits; ECC = data(x) * x^(m*t) mod g(x).
"""

from functools import lru_cache

import numpy as np

__all__ = ["BCH"]


@lru_cache(maxsize=8)
def _gf_tables(m: int, prim_poly: int):
    n = (1 << m) - 1
    exp = np.zeros(2 * n, dtype=np.int64)
    log = np.full(n + 1, -1, dtype=np.int64)
    x = 1
    for i in range(n):
        exp[i] = x
        log[x] = i
        x <<= 1
        if x & (1 << m):
            x ^= prim_poly
    exp[n:] = exp[:n]
    return exp, log


def _gf2_mul(a: int, b: int) -> int:
    """Carry-less product of two GF(2)[x] polynomials stored as ints."""
    r = 0
    while b:
        if b & 1:
            r ^= a
        a <<= 1
        b >>= 1
    return r


@lru_cache(maxsize=8)
def _generator(m: int, t: int, prim_poly: int) -> int:
    """g(x) = lcm of the minimal polynomials of alpha^1 .. alpha^(2t)."""
    exp, log = _gf_tables(m, prim_poly)
    n = (1 << m) - 1
    seen, g = set(), 1
    for i in range(1, 2 * t + 1):
        if i in seen:
            continue
        coset, j = [], i
        while j not in coset:
            coset.append(j)
            j = (j * 2) % n
        seen.update(coset)
        # minimal polynomial = prod (x - alpha^j) over the coset, coefficients in GF(2^m)
        poly = [1]  # highest degree first, field elements
        for j in coset:
            root = int(exp[j])
            nxt = [*poly, 0]
            for k in range(len(poly)):
                c = poly[k]
                if c:
                    nxt[k + 1] ^= int(exp[(log[c] + log[root]) % n])
            poly = nxt
        mp = 0
        for c in poly:
            assert c in (0, 1), "minimal polynomial must be binary"
            mp = (mp << 1) | c
        g = _gf2_mul(g, mp)
    return g


class BCH:
    """Subset of the ``bchlib.BCH`` API: ``encode``, ``decode``, ``correct``."""

    def __init__(self, t: int, prim_poly: int) -> None:
        self.t = t
        self.prim_poly = prim_poly
        self.m = prim_poly.bit_length() - 1
        self.n = (1 << self.m) - 1
        self.ecc_bits = self.m * t
        self.ecc_bytes = (self.ecc_bits + 7) // 8
        self._g = _generator(self.m, t, prim_poly)
        self._exp, self._log = _gf_tables(self.m, prim_poly)
        self._errloc: list[int] = []

    # ── encoding ────────────────────────────────────────────────────────
    def _remainder(self, bits_int: int, nbits: int) -> int:
        """(data(x) * x^ecc_bits) mod g(x) for a data polynomial of nbits bits."""
        g, gd = self._g, self._g.bit_length() - 1
        r = bits_int << gd
        for d in range(nbits + gd - 1, gd - 1, -1):
            if (r >> d) & 1:
                r ^= g << (d - gd)
        return r

    def encode(self, data: bytes) -> bytearray:
        r = self._remainder(int.from_bytes(data, "big"), len(data) * 8)
        # ecc bits occupy the top ecc_bits of ecc_bytes, MSB-first (kernel layout)
        pad = self.ecc_bytes * 8 - self.ecc_bits
        return bytearray((r << pad).to_bytes(self.ecc_bytes, "big"))

    # ── decoding ────────────────────────────────────────────────────────
    def _codeword_degrees(self, data: bytes, ecc: bytes) -> tuple[np.ndarray, int]:
        bits = np.unpackbits(np.frombuffer(bytes(data), dtype=np.uint8))
        ebits = np.unpackbits(np.frombuffer(bytes(ecc), dtype=np.uint8))[: self.ecc_bits]
        cw = np.concatenate([bits, ebits])
        N = cw.size
        return (N - 1 - np.nonzero(cw)[0]).astype(np.int64), N

    def decode(self, data, ecc) -> int:
        """Number of bit errors found (0 = clean), -1 if uncorrectable.
        Locations are kept for ``correct``."""
        self._errloc = []
        exp, log, n, t = self._exp, self._log, self.n, self.t
        degs, N = self._codeword_degrees(data, ecc)
        if degs.size == 0:
            return 0
        js = np.arange(1, 2 * t + 1, dtype=np.int64)
        powers = np.outer(js, degs) % n
        S = np.bitwise_xor.reduce(exp[powers], axis=1).astype(np.int64)
        if not S.any():
            return 0

        # Berlekamp–Massey over GF(2^m)
        def mul(a, b):
            return 0 if a == 0 or b == 0 else int(exp[(log[a] + log[b]) % n])

        def inv(a):
            return int(exp[(n - log[a]) % n])

        C, B = [1], [1]
        L, mshift, b = 0, 1, 1
        for k in range(2 * t):
            d = int(S[k])
            for i in range(1, L + 1):
                if i < len(C) and C[i]:
                    d ^= mul(C[i], int(S[k - i]))
            if d == 0:
                mshift += 1
                continue
            coef = mul(d, inv(b))
            T = C[:]
            need = len(B) + mshift
            if len(C) < need:
                C = C + [0] * (need - len(C))
            for i, bi in enumerate(B):
                if bi:
                    C[i + mshift] ^= mul(coef, bi)
            if k >= 2 * L:
                L, B, b, mshift = k + 1 - L, T, d, 1
            else:
                mshift += 1
        C = C[: L + 1]
        if t < L:
            return -1
        # Chien search: roots X^-1 of the locator, X = alpha^deg, deg in [0, N)
        degrees = np.arange(N, dtype=np.int64)
        acc = np.zeros(N, dtype=np.int64)
        for i, ci in enumerate(C):
            if ci == 0:
                continue
            term = exp[(log[ci] - i * degrees) % n]
            acc ^= term
        roots = np.nonzero(acc == 0)[0]
        if roots.size != L:
            return -1
        self._errloc = [int(N - 1 - d) for d in roots]  # bit index in data||ecc stream
        return L

    def correct(self, data: bytearray, ecc: bytearray) -> None:
        nd = len(data) * 8
        for pos in self._errloc:
            if pos < nd:
                data[pos // 8] ^= 1 << (7 - pos % 8)
            else:
                q = pos - nd
                ecc[q // 8] ^= 1 << (7 - q % 8)
