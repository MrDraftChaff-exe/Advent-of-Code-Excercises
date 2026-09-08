#!/usr/bin/env bash
# Download Java (if needed), the official vanilla server jar, and playit.gg.
set -euo pipefail
# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
load_versions
ensure_dirs

os="$(uname -s | tr '[:upper:]' '[:lower:]')"
arch="$(uname -m)"
case "$arch" in
  x86_64|amd64) adoptium_arch="x64"; playit_arch="amd64" ;;
  aarch64|arm64) adoptium_arch="aarch64"; playit_arch="aarch64" ;;
  *) echo "Unsupported CPU architecture: $arch" >&2; exit 1 ;;
esac
case "$os" in
  linux) adoptium_os="linux" ;;
  darwin) adoptium_os="mac" ;;
  *) echo "Unsupported OS: $os (use windows/Start-Server.ps1 on Windows)" >&2; exit 1 ;;
esac

install_jdk() {
  local bin
  bin="$(java_bin)"
  if [[ -n "$bin" ]]; then
    local major
    major="$(java_major_version "$bin" || true)"
    if [[ -n "${major:-}" && "$major" -ge "$JAVA_MAJOR" ]]; then
      echo "Java $major already available: $bin"
      return
    fi
  fi

  echo "Downloading Temurin JDK ${JAVA_MAJOR} for ${adoptium_os}/${adoptium_arch}..."
  local url tarball
  url="https://api.adoptium.net/v3/binary/latest/${JAVA_MAJOR}/ga/${adoptium_os}/${adoptium_arch}/jdk/hotspot/normal/eclipse?project=jdk"
  tarball="$CACHE/jdk${JAVA_MAJOR}.tar.gz"
  curl -fL --retry 3 --retry-delay 2 -o "$tarball" "$url"
  rm -rf "$CACHE/jdk"
  mkdir -p "$CACHE/jdk"
  tar -xzf "$tarball" -C "$CACHE/jdk" --strip-components=1
  rm -f "$tarball"
  echo "Installed $($CACHE/jdk/bin/java -version 2>&1 | head -n 1)"
}

sha1_file() {
  if command -v sha1sum >/dev/null 2>&1; then
    sha1sum "$1" | awk '{print $1}'
  else
    shasum -a 1 "$1" | awk '{print $1}'
  fi
}

install_server_jar() {
  local jar="$CACHE/server-${MC_VERSION}.jar"
  if [[ -f "$jar" && -n "$MC_SERVER_SHA1" ]]; then
    local have
    have="$(sha1_file "$jar")"
    if [[ "$have" == "$MC_SERVER_SHA1" ]]; then
      echo "Server jar already cached: $jar"
      cp -f "$jar" "$RUNTIME/server.jar"
      return
    fi
  fi
  if [[ -z "$MC_SERVER_URL" ]]; then
    echo "MC_SERVER_URL is empty" >&2
    exit 1
  fi
  echo "Downloading Minecraft ${MC_VERSION} server.jar..."
  curl -fL --retry 3 --retry-delay 2 -o "$jar" "$MC_SERVER_URL"
  if [[ -n "$MC_SERVER_SHA1" ]]; then
    local have
    have="$(sha1_file "$jar")"
    if [[ "$have" != "$MC_SERVER_SHA1" ]]; then
      echo "SHA-1 mismatch for server.jar (got $have, expected $MC_SERVER_SHA1)" >&2
      rm -f "$jar"
      exit 1
    fi
  fi
  cp -f "$jar" "$RUNTIME/server.jar"
}

install_playit() {
  local dest="$CACHE/bin/playit"
  local cli="$CACHE/bin/playit-cli"
  local base="https://github.com/playit-cloud/playit-agent/releases/download/${PLAYIT_TAG}"
  if [[ ! -x "$dest" ]]; then
    echo "Downloading playit ${PLAYIT_TAG}..."
    curl -fL --retry 3 --retry-delay 2 -o "$dest" "${base}/playit-linux-${playit_arch}"
    chmod +x "$dest"
  fi
  if [[ ! -x "$cli" ]]; then
    curl -fL --retry 3 --retry-delay 2 -o "$cli" "${base}/playit-cli-linux-${playit_arch}"
    chmod +x "$cli"
  fi
  echo "playit ready: $dest"
}

seed_runtime() {
  if [[ ! -f "$RUNTIME/eula.txt" ]]; then
    cp "$TEMPLATES/eula.txt" "$RUNTIME/eula.txt"
  fi
  if [[ ! -f "$RUNTIME/server.properties" ]]; then
    cp "$TEMPLATES/server.properties" "$RUNTIME/server.properties"
  fi
  # Keep the configured port in sync if SERVER_PORT was overridden.
  if grep -q '^server-port=' "$RUNTIME/server.properties"; then
    sed -i.bak "s/^server-port=.*/server-port=${SERVER_PORT}/" "$RUNTIME/server.properties"
    rm -f "$RUNTIME/server.properties.bak"
  fi
}

install_jdk
install_server_jar
if [[ "$os" == "linux" ]]; then
  install_playit
else
  echo "On macOS, download playit from https://playit.gg/download if you want internet friends."
fi
seed_runtime

echo
echo "Install complete."
echo "  Minecraft ${MC_VERSION}  Java ${JAVA_MAJOR}+  port ${SERVER_PORT}"
echo "Start the server with:  $ROOT/scripts/start-server.sh"
