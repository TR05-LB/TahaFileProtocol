import argparse
import socket
from pathlib import Path
from uuid import uuid4

from tfp.checksum import calculate_sha256
from tfp.protocol import (
    PROTOCOL_NAME,
    PROTOCOL_VERSION,
    SUPPORTED_FEATURES,
    MessageType,
    ProtocolError,
    decode_error,
    decode_json,
    encode_json,
    read_packet,
    send_packet,
)




CHUNK_SIZE = 64 * 1024


def wait_for_ack(sock):
    message_type, payload = read_packet(sock)

    if message_type == MessageType.ERROR:
        error = decode_error(payload)
        raise ProtocolError(f"{error['code']}: {error['message']}")

    if message_type != MessageType.ACK:
        raise ProtocolError(f"expected ACK, got {message_type.name}")

    if payload:
        return decode_json(payload)

    return {}




def send_file(file_path, host, port, progress_callback=None):

    file_path = Path(file_path)

    if not file_path.is_file():
        raise FileNotFoundError(f"file does not exist: {file_path}")

    file_size = file_path.stat().st_size
    file_sha256 = calculate_sha256(file_path)

    transfer_id = str(uuid4())

    file_info = {
        "transfer_id": transfer_id,
        "filename": file_path.name,
        "size": file_size,
        "sha256": file_sha256,
    }

    hello = {
        "protocol": PROTOCOL_NAME,
        "version": PROTOCOL_VERSION,
        "features": SUPPORTED_FEATURES,
        "transfer_id": transfer_id,
    }


    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))

        send_packet(sock, MessageType.HELLO, encode_json(hello))
        ack = wait_for_ack(sock)

        if not ack.get("accepted"):
            raise ProtocolError(f"receiver rejected transfer: {ack}")


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
                if progress_callback is not None:
                    progress_callback(bytes_sent, file_size)
                else:
                    print(f"Sent {bytes_sent}/{file_size} bytes", end="\r")


        send_packet(sock, MessageType.FILE_END)
        wait_for_ack(sock)


    print()
    print(f"Sent {file_path}")
    print(f"Size: {file_size} bytes")
    print(f"SHA-256: {file_sha256}")
    print(f"Transfer ID: {transfer_id}")



def main():
    parser = argparse.ArgumentParser(description="Send a file using TFP")
    parser.add_argument("file")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)

    args = parser.parse_args()

    send_file(args.file, args.host, args.port)


if __name__ == "__main__":
    main()
