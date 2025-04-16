import os
import requests
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

#URL = "https://bigota.d.miui.com/V12.5.3.0.RCRIDXM/miui_ANGELICAIDGlobal_V12.5.3.0.RCRIDXM_f393b1e84d_11.0.zip"

URL = "https://bigota.d.miui.com/V12.5.3.0.RCRIDXM/angelica_id_global_images_V12.5.3.0.RCRIDXM_20220731.0000.00_11.0_global_7435392bee.tgz"
FILENAME = URL.split("/")[-1]
NUM_THREADS = 32
CHUNK_SIZE = 1024 * 256  # 256KB

BASE_DIR = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(BASE_DIR, "results2")
OUTPUT_PATH = os.path.join(RESULTS_DIR, FILENAME)
os.makedirs(RESULTS_DIR, exist_ok=True)

def get_file_size():
    res = requests.head(URL)
    return int(res.headers['Content-Length'])

def download_part(start, end, part_num, pbar):
    headers = {'Range': f'bytes={start}-{end}'}
    part_path = os.path.join(RESULTS_DIR, f"{FILENAME}.part{part_num}")

    downloaded = os.path.getsize(part_path) if os.path.exists(part_path) else 0
    if downloaded >= (end - start + 1):
        pbar.update(end - start + 1)
        return

    with requests.get(URL, headers=headers, stream=True) as r:
        r.raise_for_status()
        with open(part_path, 'ab') as f:
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))

def combine_parts():
    with open(OUTPUT_PATH, 'wb') as output:
        for i in range(NUM_THREADS):
            part_path = os.path.join(RESULTS_DIR, f"{FILENAME}.part{i}")
            with open(part_path, 'rb') as part_file:
                output.write(part_file.read())
            os.remove(part_path)

def main():
    file_size = get_file_size()
    part_size = file_size // NUM_THREADS

    print(f"[+] Ukuran file: {file_size / (1024**2):.2f} MB")
    print(f"[+] Mulai unduh dengan {NUM_THREADS} koneksi...\n")

    ranges = []
    for i in range(NUM_THREADS):
        start = i * part_size
        end = file_size - 1 if i == NUM_THREADS - 1 else (start + part_size - 1)
        ranges.append((start, end, i))

    with tqdm(total=file_size, unit='B', unit_scale=True, desc='Mengunduh') as pbar:
        with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
            futures = [executor.submit(download_part, start, end, i, pbar) for start, end, i in ranges]
            for f in futures:
                f.result()

    print("\n[*] Menggabungkan file...")
    combine_parts()
    print(f"[✓] Selesai! File tersimpan di: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()

