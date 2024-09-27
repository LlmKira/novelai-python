# 纠错码
# MIT: https://github.com/NovelAI/novelai-image-metadata/blob/main/nai_bch.py
import functools

import bchlib
import numpy as np

correctable_bits = 16
block_length = 2019
code_block_len = 1920


def bit_shuffle(data_bytes, w, h, use_bytes=False):
    bits = np.frombuffer(data_bytes, dtype=np.uint8)
    bit_fac = 8
    if use_bytes:
        bit_fac = 1
    else:
        bits = np.unpackbits(bits)
    bits = bits.reshape((h, w, 3 * bit_fac))
    code_block_len = 1920
    flat_tile_len = (w * h * 3) // code_block_len
    tile_w = 32
    if flat_tile_len // tile_w > 100:
        tile_w = 64
    tile_h = flat_tile_len // tile_w
    h_cutoff = (h // tile_h) * tile_h
    tile_hr = h - h_cutoff
    easy_tiles = bits[:h_cutoff].reshape(h_cutoff // tile_h, tile_h, w // tile_w, tile_w, 3 * bit_fac)
    easy_tiles = easy_tiles.swapaxes(1, 2)
    easy_tiles = easy_tiles.reshape(-1, tile_h * tile_w)
    easy_tiles = easy_tiles.T
    rest_tiles = bits[h_cutoff:]
    rest_tiles = rest_tiles.reshape(tile_hr, 1, w // tile_w, tile_w, 3 * bit_fac)
    rest_tiles = rest_tiles.swapaxes(1, 2)
    rest_tiles = rest_tiles.reshape(-1, tile_hr * tile_w)
    rest_tiles = rest_tiles.T
    rest_dim = rest_tiles.shape[-1]
    rest_tiles = np.pad(rest_tiles, ((0, 0), (0, easy_tiles.shape[-1] - rest_tiles.shape[-1])), mode='constant',
                        constant_values=0)
    bits = np.concatenate((easy_tiles, rest_tiles), axis=0)
    dim = bits.shape[-1]
    bits = bits.reshape((-1,))
    if not use_bytes:
        bits = np.packbits(bits)
    return bytearray(bits.tobytes()), dim, rest_tiles.shape[0], rest_dim


def bit_unshuffle(data_bytes, w, h, dim, rest_size, rest_dim, use_bytes=False):
    bits = np.frombuffer(data_bytes, dtype=np.uint8)
    bit_fac = 8
    if use_bytes:
        bit_fac = 1
    else:
        bits = np.unpackbits(bits)
    code_block_len = 1920
    flat_tile_len = (w * h * 3) // code_block_len
    tile_w = 32
    if flat_tile_len // tile_w > 100:
        tile_w = 64
    tile_h = flat_tile_len // tile_w
    h_cutoff = (h // tile_h) * tile_h
    tile_hr = h - h_cutoff
    bits = bits.reshape((-1, dim))
    rev_cutoff = bits.shape[0] - rest_size
    rest_tiles = bits[rev_cutoff:]
    rest_tiles = rest_tiles.reshape((-1, dim))
    rest_tiles = rest_tiles[:, :rest_dim]
    rest_tiles = rest_tiles.T
    rest_tiles = rest_tiles.reshape((tile_hr, w // tile_w, 1, tile_w, 3 * bit_fac))
    rest_tiles = rest_tiles.swapaxes(1, 2)
    rest_tiles = rest_tiles.reshape((-1,))
    easy_tiles = bits[:rev_cutoff]
    easy_tiles = easy_tiles.T
    easy_tiles = easy_tiles.reshape((h_cutoff // tile_h, w // tile_w, tile_h, tile_w, 3 * bit_fac))
    easy_tiles = easy_tiles.swapaxes(1, 2)
    easy_tiles = easy_tiles.reshape((-1,))
    data_bytes = np.concatenate((easy_tiles, rest_tiles), axis=0)
    if not use_bytes:
        data_bytes = np.packbits(data_bytes)
    data_bytes = data_bytes.tobytes()
    return bytearray(data_bytes)


@functools.lru_cache(maxsize=512)
def get_indices(len_db):
    indices = np.arange(0, len_db)
    rng = np.random.Generator(np.random.MT19937(31337))
    indices = rng.permutation(indices)
    unshuffled = indices.copy()
    unshuffled[indices] = np.arange(0, len_db)
    return indices, unshuffled


def rand_byte_shuffle(data_bytes):
    indices, _ = get_indices(len(data_bytes))
    data_bytes = np.frombuffer(data_bytes, dtype=np.uint8)
    data_bytes = bytearray(data_bytes[indices].tobytes())
    return data_bytes


def rand_byte_unshuffle(data_bytes):
    _, indices = get_indices(len(data_bytes))
    data_bytes = np.frombuffer(data_bytes, dtype=np.uint8)
    data_bytes = bytearray(data_bytes[indices].tobytes())
    return data_bytes


use_bytes = True  # Bit shuffling provides better resilience, but byte shuffling is much faster and still sufficient
shuffle_fn = lambda data_bytes, w, h: bit_shuffle(data_bytes, w, h, use_bytes=use_bytes)
unshuffle_fn = lambda data_bytes, w, h, dim, rest_size, rest_dim: bit_unshuffle(data_bytes, w, h, dim, rest_size,
                                                                                rest_dim, use_bytes=use_bytes)


def split_byte_ranges(data_bytes, n, w, h, shuffle=False):
    if shuffle:
        data_bytes, dim, rest_size, rest_dim = shuffle_fn(data_bytes.copy(), w, h)
    chunks = []
    for i in range(0, len(data_bytes), n):
        chunks.append(data_bytes[i:i + n])
    if shuffle:
        return chunks, dim, rest_size, rest_dim
    return chunks


def pad(data_bytes):
    return bytearray(data_bytes + b'\x00' * (2019 - len(data_bytes)))


# Returns codes for the data in data_bytes
def fec_encode(data_bytes, w, h):
    encoder = bchlib.BCH(16, prim_poly=17475)
    # import galois
    # encoder = galois.BCH(16383, 16383-224, d=17, c=224)
    chunks = [bytearray(encoder.encode(pad(x))) for x in split_byte_ranges(data_bytes, 2019, w, h, shuffle=True)[0]]
    return b''.join(chunks)


# Returns the error corrected data and number of corrected errors or None, None if errors are not correctable
def fec_decode(data_bytes, codes, w, h):
    encoder = bchlib.BCH(16, prim_poly=17475)
    chunks, dim, rest_size, rest_dim = split_byte_ranges(data_bytes, 2019, w, h, shuffle=True)
    codes = split_byte_ranges(codes, 28, w, h)
    corrected = []
    total_errors = 0
    for i, chunk in enumerate(chunks):
        c_len = len(chunk)
        chunk = pad(chunk)
        code = bytearray(codes[i])
        n_err = encoder.decode(chunk, code)
        if n_err > 0:
            total_errors += n_err
            encoder.correct(chunk, code)
        # Ignoring the following case, since it might be caused by corrupted codes which might not even be needed
        # if n_err < 0:
        #    raise ValueError("Too many errors to correct")
        corrected.append(chunk[:c_len])
    corrected = b''.join(corrected)
    corrected = unshuffle_fn(corrected, w, h, dim, rest_size, rest_dim)
    return corrected, total_errors
