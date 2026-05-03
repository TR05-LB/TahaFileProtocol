# Taha File Protocol

Taha File Protocol or TFP, is a learning project for building a custom file transfer protocol over TCP using Python.

The goal is to understand how application protocols are made

## What This Project Does

TFP lets one computer send a file to another computer using a simple custom protocol.

It supports:

- TCP socket communication
- Custom packet headers
- Message types such as `HELLO`, `FILE_INFO`, `FILE_CHUNK`, `FILE_END`, and `ACK`
- File transfer in chunks
- SHA-256 checksum verification
- Command-line sender and receiver tools

## Project Structure

```text
TahaFileProtocol/
  tfp/
    protocol.py
    sender.py
    receiver.py
    checksum.py
    __init__.py
  tests/
    test_protocol.py
  pyproject.toml
  README.md
  LICENSE
