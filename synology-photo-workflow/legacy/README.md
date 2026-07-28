# Legacy Bash fallback: `nas_photosort.sh`

This directory contains the **unchanged historical fallback script** supplied as
`nas_photosort.sh` (script version `v4.2`). Its SHA-256 is recorded in
`SHA256SUMS`; verify it before use:

```sh
cd legacy
sha256sum -c SHA256SUMS
bash -n nas_photosort.sh
# Or, from the project root:
../scripts/verify-legacy.sh
```

## Purpose and limits

Use this script only as a manual emergency fallback when the Python/Docker
workflow or optional components are unavailable. It is **not** called by the
Python workflow, is not modified by it, and has no awareness of scoring,
metadata, sample pools, face recognition, calibration, manifests, or modern
resume state.

The script retains the historic basic flow:

1. Stable valid camera folders: `TEMPSD -> TEMPIMAGES`.
2. Move `*.ARW`/`*.arw` to `ARW/`.
3. Create `SAVE/<date>ALLJPG.zip` from source JPGs.
4. Process manually moved `TEMPDONE` folders: remove ARWs without a matching
   main-folder JPG, archive remaining ARWs as `SAVE/<date>SORTARW.zip`, and
   mark the folder `.PROCESSED`.

## Mandatory operational precautions

- Run it manually, with the same NAS paths and permissions it historically used.
- Do not run it concurrently with the Python workflow; both use independent
  locks and cannot coordinate state.
- Stop Python/Docker scheduling first; inspect `TEMPSD`, `TEMPIMAGES`, and
  `TEMPDONE` before invoking Bash.
- Treat it as a basic recovery tool, not as an equivalent of the Python safety
  model: it does not use Python batch state, archive fingerprints, review
  records, or calibration gates.
- Keep `TEMPDONE` folders manually reviewed; only JPGs in the batch main folder
  count as active for the legacy ARW cleanup logic.
