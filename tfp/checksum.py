import hashlib


def calculate_sha256(file_path):
    hasher = hashlib.sha256()

    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(64 * 1024)

            if chunk == b"":
                break

            hasher.update(chunk)

    return hasher.hexdigest()
