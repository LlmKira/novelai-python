import cv2 as cv
import numpy as np


def create_mask_from_sketch(
        original_img_bytes: bytes,
        sketch_img_bytes: bytes,
        min_block_size: int = 15,
        jagged_edges: bool = True,
        output_format: str = '.png'
) -> bytes:
    """
    Function to create a mask from original and sketch images input as bytes. Returns BytesIO object.

    :param original_img_bytes:  Bytes corresponding to the original image.
    :param sketch_img_bytes:  Bytes corresponding to the sketch image.
    :param min_block_size:  The minimum size of the pixel blocks. Default is 1, i.e., no pixelation.
    :param jagged_edges:  If set to True, the edges of the resulting mask will be more jagged.
    :param output_format:  Format of the output image. Defaults to '.png'. It could also be '.jpg'
    :return:  bytes corresponding to the resultant mask
    """

    # Load images
    ori_img = cv.imdecode(np.frombuffer(original_img_bytes, np.uint8), cv.IMREAD_COLOR)
    sketch_img = cv.imdecode(np.frombuffer(sketch_img_bytes, np.uint8), cv.IMREAD_COLOR)

    # Check if images have the same size
    if ori_img.shape != sketch_img.shape:
        raise ValueError("Images must have the same size.")

    # Calculate difference between the original and sketch images
    diff_img = cv.absdiff(ori_img, sketch_img)

    # Convert the difference image to grayscale
    diff_gray = cv.cvtColor(diff_img, cv.COLOR_BGR2GRAY)

    # Threshold to create the mask
    _, thresh = cv.threshold(diff_gray, 10, 255, cv.THRESH_BINARY)

    # Create bigger kernel for morphological operations
    if jagged_edges:
        # Use a bigger kernel for dilation to create larger 'step' effect at the edges
        kernel = np.ones((7, 7), np.uint8)
    else:
        kernel = np.ones((3, 3), np.uint8)

    # Perform morphological opening to remove small noise
    opening = cv.morphologyEx(thresh, cv.MORPH_OPEN, kernel, iterations=2)

    # Perform morphological dilation
    dilation = cv.dilate(opening, kernel, iterations=2)

    # Perform morphological closing to connect separated areas
    closing = cv.morphologyEx(dilation, cv.MORPH_CLOSE, kernel, iterations=3)

    # Further remove noise with a Gaussian filter
    smooth = cv.GaussianBlur(closing, (5, 5), 0)

    if min_block_size > 1:
        # Resize to smaller image, then resize back to original size to create a pixelated effect
        small = cv.resize(smooth, (smooth.shape[1] // min_block_size, smooth.shape[0] // min_block_size),
                          interpolation=cv.INTER_LINEAR)
        smooth = cv.resize(small, (smooth.shape[1], smooth.shape[0]), interpolation=cv.INTER_NEAREST)

    if jagged_edges:
        # Apply additional thresholding to create sharper, jagged edges
        _, smooth = cv.threshold(smooth, 128, 255, cv.THRESH_BINARY)

    # Convert image to BytesIO object
    is_success, buffer = cv.imencode(output_format, smooth)
    if is_success:
        output_io = buffer.tobytes()
    else:
        raise ValueError("Error during conversion of image to BytesIO object")

    return output_io
