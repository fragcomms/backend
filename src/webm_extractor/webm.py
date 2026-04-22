import sys
import os
import json
import subprocess


def extract_webm(mka_path):
  if not os.path.exists(mka_path):
    print(
      'DATA_OUTPUT:{"type": "error", "payload": {"message": "MKA file not found"}}',
      flush=True,
    )
    sys.exit(1)

  base_dir = os.path.dirname(mka_path)
  base_name = os.path.splitext(os.path.basename(mka_path))[0]

  probe_cmd = [
    "ffprobe",
    "-v",
    "quiet",
    "-print_format",
    "json",
    "-show_streams",
    "-select_streams",
    "a",
    mka_path,
  ]

  try:
    result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    probe_data = json.loads(result.stdout)
  except Exception as e:
    print(
      f'DATA_OUTPUT:{{"type": "error", "payload": {{"message": "ffprobe failed: {str(e)}"}}}}',
      flush=True,
    )
    sys.exit(1)

  extracted_files = []

  for stream in probe_data.get("streams", []):
    index = stream.get("index")
    tags = stream.get("tags", {})

    discord_id = tags.get("title")

    if discord_id:
      out_filename = f"{base_name}_{discord_id}.webm"
      out_filepath = os.path.join(base_dir, out_filename)

      ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        mka_path,
        "-map",
        f"0:{index}",
        "-af",
        "aresample=async=1:first_pts=0",
        "-c:a",
        "libopus",
        "-b:a",
        "20k",
        "-f",
        "webm",
        out_filepath,
      ]

      try:
        subprocess.run(ffmpeg_cmd, capture_output=True, check=True)
        extracted_files.append({"discord_id": discord_id, "file_path": out_filepath})
      except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Failed to extract track {discord_id}: {e.stderr.decode()}\n")

  event = {
    "type": "webm_extraction_complete",
    "payload": {"mka_path": mka_path, "extracted_tracks": extracted_files},
  }

  print(f"DATA_OUTPUT:{json.dumps(event)}", flush=True)


if __name__ == "__main__":
  if len(sys.argv) < 2:
    print("Usage: python webm.py <path_to_mka>")
    sys.exit(1)
  extract_webm(sys.argv[1])
