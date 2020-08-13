from io import BytesIO
from PIL import Image, ImageDraw
from PIL.PngImagePlugin import PngInfo
from typing import Tuple

components = {
    'R': ((4, 4), (4, 2), (3, 1), (2, 3), (2, 0), (1, 4), (1, 2), (0, 1)),
    'G': ((4, 3), (3, 4), (3, 2), (2, 1), (1, 3), (1, 0), (0, 4), (0, 2)),
    'B': ((4, 1), (3, 3), (3, 0), (2, 4), (2, 2), (1, 1), (0, 3), (0, 0))
}


def _enc_bit(secret_bit: bool) -> Tuple[int, int, int]:
    return (0, 0, 0) if secret_bit else (30, 30, 30)


def _dec_bit(secret_pixel: Tuple[int, int, int]) -> bool:
    return secret_pixel == (0, 0, 0)


def enc_nn(inputs: Tuple[BytesIO, BytesIO, BytesIO, BytesIO]) -> Tuple[BytesIO, BytesIO, BytesIO]:
    with Image.open(inputs[0]) as secret:
        # Enforce RGB mode
        if secret.mode != 'RGB':
            secret = secret.convert('RGB')

        covers = []
        for cover in inputs[1:]:
            cover_img = Image.open(cover)
            if secret.size != cover_img.size:
                raise ValueError('Secret and covers must have the same size!')
            covers.append(cover_img)

        share_size = tuple(dim * 5 for dim in secret.size)
        shares = tuple(Image.new('RGB', share_size)
                       for _ in range(len(covers)))

        width, height = secret.size
        x = 0
        for i in range(width):
            y = 0
            for j in range(height):
                secret_pixel = secret.getpixel((i, j))
                for index, channel in enumerate(components.keys()):
                    cover_pixel = covers[index].getpixel((i, j))
                    with Image.new('RGB', (5, 5), cover_pixel) as block:
                        block_draw = ImageDraw.Draw(block)
                        for b, cell in enumerate(components[channel]):
                            block_draw.point(cell,
                                             _enc_bit(secret_pixel[index] >> b & 1))
                        shares[index].paste(block, (x, y, x + 5, y + 5))
                y += 5
            x += 5

        out = tuple(BytesIO() for _ in range(len(shares)))
        for i, ch in enumerate(components.keys()):
            # CH tells which channel is encrypted in this share
            ch_info = PngInfo()
            ch_info.add_text('CH', ch)
            shares[i].save(out[i], 'PNG', pnginfo=ch_info)
            shares[i].close()
            covers[i].close()
            out[i].seek(0)

        return out


