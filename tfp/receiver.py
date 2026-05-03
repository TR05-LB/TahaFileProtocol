import argparse
import socket
from pathlib import Path

from tfp.checksum import calculate_sha256
from tfp.protocol import (
    MessageType,
    ProtocolError,
    decode_json,
    send_packet,
    read_packet,
)


def expect_packet(sock, expected_type):
    message_type, payload = read_packet(sock)

    if message_type != expected_type:
        raise ProtocolError(
            f"expected {expected_type.name}, got {message_type.name}"
        )

    return payload


def receive_file(host, port, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(1)

        print(f"Receiver listening on {host}:{port}")

        conn, address = server.accept()

        with conn:
            print(f"Connection from {address[0]}:{address[1]}")

            expect_packet(conn, MessageType.HELLO)
            send_packet(conn, MessageType.ACK)

            file_info_payload = expect_packet(conn, MessageType.FILE_INFO)
            file_info = decode_json(file_info_payload)

            filename = Path(file_info["filename"]).name
            expected_size = file_info["size"]
            expected_sha256 = file_info["sha256"]

            output_path = output_dir / filename

            send_packet(conn, MessageType.ACK)

            bytes_received = 0

            with open(output_path, "wb") as file:
                while True:
                    message_type, payload = read_packet(conn)

                    if message_type == MessageType.FILE_CHUNK:
                        file.write(payload)
                        bytes_received += len(payload)
                        send_packet(conn, MessageType.ACK)

                    elif message_type == MessageType.FILE_END:
                        send_packet(conn, MessageType.ACK)
                        break

                    else:
                        raise ProtocolError(
                            f"unexpected message type: {message_type.name}"
                        )

            if bytes_received != expected_size:
                raise ProtocolError(
                    f"file size mismatch: expected {expected_size}, got {bytes_received}"
                )

            actual_sha256 = calculate_sha256(output_path)

            if actual_sha256 != expected_sha256:
                raise ProtocolError("checksum mismatch")

            print(f"Received {output_path}")
            print(f"Size: {bytes_received} bytes")
            print(f"SHA-256: {actual_sha256}")


def main():
    parser = argparse.ArgumentParser(description="Receive a file using TFP")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--output", default="downloads")

    args = parser.parse_args()

    receive_file(args.host, args.port, args.output)


if __name__ == "__main__":
    main()
