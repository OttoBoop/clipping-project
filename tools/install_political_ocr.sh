#!/usr/bin/env bash
# Rootless Render build installation, using signed official Debian repositories.
# Debian package references: https://packages.debian.org/bookworm/tesseract-ocr
# and https://packages.debian.org/bookworm/tesseract-ocr-por . No dpkg installation.
set -euo pipefail

political_ocr_root="${POLITICAL_OCR_ROOT:-$PWD/.render-tools/political-ocr}"
political_ocr_root="$(mkdir -p "$political_ocr_root" && cd "$political_ocr_root" && pwd)"
. /etc/os-release
if [[ "${ID:-}" != debian || "${VERSION_ID:-}" != 12 ]]; then
  echo 'Political OCR installation requires the verified Debian 12 Render image.' >&2
  exit 1
fi
for political_tool in apt-get dpkg-deb dpkg; do
  command -v "$political_tool" >/dev/null
done
political_ocr_work="$(mktemp -d)"
trap 'rm -rf "$political_ocr_work"' EXIT
mkdir -p "$political_ocr_work/state/lists/partial" "$political_ocr_work/cache/archives/partial"
cat > "$political_ocr_work/sources.list" <<'SOURCES'
deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://deb.debian.org/debian bookworm main
deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://deb.debian.org/debian bookworm-updates main
deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://security.debian.org/debian-security bookworm-security main
SOURCES
political_apt_options=(
  -o "Dir::State=$political_ocr_work/state"
  -o "Dir::State::status=/var/lib/dpkg/status"
  -o "Dir::Cache=$political_ocr_work/cache"
  -o "Dir::Etc::sourcelist=$political_ocr_work/sources.list"
  -o 'Dir::Etc::sourceparts=-'
  -o 'Dir::Etc::parts=-'
  -o 'Dir::Etc::main=-'
  -o "APT::Sandbox::User=$(id -un)"
  -o 'Debug::NoLocking=1'
  -o 'Acquire::Languages=none'
)
apt-get "${political_apt_options[@]}" update
apt-get "${political_apt_options[@]}" --download-only --no-install-recommends --yes install \
  tesseract-ocr tesseract-ocr-por
for political_package in "$political_ocr_work"/cache/archives/*.deb; do
  [[ -e "$political_package" ]] || continue
  dpkg-deb -x "$political_package" "$political_ocr_root"
done
# Explicitly download these even when present in the build host, so the native
# executable, its two OCR libraries and Portuguese model travel with the build.
(
  cd "$political_ocr_work"
  apt-get "${political_apt_options[@]}" download tesseract-ocr libtesseract5 liblept5 tesseract-ocr-por
)
for political_package in "$political_ocr_work"/*.deb; do
  dpkg-deb -x "$political_package" "$political_ocr_root"
done
political_ocr_arch="$(dpkg-architecture -qDEB_HOST_MULTIARCH 2>/dev/null || printf '%s-linux-gnu' "$(uname -m)")"
export LD_LIBRARY_PATH="$political_ocr_root/usr/lib/$political_ocr_arch${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export TESSDATA_PREFIX="$political_ocr_root/usr/share/tesseract-ocr/5/tessdata"
"$political_ocr_root/usr/bin/tesseract" --version
"$political_ocr_root/usr/bin/tesseract" --list-langs | grep -Fx por >/dev/null
printf 'Political OCR ready at %s; set POLITICAL_OCR_ROOT to this directory at runtime.\n' "$political_ocr_root"
