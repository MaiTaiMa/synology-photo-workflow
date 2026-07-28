#!/bin/sh
set -eu
cd "$(dirname "$0")/../legacy"
sha256sum -c SHA256SUMS
bash -n nas_photosort.sh
