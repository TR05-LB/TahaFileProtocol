import json
import struct
from enum import IntEnum


MAGIC = b"TFP1"
HEADER_FORMAT = "!4sBQ"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
MAX_PAYLOAD_SIZE = 16 * 1024 * 1024


class MessageType(IntEnum):
    HELLO = 1
    FILE_INFO = 2
    FILE_CHUNK = 3
    FILE_END = 4
    ACK = 5
    ERROR = 6


class ProtocolError(Exception):
    pass


def encode_packet(message_type, payload=b""):
    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")

    if len(payload) > MAX_PAYLOAD_SIZE:
        raise ProtocolError("payload is too large")

    header = struct.pack(
        HEADER_FORMAT,
        MAGIC,
        int(message_type),
        len(payload),
    )

    return header + payload


def decode_header(header):
    if len(header) != HEADER_SIZE:
        raise ProtocolError("incomplete header")

    magic, message_type, payload_length = struct.unpack(HEADER_FORMAT, header)

    if magic != MAGIC:
        raise ProtocolError("invalid protocol magic")

    if payload_length > MAX_PAYLOAD_SIZE:
        raise ProtocolError("payload is too large")

    try:
        message_type = MessageType(message_type)
    except ValueError:
        raise ProtocolError("unknown message type")

    return message_type, payload_length


def read_exact(sock, size):
    chunks = []
    remaining = size

    while remaining > 0:
        chunk = sock.recv(remaining)

        if chunk == b"":
            raise ProtocolError("connection closed early")

        chunks.append(chunk)
        remaining -= len(chunk)

    return b"".join(chunks)


def send_packet(sock, message_type, payload=b""):
    packet = encode_packet(message_type, payload)
    sock.sendall(packet)


def read_packet(sock):
    header = read_exact(sock, HEADER_SIZE)
    message_type, payload_length = decode_header(header)
    payload = read_exact(sock, payload_length)

    return message_type, payload


def encode_json(data):
    text = json.dumps(data)
    return text.encode("utf-8")


def decode_json(payload):
    text = payload.decode("utf-8")
    return json.loads(text)
