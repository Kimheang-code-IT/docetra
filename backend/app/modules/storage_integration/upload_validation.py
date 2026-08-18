from io import BytesIO
from zipfile import BadZipFile, ZipFile

from fastapi import HTTPException


def detect_upload_type(content: bytes, extension: str) -> str:
    if not content:
        raise HTTPException(422, "Empty files are not allowed")
    if content.startswith((b"MZ", b"\x7fELF")):
        raise HTTPException(415, "Executable files are not allowed")
    signatures = [
        (b"%PDF-", "application/pdf", {"pdf"}),
        (b"\x89PNG\r\n\x1a\n", "image/png", {"png"}),
        (b"\xff\xd8\xff", "image/jpeg", {"jpg", "jpeg"}),
        (b"GIF87a", "image/gif", {"gif"}),
        (b"GIF89a", "image/gif", {"gif"}),
    ]
    for signature, mime, extensions in signatures:
        if content.startswith(signature):
            if extension not in extensions:
                raise HTTPException(415, "File content does not match its extension")
            return mime
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        if extension != "webp":
            raise HTTPException(415, "File content does not match its extension")
        return "image/webp"
    if extension in {"docx", "xlsx"}:
        try:
            with ZipFile(BytesIO(content)) as archive:
                names = archive.namelist()
                if len(names) > 10_000 or sum(item.file_size for item in archive.infolist()) > 250 * 1024 * 1024:
                    raise HTTPException(413, "Compressed document expands beyond the safety limit")
                required = "word/" if extension == "docx" else "xl/"
                if not any(name.startswith(required) for name in names):
                    raise HTTPException(415, "Office document content does not match its extension")
        except BadZipFile as exc:
            raise HTTPException(415, "Invalid Office document") from exc
        if extension == "docx":
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if extension in {"txt", "csv"}:
        try:
            content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise HTTPException(415, "Text uploads must use UTF-8") from exc
        return "text/csv" if extension == "csv" else "text/plain"
    raise HTTPException(415, "Unsupported or unrecognized file content")
