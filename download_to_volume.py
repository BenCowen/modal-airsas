# save as get_file.py; usage: python3 get_file.py URL scenes.zip
import os
from pathlib import Path
import zipfile


import modal

# # Introduction

# # Preliminaries
# ## Constants
HOURS = 60 * 60

# ### Data
vol = modal.Volume.from_name("airsas", create_if_missing=True)
MNT = "/data"

# ### App
app = modal.App("airsas", volumes={MNT: vol})

# ### Images
airsas_image = (
    modal.Image.from_registry("docker.io/gnuoctave/octave:10.2.0", add_python="3.12")
    .apt_install("ca-certificates", "git")
    .uv_pip_install("requests", "tqdm")
    .run_commands("git clone https://github.com/tblanford/airsas.git")
)


# ## Data Downloader
@app.function(
    image=airsas_image,
    timeout=24 * HOURS,
    max_containers=2,  # 2 in case of preemption needs replacement
)
def copy_data():
    """
    Download the data from Springer/ Nature/ figshare:
        https://springernature.figshare.com/articles/dataset/An_in-air_synthetic_aperture_sonar_dataset_of_target_scattering_in_environments_of_varying_complexity/26961892
    """
    import requests
    from tqdm import tqdm

    urls = {
        "data/scenes.zip": "https://springernature.figshare.com/ndownloader/files/49062316",
        "data/meta.zip": "https://springernature.figshare.com/ndownloader/files/49061617",
    }

    base = Path(MNT)
    for rel, url in urls.items():
        dest = base / rel
        tmp = dest.with_suffix(dest.suffix + ".part")
        tmp.parent.mkdir(parents=True, exist_ok=True)

        pos = tmp.stat().st_size if tmp.exists() else 0
        headers = {"Range": f"bytes={pos}-"} if pos else {}

        with requests.get(
            url, headers=headers, stream=True, allow_redirects=True, timeout=30
        ) as r:
            # If server ignored Range during resume, start fresh
            if pos and r.status_code == 200:
                tmp.unlink(missing_ok=True)
                pos, headers = 0, {}

            r.raise_for_status()
            total = None
            if "Content-Range" in r.headers:
                # e.g. "bytes 12345-.../99999999"
                try:
                    total = int(r.headers["Content-Range"].split("/")[-1])
                except:
                    total = None
            elif "Content-Length" in r.headers:
                try:
                    total = pos + int(r.headers["Content-Length"])
                except:
                    pass

            with (
                open(tmp, "ab" if pos else "wb") as f,
                tqdm(
                    total=total, initial=pos, unit="B", unit_scale=True, desc=rel
                ) as bar,
            ):
                for chunk in r.iter_content(1 << 20):
                    if not chunk:
                        continue
                    f.write(chunk)
                    bar.update(len(chunk))
                f.flush()
                os.fsync(f.fileno())

        tmp.replace(dest)  # atomic finalize

        # Finally:
        if dest.suffix == ".zip":
            with zipfile.ZipFile(dest, "r") as zf:
                zf.extractall(dest.parent)
            print(f"✔ Unzipped {dest} into {dest.parent}")


@app.local_entrypoint()
def main():
    # TODO: move this to a check_data enter step
    # copy_data.spawn()

    return
