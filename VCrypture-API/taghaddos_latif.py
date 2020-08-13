from io import BytesIO
from Crypto.Random import random
from PIL import Image, ImageDraw
from typing import Tuple

patterns = ((1, 1, 0, 0), (1, 0, 1, 0), (1, 0, 0, 1), (0, 1, 1, 0),
            (0, 1, 0, 1), (0, 0, 1, 1))


def _draw_block(draw, ij, colors):
    i, j = ij
    draw.point((2*i-1, 2*j-1), colors[0])
    draw.point((2*i-1, 2*j), colors[1])
    draw.point((2*i, 2*j-1), colors[2])
    draw.point((2*i, 2*j), colors[3])


def enc(source: BytesIO) -> Tuple[BytesIO, BytesIO]:
    with Image.open(source) as secret:
        # Enforce grayscale mode
        if secret.mode != 'L':
            secret = secret.convert('L')

        width, height = secret.size
        size_out = (width * 2, height * 2)
        share_A = Image.new('L', size_out)
        share_B = Image.new('L', size_out)

        draw_A = ImageDraw.Draw(share_A)
        draw_B = ImageDraw.Draw(share_B)

        for x in range(0, width):
            for y in range(0, height):
                shareA_colors = [0, 0, 0, 0]
                shareB_colors = [0, 0, 0, 0]
                for b in range(8):
                    pattern = random.choice(patterns)
                    if secret.getpixel((x, y)) >> b & 1:
                        for i in range(len(shareA_colors)):
                            shareA_colors[i] |= (pattern[i] << b)
                            shareB_colors[i] = shareA_colors[i]
                    else:
                        for i in range(len(shareA_colors)):
                            shareA_colors[i] |= (pattern[i] << b)
                            shareB_colors[i] |= ((1-pattern[i]) << b)
                _draw_block(draw_A, (x, y), shareA_colors)
                _draw_block(draw_B, (x, y), shareB_colors)

        # Return outputs
        out_A = BytesIO()
        out_B = BytesIO()

        share_A.save(out_A, 'PNG')
        share_A.close()
        out_A.seek(0)
        share_B.save(out_B, 'PNG')
        share_B.close()
        out_B.seek(0)

        return (out_A, out_B)


def dec(shares: Tuple[BytesIO, BytesIO]) -> BytesIO:
    share_A = Image.open(shares[0])
    share_B = Image.open(shares[1])

    if share_A.size != share_B.size:
        raise ValueError('Shares must have the same size!')

    # Enforce grayscale mode
    if share_A.mode != 'L':
        share_A = share_A.convert('L')
    if share_B.mode != 'L':
        share_B = share_B.convert('L')

    # Overlap shares to get the secret
    secret = Image.new('L', share_A.size)
    secret_draw = ImageDraw.Draw(secret)

    for x in range(secret.size[0]):
        for y in range(secret.size[1]):
            p1 = share_A.getpixel((x, y))
            p2 = share_B.getpixel((x, y))
            secret_draw.point((x, y), p1 & p2)

    share_A.close()
    share_B.close()

    out = BytesIO()
    secret.save(out, 'PNG')
    secret.close()
    out.seek(0)
    return out
