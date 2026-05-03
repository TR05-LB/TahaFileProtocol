import argparse
import socket
from pathlib import Path

from tfp.checksum import calculate_sha256
from tfp.protocol import (
    MessageType,
    ProtocolError,
    encode_json,
    read_packet,
    send_packet,
)


CHUNK_SIZE = 64 * 1024


def wait_for_ack(sock):
    message_type, payload = read_packet(sock)

    if message_type != MessageType.ACK:
        raise ProtocolError(f"expected ACK, got {message_type.name}")

    return payload


def send_file(file_path, host, port):
    file_path = Path(file_path)

    if not file_path.is_file():
        raise FileNotFoundError(f"file does not exist: {file_path}")

    file_size = file_path.stat().st_size
    file_sha256 = calculate_sha256(file_path)

    file_info = {
        "filename": file_path.name,
        "size": file_size,
        "sha256": file_sha256,
    }

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))

        send_packet(sock, MessageType.HELLO)
        wait_for_ack(sock)

        send_packet(sock, MessageType.FILE_INFO, encode_json(file_info))
        wait_for_ack(sock)

        bytes_sent = 0

        with open(file_path, "rb") as file:
            while True:
                chunk = file.read(CHUNK_SIZE)

                if chunk == b"":
                    break

                send_packet(sock, MessageType.FILE_CHUNK, chunk)
                wait_for_ack(sock)

                bytes_sent += len(chunk)
                print(f"Sent {bytes_sent}/{file_size} bytes", end="\r")

        send_packet(sock, MessageType.FILE_END)
        wait_for_ack(sock)

    print()
    print(f"Sent {file_path}")
    print(f"Size: {file_size} bytes")
    print(f"SHA-256: {file_sha256}")


def main():
    parser = argparse.ArgumentParser(description="Send a file using TFP")
    parser.add_argument("file")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)

    args = parser.parse_args()

    send_file(args.file, args.host, args.port)


if __name__ == "__main__":
    main()
