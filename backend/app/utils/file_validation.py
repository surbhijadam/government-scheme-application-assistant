import os

ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def get_extension(filename):
    """Return the lowercase file extension, without the dot."""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def is_allowed_extension(filename):
    return get_extension(filename) in ALLOWED_EXTENSIONS


def get_file_size(file_storage):
    """Return a Werkzeug FileStorage's size in bytes without permanently consuming the stream."""
    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    return size