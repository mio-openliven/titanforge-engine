from __future__ import annotations

import io
import struct
from typing import Any


TAG_END = 0
TAG_BYTE = 1
TAG_INT = 3
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10


def write_nbt(name: str, payload: dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    _write_tag_header(buffer, TAG_COMPOUND, name)
    _write_compound_payload(buffer, payload)
    return buffer.getvalue()


def read_nbt(data: bytes) -> tuple[str, dict[str, Any]]:
    buffer = io.BytesIO(data)
    tag_type = _read_ubyte(buffer)
    if tag_type != TAG_COMPOUND:
        raise ValueError(f"Expected root compound tag, got {tag_type}.")
    name = _read_string(buffer)
    payload = _read_compound_payload(buffer)
    return name, payload


def _write_named_tag(buffer: io.BytesIO, name: str, value: Any) -> None:
    tag_type = _infer_tag_type(value)
    _write_tag_header(buffer, tag_type, name)
    _write_payload(buffer, tag_type, value)


def _write_tag_header(buffer: io.BytesIO, tag_type: int, name: str) -> None:
    buffer.write(struct.pack(">B", tag_type))
    _write_string(buffer, name)


def _write_payload(buffer: io.BytesIO, tag_type: int, value: Any) -> None:
    if tag_type == TAG_BYTE:
        buffer.write(struct.pack(">b", 1 if value else 0))
        return
    if tag_type == TAG_INT:
        buffer.write(struct.pack(">i", int(value)))
        return
    if tag_type == TAG_STRING:
        _write_string(buffer, str(value))
        return
    if tag_type == TAG_LIST:
        _write_list_payload(buffer, value)
        return
    if tag_type == TAG_COMPOUND:
        _write_compound_payload(buffer, value)
        return
    raise ValueError(f"Unsupported NBT tag type: {tag_type}")


def _write_list_payload(buffer: io.BytesIO, items: list[Any]) -> None:
    if not items:
        buffer.write(struct.pack(">Bi", TAG_END, 0))
        return
    item_type = _infer_tag_type(items[0])
    buffer.write(struct.pack(">Bi", item_type, len(items)))
    for item in items:
        if _infer_tag_type(item) != item_type:
            raise ValueError("NBT lists must be homogeneous.")
        _write_payload(buffer, item_type, item)


def _write_compound_payload(buffer: io.BytesIO, payload: dict[str, Any]) -> None:
    for name, value in payload.items():
        _write_named_tag(buffer, name, value)
    buffer.write(struct.pack(">B", TAG_END))


def _write_string(buffer: io.BytesIO, value: str) -> None:
    encoded = value.encode("utf-8")
    buffer.write(struct.pack(">H", len(encoded)))
    buffer.write(encoded)


def _read_named_tag(buffer: io.BytesIO) -> tuple[int, str, Any]:
    tag_type = _read_ubyte(buffer)
    if tag_type == TAG_END:
        return tag_type, "", None
    name = _read_string(buffer)
    value = _read_payload(buffer, tag_type)
    return tag_type, name, value


def _read_payload(buffer: io.BytesIO, tag_type: int) -> Any:
    if tag_type == TAG_BYTE:
        return bool(struct.unpack(">b", buffer.read(1))[0])
    if tag_type == TAG_INT:
        return struct.unpack(">i", buffer.read(4))[0]
    if tag_type == TAG_STRING:
        return _read_string(buffer)
    if tag_type == TAG_LIST:
        return _read_list_payload(buffer)
    if tag_type == TAG_COMPOUND:
        return _read_compound_payload(buffer)
    raise ValueError(f"Unsupported NBT tag type: {tag_type}")


def _read_list_payload(buffer: io.BytesIO) -> list[Any]:
    item_type = _read_ubyte(buffer)
    length = struct.unpack(">i", buffer.read(4))[0]
    return [_read_payload(buffer, item_type) for _index in range(length)]


def _read_compound_payload(buffer: io.BytesIO) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    while True:
        tag_type, name, value = _read_named_tag(buffer)
        if tag_type == TAG_END:
            break
        payload[name] = value
    return payload


def _read_string(buffer: io.BytesIO) -> str:
    length = struct.unpack(">H", buffer.read(2))[0]
    return buffer.read(length).decode("utf-8")


def _read_ubyte(buffer: io.BytesIO) -> int:
    return struct.unpack(">B", buffer.read(1))[0]


def _infer_tag_type(value: Any) -> int:
    if isinstance(value, bool):
        return TAG_BYTE
    if isinstance(value, int):
        return TAG_INT
    if isinstance(value, str):
        return TAG_STRING
    if isinstance(value, list):
        return TAG_LIST
    if isinstance(value, dict):
        return TAG_COMPOUND
    raise ValueError(f"Unsupported NBT value type: {type(value)!r}")
