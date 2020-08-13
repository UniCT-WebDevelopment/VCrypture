from io import BytesIO
from Crypto.Random import random
from PIL import Image, ImageDraw
from typing import Tuple

patterns = ((1, 1, 0, 0), (1, 0, 1, 0), (1, 0, 0, 1), (0, 1, 1, 0),
            (0, 1, 0, 1), (0, 0, 1, 1))


def enc(source: BytesIO) -> Tuple[BytesIO, BytesIO]:
    with Image.open(source) as secret:
        # Convert the input image to binary
        secret = secret.convert('1')

        # Prepare the two shares
        width, height = secret.size
        share_size = tuple(s * 2 for s in secret.size)
        share_A = Image.new('1', share_size)
        draw_A = ImageDraw.Draw(share_A)
        share_B = Image.new('1', share_size)
        draw_B = ImageDraw.Draw(share_B)

        # Cycle through pixels
        for x in range(width):
            for y in range(height):
                pixel = secret.getpixel((x, y))
                pat = random.choice(patterns)
                # Share A will always get the pattern
                draw_A.point((x * 2, y * 2), pat[0])
                draw_A.point((x * 2 + 1, y * 2), pat[1])
                draw_A.point((x * 2, y * 2 + 1), pat[2])
                draw_A.point((x * 2 + 1, y * 2 + 1), pat[3])
                if pixel == 0:  # B gets the anti-pattern
                    draw_B.point((x * 2, y * 2), 1 - pat[0])
                    draw_B.point((x * 2 + 1, y * 2), 1 - pat[1])
                    draw_B.point((x * 2, y * 2 + 1), 1 - pat[2])
                    draw_B.point((x * 2 + 1, y * 2 + 1), 1 - pat[3])
                else:
                    draw_B.point((x * 2, y * 2), pat[0])
                    draw_B.point((x * 2 + 1, y * 2), pat[1])
                    draw_B.point((x * 2, y * 2 + 1), pat[2])
                    draw_B.point((x * 2 + 1, y * 2 + 1), pat[3])

        out_A = BytesIO()
        share_A.save(out_A, 'PNG', transparency=1)
        share_A.close()
        out_A.seek(0)
        out_B = BytesIO()
        share_B.save(out_B, 'PNG', transparency=1)
        share_B.close()
        out_B.seek(0)
        return (out_A, out_B)


def dec(shares: Tuple[BytesIO, BytesIO]) -> BytesIO:
    share_A = Image.open(shares[0])
    share_B = Image.open(shares[1])

    if share_A.size != share_B.size:
        raise ValueError('Shares must have the same size!')

    secret = Image.new('1', share_A.size)
    secret_draw = ImageDraw.Draw(secret)

    for x in range(secret.size[0]):
        for y in range(secret.size[1]):
            p1 = share_A.getpixel((x, y)) & 1
            p2 = share_B.getpixel((x, y)) & 1
            secret_draw.point((x, y), p1 & p2)

    share_A.close()
    share_B.close()

    out = BytesIO()
    secret.save(out, 'PNG')
    secret.close()
    out.seek(0)
    return out
