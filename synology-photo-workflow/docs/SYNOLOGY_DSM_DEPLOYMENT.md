# Synology DSM deployment and acceptance

## One-time setup

1. Create a dedicated DSM shared-folder subdirectory such as `/volume1/photos/photo-workflow-data`; do not mount a broad root share.
2. Give the DSM account running Task Scheduler read/write access to that directory. Record its numeric UID/GID with `id`; set those exact values in `.env` with the absolute `WORKFLOW_DATA_ROOT`.
3. Copy `.env.example` to `.env`, copy `config/config.example.yaml` to `config/config.yaml`, and review all paths. All workflow paths must remain under `data/TEMP` after Docker mapping.
4. Build: `docker compose build`. Then run `./scripts/preflight.sh`; it performs Compose validation and `automation-status` only, never Phase 1 or Phase 2.

## DSM Task Scheduler

Use a user-defined scheduled task under the same DSM account that owns the share. Set the working directory to the cloned repository, or use an absolute command:

```sh
cd /volume1/docker/synology-photo-workflow && /bin/bash scripts/run-phase1.sh >> /volume1/photos/photo-workflow-data/TEMP/WORKFLOW_DATA/runtime/task-phase1.log 2>&1
```

Create a separate Phase-2 task only after manual review. Start with a dry run:

```sh
cd /volume1/docker/synology-photo-workflow && /bin/bash scripts/run-phase2.sh --dry-run >> /volume1/photos/photo-workflow-data/TEMP/WORKFLOW_DATA/runtime/task-phase2.log 2>&1
```

Do not schedule `phase2` without `--dry-run` until the acceptance checklist is signed off. `assistedreview` remains the required production default.

## NAS acceptance checklist

- Confirm `docker compose run --rm photo-workflow --config config/config.yaml automation-status` reports `automaticphase2permitted: false` for the default configuration.
- Put one disposable JPG/ARW pair in a valid `TEMPSD/YYYYMMDD` batch. Run Phase 1; verify JPG ZIP readability, manifest hash, state file, and handoff to `TEMPIMAGES`.
- Move the review result manually to `TEMPDONE`, run Phase 2 dry-run, and compare its planned ARWs with the review folders.
- For the first destructive trial, use disposable copies only. Verify the SORTARW ZIP with `unzip -t`, its SHA-256 against the state file, and that only planned ARWs were removed.
- If metadata is enabled, verify an ExifTool readback in the DSM container. If family recognition is enabled, test its backend/cache separately; neither feature may promote an image directly to keep.
- Verify Task Scheduler logs, UID/GID ownership, lock behavior, restart/resume after an intentional interruption, and free disk capacity before real data use.

## Rollback

Disable DSM tasks first. Preserve `runtime/state`, manifests, review records, and logs. Restore an ARW from the validated batch SORTARW ZIP if needed; do not delete or edit state files to force a rerun.


## Executable non-destructive preflight

Run this on DSM under the same account that will own the scheduled task:

```sh
cd /volume1/docker/synology-photo-workflow
./scripts/dsm-acceptance-preflight.sh
```

It checks Docker Compose syntax, the legacy checksum/syntax, configured persistent
root existence and access. It **does not** run either workflow phase and does not
touch image batches.

## Staged acceptance protocol

Complete each stage using disposable copies, record the command, result, run-summary
path and operator in the local deployment log. Do not advance after a failure.

1. **Mount and identity:** `id`; verify `WORKFLOW_DATA_ROOT`, owner UID/GID and
   read/write access from inside the container with `docker compose run --rm
   photo-workflow sh -lc 'id; test -r /data && test -w /data'`.
2. **Container persistence:** create a harmless marker below the mounted runtime
   directory from the container, remove/recreate the container, then verify the
   marker exists on DSM. Remove the marker afterward.
3. **Phase 1:** one disposable `JPG`/`ARW` pair in a valid source folder; verify
   `ALLJPG.zip` with `unzip -t`, manifest hash, state and `TEMPIMAGES` handoff.
4. **SIGTERM/resume:** use a batch with multiple disposable JPGs, terminate the
   container during scoring or metadata, inspect the paused state, then rerun and
   verify no completed row is rescored and no Phase-1 handoff precedes completion.
5. **Phase 2 dry run:** manually move the reviewed folder; compare planned paths
   with the active main-folder JPG rule. Confirm no ARW or ZIP changes.
6. **Phase 2 transaction:** on disposable data, interrupt after archive activation
   but before all deletes; verify ZIP via `unzip -t` and state SHA-256, rerun, then
   confirm only planned ARWs were removed.
7. **Optional dependencies:** separately test ExifTool write/readback and enabled
   face-cache rebuild. A missing required backend must block, not silently disable,
   the configured feature.
8. **Scheduler:** run both scheduled commands under the final DSM user; verify
   logs, lock contention, time-budget pause and next-run resumption.

A successful local pytest run is not a DSM acceptance result; retain this completed
protocol with the NAS operation record before enabling destructive production runs.
