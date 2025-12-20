# src/preprocess.py
import zipfile
import shutil
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# absolute Windows path to zip (raw string is correct)
ZIP_PATH = Path(r"C:\Users\Win\Downloads\archive (2).zip")

# <-- IMPORTANT: output dir expected by train.py
DATA_DIR = ROOT / "data_preprocessed"

# (optional) where the raw zip will be extracted temporarily
EXTRACT_DIR = ROOT / "data_raw"

RATIOS = {"train": 0.7, "val": 0.15, "test": 0.15}
SEED = 42
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".gif"}

def unzip_dataset():
    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"{ZIP_PATH} not found")
    # ensure extract directory exists and is empty
    if EXTRACT_DIR.exists():
        # don't delete automatically - you can uncomment to force clean:
        # shutil.rmtree(EXTRACT_DIR)
        pass
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        z.extractall(EXTRACT_DIR)
    print("Unzipped to", EXTRACT_DIR)

def gather_image_files(class_dir: Path):
    """Return a list of image file Paths found under class_dir (recursive)."""
    files = [p for p in class_dir.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    return files

def create_splits(images_root: Path):
    random.seed(SEED)

    # find class directories (only first-level directories inside images_root)
    classes = [p.name for p in images_root.iterdir() if p.is_dir()]
    print("Found classes:", classes)

    for cls in classes:
        class_dir = images_root / cls
        imgs = gather_image_files(class_dir)
        if not imgs:
            print(f"Warning: no image files found for class '{cls}' (skipping).")
            continue

        random.shuffle(imgs)
        n = len(imgs)
        t = int(RATIOS["train"] * n)
        v = int(RATIOS["val"] * n)
        splits = {
            "train": imgs[:t],
            "val": imgs[t : t + v],
            "test": imgs[t + v :],
        }

        for split, paths in splits.items():
            out_dir = DATA_DIR / split / cls
            out_dir.mkdir(parents=True, exist_ok=True)
            for p in paths:
                # preserve original filename; if duplicates across classes exist, they go into separate folders
                dest = out_dir / p.name
                try:
                    shutil.copy2(p, dest)
                except PermissionError as e:
                    print(f"PermissionError copying {p} -> {dest}: {e}")
                except Exception as e:
                    print(f"Error copying {p} -> {dest}: {e}")

    print("Created train/val/test splits under", DATA_DIR)

def find_images_root_after_extract():
    # list directories under EXTRACT_DIR (dataset root)
    extracted_roots = [p for p in EXTRACT_DIR.iterdir() if p.is_dir()]
    images_root = None

    # Try to find the first directory that contains subdirectories (class folders)
    for cand in extracted_roots:
        subdirs = [x for x in cand.iterdir() if x.is_dir()]
        if subdirs:
            # check if any immediate child folder contains image files
            has_images = False
            for sd in subdirs:
                if any((f for f in sd.rglob("*") if f.is_file() and f.suffix.lower() in IMAGE_EXTS)):
                    has_images = True
                    break
            if has_images:
                images_root = cand
                break

    if images_root is None:
        # fallback: maybe images are directly under EXTRACT_DIR
        images_root = EXTRACT_DIR

    return images_root

def main():
    unzip_dataset()

    images_root = find_images_root_after_extract()
    print("Using images_root:", images_root)

    # ensure output root is clean / exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    create_splits(images_root)

    print("Done. You can now run training which expects:", DATA_DIR)

if __name__ == "__main__":
    main()
