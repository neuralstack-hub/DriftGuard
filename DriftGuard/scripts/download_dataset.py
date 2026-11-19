"""Download the official Beijing PM2.5 dataset from the UCI Machine Learning Repository."""

import io
import zipfile
from pathlib import Path
from urllib.request import urlopen

UCI_ZIP_URL = "https://archive.ics.uci.edu/static/public/381/beijing+pm2+5+data.zip"
TARGET_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
TARGET_FILE = TARGET_DIR / "PRSA_data_2010.1.1-2014.12.31.csv"


def download_beijing_pm25() -> Path:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    if TARGET_FILE.exists():
        print(f"Dataset already present at: {TARGET_FILE}")
        return TARGET_FILE

    print(f"Downloading Beijing PM2.5 dataset from {UCI_ZIP_URL} ...")
    with urlopen(UCI_ZIP_URL, timeout=60) as response:
        zip_bytes = response.read()

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        csv_members = [m for m in zf.namelist() if m.endswith(".csv")]
        if not csv_members:
            raise RuntimeError("No CSV file found inside downloaded UCI archive.")
        member = csv_members[0]
        with zf.open(member) as src, open(TARGET_FILE, "wb") as dst:
            dst.write(src.read())

    print(f"Successfully saved dataset to: {TARGET_FILE}")
    return TARGET_FILE


if __name__ == "__main__":
    download_beijing_pm25()
