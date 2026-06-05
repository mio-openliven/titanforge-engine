from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct
import zlib


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

_MAX_DIMENSION = 16384
_MAX_DECOMPRESSED = 256 * 1024 * 1024  # 256 MiB


class PngError(ValueError):
    """Raised when a PNG file cannot be decoded by TitanForge's minimal reader."""


@dataclass(frozen=True)
class PngImage:
    width: int
    height: int
    pixels: tuple[tuple[tuple[int, int, int, int], ...], ...]


def read_png(path: Path) -> PngImage:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise PngError(f"Not a PNG file: {path}")

    width: int | None = None
    height: int | None = None
    bit_depth: int | None = None
    color_type: int | None = None
    interlace: int | None = None
    palette: tuple[tuple[int, int, int], ...] = ()
    transparency = b""
    compressed = bytearray()

    offset = len(PNG_SIGNATURE)
    while offset < len(data):
        if offset + 8 > len(data):
            raise PngError("Truncated PNG chunk header.")

        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_start = offset + 8
        chunk_end = chunk_start + length
        offset = chunk_end + 4

        if offset > len(data):
            raise PngError("Truncated PNG chunk body.")

        chunk_data = data[chunk_start:chunk_end]
        if chunk_type == b"IHDR":
            if len(chunk_data) != 13:
                raise PngError("Malformed IHDR chunk.")
            try:
                width, height, bit_depth, color_type, _compression, _filter, interlace = struct.unpack(
                    ">IIBBBBB", chunk_data
                )
            except struct.error as exc:
                raise PngError("Malformed IHDR chunk.") from exc
        elif chunk_type == b"PLTE":
            palette = tuple(
                tuple(chunk_data[index : index + 3])  # type: ignore[misc]
                for index in range(0, len(chunk_data), 3)
            )
        elif chunk_type == b"tRNS":
            transparency = chunk_data
        elif chunk_type == b"IDAT":
            compressed.extend(chunk_data)
        elif chunk_type == b"IEND":
            break

    if width is None or height is None or bit_depth is None or color_type is None:
        raise PngError("PNG file does not contain IHDR.")
    if bit_depth != 8:
        raise PngError("Only 8-bit PNG masks are supported.")
    if interlace:
        raise PngError("Interlaced PNG masks are not supported.")
    if color_type not in (0, 2, 3, 6):
        raise PngError(f"Unsupported PNG color type: {color_type}")
    if color_type == 3 and not palette:
        raise PngError("Indexed PNG mask is missing a palette.")
    if width <= 0 or height <= 0 or width > _MAX_DIMENSION or height > _MAX_DIMENSION:
        raise PngError(f"PNG dimensions out of range: {width}x{height}")

    bytes_per_pixel = _bytes_per_pixel(color_type)
    row_size = width * bytes_per_pixel
    expected_size = (row_size + 1) * height
    if expected_size > _MAX_DECOMPRESSED:
        raise PngError("PNG image data exceeds maximum supported size.")

    try:
        dec = zlib.decompressobj()
        raw = dec.decompress(compressed, expected_size + 1)
    except zlib.error as exc:
        raise PngError("PNG image data could not be decompressed.") from exc
    if len(raw) != expected_size or dec.unconsumed_tail or dec.unused_data or not dec.eof:
        raise PngError("PNG image data has an unexpected size.")

    rows: list[bytes] = []
    previous = bytes(row_size)
    cursor = 0
    for _y in range(height):
        filter_type = raw[cursor]
        cursor += 1
        scanline = raw[cursor : cursor + row_size]
        cursor += row_size
        unfiltered = _unfilter_scanline(filter_type, scanline, previous, bytes_per_pixel)
        rows.append(unfiltered)
        previous = unfiltered

    pixels = tuple(_decode_row(row, width, color_type, palette, transparency) for row in rows)
    return PngImage(width=width, height=height, pixels=pixels)


