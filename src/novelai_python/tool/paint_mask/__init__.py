from io import BytesIO

from PIL import Image, ImageChops, ImageFilter

_FORMATS = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".webp": "WEBP", ".bmp": "BMP"}


def _repeat(img: Image.Image, flt: ImageFilter.Filter, times: int) -> Image.Image:
    for _ in range(times):
        img = img.filter(flt)
    return img


def _threshold(level: int) -> list[int]:
    """Lookup table for Image.point: 255 above level, 0 otherwise."""
    return [255 if v > level else 0 for v in range(256)]


def create_mask_from_sketch(
    original_img_bytes: bytes,
    sketch_img_bytes: bytes,
    min_block_size: int = 15,
    jagged_edges: bool = True,
    output_format: str = ".png",
) -> bytes:
    """
    Create an inpainting mask from the pixels that differ between an original image and a sketch over it.

    :param original_img_bytes: encoded original image.
    :param sketch_img_bytes: encoded sketched image, same size as the original.
    :param min_block_size: size of the pixel blocks of the mask; 1 disables pixelation.
    :param jagged_edges: bigger morphology kernel and a final threshold for sharper, stepped edges.
    :param output_format: ".png" (default) or ".jpg"/".webp"/".bmp".
    :return: encoded single-channel mask (white = repaint).
    """
    ori = Image.open(BytesIO(original_img_bytes)).convert("RGB")
    sketch = Image.open(BytesIO(sketch_img_bytes)).convert("RGB")
    if ori.size != sketch.size:
        raise ValueError("Images must have the same size.")

    # changed pixels -> grayscale (ITU-R 601 weights, as OpenCV's BGR2GRAY) -> binary
    diff = ImageChops.difference(ori, sketch).convert("L")
    mask = diff.point(_threshold(10))

    # square kernel: MinFilter = erode, MaxFilter = dilate
    k = 7 if jagged_edges else 3
    erode, dilate = ImageFilter.MinFilter(k), ImageFilter.MaxFilter(k)
    mask = _repeat(_repeat(mask, erode, 2), dilate, 2)  # opening: drop small noise
    mask = _repeat(mask, dilate, 2)  # grow the painted area
    mask = _repeat(_repeat(mask, dilate, 3), erode, 3)  # closing: join nearby areas
    mask = mask.filter(ImageFilter.GaussianBlur(1.1))  # sigma of OpenCV's 5x5 kernel

    if min_block_size > 1:
        w, h = mask.size
        small = mask.resize((max(1, w // min_block_size), max(1, h // min_block_size)), Image.Resampling.BILINEAR)
        mask = small.resize((w, h), Image.Resampling.NEAREST)

    if jagged_edges:
        mask = mask.point(_threshold(128))

    fmt = _FORMATS.get(output_format.lower())
    if fmt is None:
        raise ValueError(f"Unsupported output format: {output_format}")
    out = BytesIO()
    mask.save(out, format=fmt)
    return out.getvalue()
