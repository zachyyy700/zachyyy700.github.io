import osxphotos
from PIL import Image as PILImage
import datetime as dt
from colorthief import ColorThief
import pandas as pd
import logging
import os

OUTPUT_FILE = "posts/2026-3-17-photo-palette/all_colors.csv"

# set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s", 
                    handlers=[logging.StreamHandler(),logging.FileHandler("posts/2026-3-17-photo-palette/all_colors.log")])
logger = logging.getLogger(__name__)

def photo_filter(photo): 
    # Exclude screenshots
    if photo.screenshot:
        return False
    # Exclude movies
    if photo.ismovie:
        return False
    # Exclude saved photos
    if photo.exif_info.aperture is None:
        return False
    return True

def load_processed_uuids():
    if not os.path.exists(OUTPUT_FILE):
        return set()
    df = pd.read_csv(OUTPUT_FILE)
    return set(df["uuid"].tolist())

def extract_colors(photos):
    processed = load_processed_uuids()
    skipped = len([p for p in photos if p.uuid in processed])
    if skipped:
        logger.info(f"Resuming: Skipping {skipped} already-processed photos.")
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    write_header = not os.path.exists(OUTPUT_FILE)

    # Initialize photo error count
    err_count = 0
    for i, photo in enumerate(photos):
        if photo.uuid in processed:
            continue
        try:
            ct = ColorThief(photo.path)
            r, g, b = ct.get_color()
            row = pd.DataFrame([{"uuid": photo.uuid, "path": photo.path, "date": photo.date, "r": r, "g": g, "b": b}])
            row.to_csv(OUTPUT_FILE, mode='a', header=write_header, index=False)
            write_header = False
        except Exception as e:
            err_count += 1
            logger.warning(f"Failed on {photo.path}: {e}")
        
        if (i + 1) % 100 == 0:
            logger.info(f"Progress: {i + 1} / {len(photos)}")
    
    logger.info(f"Done. Errors: {err_count}")

def main():

    # Retrieve photos library from system path
    logger.info("Loading photos from system.")
    photosdb = osxphotos.PhotosDB()

    start, end = dt.datetime(2024, 1, 1), dt.datetime(2026, 3, 31)
    photos = photosdb.photos(from_date=start, to_date=end)
    logger.info(f"{len(photos)} photos loaded.")

    photos = sorted([p for p in photos if photo_filter(p)], key=lambda p: p.date)
    logger.info(f"{len(photos)} after filter.")

    extract_colors(photos)

if __name__ == "__main__":
    main()