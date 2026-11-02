import sys
import json
import re
import urllib.request
import urllib.error
from packaging.specifiers import SpecifierSet
from packaging.version import Version, InvalidVersion

TARGET_PYTHON = "3.11"

def fetch_json(url: str):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PyPI-Checker/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    return None

def extract_min_python_version(specifier_set: SpecifierSet):
    min_ver = None
    for spec in specifier_set:
        if spec.operator in (">=", ">", "=="):
            try:
                v = Version(spec.version)
                if min_ver is None or v > min_ver:
                    min_ver = v
            except InvalidVersion:
                continue
    return min_ver

def parse_line(line: str):
    match = re.split(r"={1,2}", line.strip())
    if len(match) == 2:
        return match[0].strip(), match[1].strip()
    return None, None

def run():
    target_file = sys.argv[1] if len(sys.argv) > 1 else "requirements.txt"
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    except FileNotFoundError:
        lines = []

    dependencies_checked = len(lines)
    not_found_count = 0
    incompatible_count = 0

    highest_min_version = None
    highest_req_text = "None"

    for line in lines:
        pkg_name, pinned_ver = parse_line(line)

        if not pkg_name or not pinned_ver:
            not_found_count += 1
            continue

        url = f"https://pypi.org/pypi/{pkg_name}/{pinned_ver}/json"
        data = fetch_json(url)

        if data is None:
            not_found_count += 1
            continue

        info = data.get("info", {})
        requires_python = info.get("requires_python")

        if requires_python:
            try:
                spec = SpecifierSet(requires_python)
                if TARGET_PYTHON not in spec:
                    incompatible_count += 1

                min_v = extract_min_python_version(spec)
                if min_v:
                    if highest_min_version is None or min_v > highest_min_version:
                        highest_min_version = min_v
                        highest_req_text = f"{pkg_name}=={pinned_ver} ({requires_python})"
            except Exception:
                pass

    print(f"Dependencies checked: {dependencies_checked}")
    print(f"Not found on PyPI: {not_found_count}")
    print(f"Incompatible with Python 3.11: {incompatible_count}")
    print(f"Highest requirement: {highest_req_text}")

if __name__ == "__main__":
    run()
    
# requests==2.31.0
# django==6.0
# numpy=1.21.6
# flask==3.0.0
# langchain-pdf-agent==0.3.1