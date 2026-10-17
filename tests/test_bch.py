"""Pure-NumPy BCH must match bchlib 2.1.3 bit for bit: vectors were produced by
the real bchlib (BCH(16, prim_poly=17475), the code NovelAI uses for its
image-metadata FEC) with 0..20 random bit flips per codeword."""

import base64
import json
from pathlib import Path

from novelai_python.tool.image_metadata.bch import BCH

V = json.loads((Path(__file__).parent / "fixtures" / "bch_vectors.json").read_text(encoding="utf-8"))


def b(s):
    return bytearray(base64.b64decode(s))


def test_parameters_match_bchlib():
    bch = BCH(16, prim_poly=17475)
    assert (bch.m, bch.n, bch.t, bch.ecc_bits, bch.ecc_bytes) == (V["m"], V["n"], V["t"], V["ecc_bits"], V["ecc_bytes"])


def test_encode_matches_bchlib():
    bch = BCH(16, prim_poly=17475)
    for c in V["cases"]:
        assert bch.encode(bytes(b(c["data"]))) == b(c["ecc"])


def test_decode_and_correct_match_bchlib():
    bch = BCH(16, prim_poly=17475)
    for c in V["cases"]:
        d, e = b(c["cdata"]), b(c["cecc"])
        nerr = bch.decode(d, e)
        assert nerr == c["nerr"], (c["len"], c["flips"], nerr, c["nerr"])
        if nerr > 0:
            bch.correct(d, e)
            assert d == b(c["fixed"]) and e == b(c["fixed_ecc"])
            assert d == b(c["data"])