def write_rgba_png(path: Path, width: int, height: int, pixels: tuple[tuple[tuple[int, int, int, int], ...], ...]) -> None:
    if len(pixels) != height:
        raise PngError("Pixel row count does not match image height.")
    for row in pixels:
        if len(row) != width:
            raise PngError("Pixel column count does not match image width.")

    raw = bytearray()
    for row in pixels:
        raw.append(0)
        for red, green, blue, alpha in row:
            raw.extend((red, green, blue, alpha))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    data = bytearray(PNG_SIGNATURE)
    data.extend(_chunk(b"IHDR", ihdr))
    data.extend(_chunk(b"IDAT", zlib.compress(bytes(raw))))
    data.extend(_chunk(b"IEND", b""))
    path.write_bytes(bytes(data))


def _bytes_per_pixel(color_type: int) -> int:
    return {
        0: 1,
        2: 3,
        3: 1,
        6: 4,
    }[color_type]


def _unfilter_scanline(filter_type: int, scanline: bytes, previous: bytes, bytes_per_pixel: int) -> bytes:
    result = bytearray(scanline)

    for index, value in enumerate(scanline):
        left = result[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
        up = previous[index]
        upper_left = previous[index - bytes_per_pixel] if index >= bytes_per_pixel else 0

        if filter_type == 0:
            result[index] = value
        elif filter_type == 1:
            result[index] = (value + left) & 0xFF
        elif filter_type == 2:
            result[index] = (value + up) & 0xFF
        elif filter_type == 3:
            result[index] = (value + ((left + up) // 2)) & 0xFF
        elif filter_type == 4:
            result[index] = (value + _paeth(left, up, upper_left)) & 0xFF
        else:
            raise PngError(f"Unsupported PNG filter type: {filter_type}")

    return bytes(result)


def _decode_row(
    row: bytes,
    width: int,
    color_type: int,
    palette: tuple[tuple[int, int, int], ...],
    transparency: bytes,
) -> tuple[tuple[int, int, int, int], ...]:
    pixels: list[tuple[int, int, int, int]] = []

    if color_type == 0:
        transparent_value = transparency[1] if len(transparency) >= 2 else None
        for value in row:
            alpha = 0 if value == transparent_value else 255
            pixels.append((value, value, value, alpha))
    elif color_type == 2:
        transparent = _truecolor_transparency(transparency)
        for index in range(0, width * 3, 3):
            rgb = tuple(row[index : index + 3])
            alpha = 0 if rgb == transparent else 255
            pixels.append((rgb[0], rgb[1], rgb[2], alpha))
    elif color_type == 3:
        for palette_index in row[:width]:
            if palette_index >= len(palette):
                raise PngError(
                    f"Palette index {palette_index} out of range ({len(palette)} entries)."
                )
            red, green, blue = palette[palette_index]
            alpha = transparency[palette_index] if palette_index < len(transparency) else 255
            pixels.append((red, green, blue, alpha))
    elif color_type == 6:
        for index in range(0, width * 4, 4):
            red, green, blue, alpha = row[index : index + 4]
            pixels.append((red, green, blue, alpha))

    return tuple(pixels)


def _truecolor_transparency(transparency: bytes) -> tuple[int, int, int] | None:
    if len(transparency) < 6:
        return None
    red, green, blue = struct.unpack(">HHH", transparency[:6])
    if red > 255 or green > 255 or blue > 255:
        return None
    return (red, green, blue)


def _paeth(left: int, up: int, upper_left: int) -> int:
    estimate = left + up - upper_left
    distance_left = abs(estimate - left)
    distance_up = abs(estimate - up)
    distance_upper_left = abs(estimate - upper_left)

    if distance_left <= distance_up and distance_left <= distance_upper_left:
        return left
    if distance_up <= distance_upper_left:
        return up
    return upper_left


def _chunk(chunk_type: bytes, payload: bytes) -> bytes:
    checksum = zlib.crc32(chunk_type)
    checksum = zlib.crc32(payload, checksum)
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", checksum & 0xFFFFFFFF)
