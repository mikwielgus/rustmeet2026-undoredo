import os
import re
import subprocess
import sys
import tempfile


def detect_title(chunk_lines):
    i = 0
    while i < len(chunk_lines) and chunk_lines[i].strip() == "":
        i += 1
    if (
        i + 1 < len(chunk_lines)
        and chunk_lines[i].strip() != ""
        and re.match(r"^-{3,}\s*$", chunk_lines[i + 1])
    ):
        return chunk_lines[i].strip(), chunk_lines[:i] + chunk_lines[i + 2 :]
    return None, chunk_lines


def preprocess(text):
    lines = text.split("\n")

    frontmatter = ""
    body_start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                frontmatter = "\n".join(lines[: i + 1])
                body_start = i + 1
                break

    body = "\n".join(lines[body_start:])

    out = []
    if frontmatter:
        out.append(frontmatter)

    for chunk in re.split(r"(?m)^<!--\s*end_slide\s*-->\s*$", body):
        title, rest = detect_title(chunk.split("\n"))
        rest_text = "\n".join(rest)
        rest_text = re.sub(r"(?m)^<!--\s*jump_to_middle\s*-->\s*$", "", rest_text)
        rest_text = re.sub(r"(?m)^([^\n]+)\n-{3,}\s*$", r"### \1", rest_text)

        if title is None and rest_text.strip() == "":
            continue

        head = "## " + (title if title else "\u00a0")
        for fragment in re.split(r"(?m)^<!--\s*pause\s*-->\s*$", rest_text):
            fragment = fragment.strip()
            if fragment == "":
                continue
            out.append(head + "\n\n" + fragment + "\n")

    return "\n\n".join(out) + "\n"


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: presenterm_to_pptx.py <input.md> <output.pptx>")

    src, dst = sys.argv[1], sys.argv[2]
    resource_path = os.path.dirname(os.path.abspath(src)) or "."

    with open(src, encoding="utf-8") as f:
        preprocessed = preprocess(f.read())

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(preprocessed)
        tmp_path = tmp.name

    try:
        subprocess.run(
            ["pandoc", tmp_path, "-o", dst, "--resource-path", resource_path],
            check=True,
        )
    finally:
        os.unlink(tmp_path)

    print(f"wrote {dst}")


if __name__ == "__main__":
    main()