def dec_nn(inputs: Tuple[BytesIO, BytesIO, BytesIO]) -> BytesIO:
    covers = []
    for cover in inputs:
        img_cover = Image.open(cover)
        if 'CH' not in img_cover.info:
            raise Exception('Missing metadata info in share!')
        covers.append(img_cover)

    cover_size = covers[0].size
    if not all(cover.size == cover_size for cover in covers):
        raise ValueError('Covers must have the same size!')

    secret_size = tuple(s // 5 for s in cover_size)
    width, height = cover_size
    out = BytesIO()
    with Image.new('RGB', secret_size) as secret:
        secret_draw = ImageDraw.Draw(secret)
        for cover in covers:
            ch = cover.info['CH']
            ch_index = 0 if ch == 'R' else 1 if ch == 'G' else 2
            x = 0
            for i in range(0, width, 5):
                y = 0
                for j in range(0, height, 5):
                    sub = cover.crop((i, j, i + 5, j + 5))
                    color = 0
                    for b, cell in enumerate(components[ch]):
                        color |= _dec_bit(sub.getpixel(cell)) << b
                    s_color = list(secret.getpixel((x, y)))
                    s_color[ch_index] = color
                    secret_draw.point((x, y), tuple(s_color))
                    y += 1
                x += 1
        secret.save(out, 'PNG')

    for cover in covers:
        cover.close()

    out.seek(0)
    return out


def enc_kn(inputs: Tuple[BytesIO, BytesIO, BytesIO, BytesIO]) -> Tuple[BytesIO, BytesIO, BytesIO]:
    with Image.open(inputs[0]) as secret:
        # Enforce RGB mode
        if secret.mode != 'RGB':
            secret = secret.convert('RGB')

        covers = []
        for cover in inputs[1:]:
            cover_img = Image.open(cover)
            if secret.size != cover_img.size:
                raise ValueError('Secret and covers must have the same size!')
            covers.append(cover_img)

        share_size = tuple(s * 5 for s in secret.size)
        shares = tuple(Image.new('RGB', share_size)
                       for _ in range(len(covers)))

        width, height = secret.size
        x = 0
        for i in range(width):
            y = 0
            for j in range(height):
                secret_pixel = secret.getpixel((i, j))

                with Image.new('RGB', (5, 5)) as block:
                    block_draw = ImageDraw.Draw(block)
                    for index, channel in enumerate(components.keys()):
                        for b, cell in enumerate(components[channel]):
                            secret_bit = secret_pixel[index] >> b & 1
                            block_draw.point(cell, _enc_bit(secret_bit))

                    for cover_index, cover in enumerate(covers):
                        channel = tuple(components.keys())[cover_index]
                        cover_pixel = cover.getpixel((i, j))
                        cover_block = block.copy()
                        cover_block_draw = ImageDraw.Draw(cover_block)
                        cover_block_draw.point((4, 0), cover_pixel)
                        for cell in components[channel]:
                            cover_block_draw.point(cell, cover_pixel)
                        shares[cover_index].paste(
                            cover_block, (x, y, x + 5, y + 5))

                y += 5
            x += 5

        out = tuple(BytesIO() for _ in range(len(shares)))
        for i, ch in enumerate(components.keys()):
            # MISSING tells which channel is not encrypted in this share
            ch_info = PngInfo()
            ch_info.add_text('MISSING', ch)
            shares[i].save(out[i], 'PNG', pnginfo=ch_info)
            shares[i].close()
            cover.close()
            out[i].seek(0)

        return out


def dec_kn(inputs: Tuple[BytesIO, BytesIO]) -> BytesIO:
    covers = []
    for cover in inputs:
        img_cover = Image.open(cover)
        if 'MISSING' not in img_cover.info:
            raise Exception('Missing metadata info in share!')
        covers.append(img_cover)

    cover_size = covers[0].size
    if not all(cover.size == cover_size for cover in covers):
        raise ValueError('Covers must have the same size!')

    width, height = cover_size
    for cover in covers:
        channel = cover.info['MISSING']
        for i in range(0, width, 5):
            for j in range(0, height, 5):
                sub = cover.crop((i, j, i + 5, j + 5))
                sub_draw = ImageDraw.Draw(sub)
                sub_draw.point((4, 0), (0, 0, 0))
                for cell in components[channel]:
                    sub_draw.point(cell, (0, 0, 0))
                cover.paste(sub, (i, j, i + 5, j + 5))

    out = BytesIO()
    with Image.new('RGB', cover_size) as middle:
        middle_draw = ImageDraw.Draw(middle)
        for i in range(width):
            for j in range(height):
                c1 = covers[0].getpixel((i, j))
                c2 = covers[1].getpixel((i, j))
                c3 = tuple(map(lambda x, y: x | y, c1, c2))
                middle_draw.point((i, j), c3)

        with Image.new('RGB', tuple(s // 5 for s in cover_size)) as secret:
            i = 0
            for x in range(0, width, 5):
                j = 0
                for y in range(0, height, 5):
                    sub = middle.crop((x, y, x + 5, y + 5))
                    secret_color = [0, 0, 0]
                    for index, channel in enumerate(components.keys()):
                        for b, cell in enumerate(components[channel]):
                            secret_color[index] |= _dec_bit(
                                sub.getpixel(cell)) << b
                    secret.putpixel((i, j), tuple(secret_color))

                    j += 1
                i += 1
            secret.save(out, 'PNG')

    out.seek(0)
    return out
