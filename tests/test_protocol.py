import pytest
import struct

from tfp.protocol import (
    HEADER_SIZE,
    MAGIC,
    MessageType,
    ProtocolError,
    decode_header,
    decode_json,
    encode_json,
    encode_packet,
)


def test_encode_packet_contains_header_and_payload():
    payload = b"hello"

    packet = encode_packet(MessageType.HELLO, payload)

    assert packet.startswith(MAGIC)
    assert len(packet) == HEADER_SIZE + len(payload)
    assert packet[HEADER_SIZE:] == payload


def test_decode_header_reads_message_type_and_payload_length():
    payload = b"abc"
    packet = encode_packet(MessageType.FILE_CHUNK, payload)

    header = packet[:HEADER_SIZE]

    message_type, payload_length = decode_header(header)

    assert message_type == MessageType.FILE_CHUNK
    assert payload_length == 3


def test_decode_header_rejects_bad_magic():
    packet = encode_packet(MessageType.HELLO, b"")
    bad_packet = b"BAD!" + packet[4:]

    with pytest.raises(ProtocolError):
        decode_header(bad_packet[:HEADER_SIZE])


def test_json_encoding_round_trip():
    data = {
        "filename": "example.txt",
        "size": 123,
        "sha256": "abc123",
    }

    payload = encode_json(data)
    result = decode_json(payload)

    assert result == data

def test_encode_packet_rejects_non_bytes_payload():
    with pytest.raises(TypeError):
        encode_packet(MessageType.HELLO, payload="not bytes")

def test_encode_packet_rejects_oversize_payload():
    payload = b"a" * (16 * 1024 * 1024 + 1)  # 16MB + 1 byte

    with pytest.raises(ProtocolError):
        encode_packet(MessageType.HELLO, payload)

def test_decode_header_rejects_incomplete_header():
    incomplete_header = b"TFP1\x01\x00\x00"  # Only 7 bytes instead of HEADER_SIZE

    with pytest.raises(ProtocolError):
        decode_header(incomplete_header)

def test_decode_header_rejects_unknown_message_type():
    packet = encode_packet(99, b"")  # 99 is not a valid MessageType
    header = packet[:HEADER_SIZE]

    with pytest.raises(ProtocolError):
        decode_header(header)

def test_decode_header_rejects_oversize_payload():
    # Create a header with a valid magic and message type but an oversize payload length
    header = struct.pack(
        "!4sBQ",
        MAGIC,
        int(MessageType.HELLO),
        16 * 1024 * 1024 + 1,  # 16MB + 1 byte
    )

    with pytest.raises(ProtocolError):
        decode_header(header)

