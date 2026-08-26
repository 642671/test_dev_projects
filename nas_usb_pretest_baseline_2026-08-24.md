# NAS USB test baseline

Captured at `2026-08-24T17:43:55+08:00` from `test@10.18.15.129:9222` before the user-performed reboot.

## NAS state

- Hostname: `TNAS`; kernel: `6.12.63+`.
- `tnas-mntdata.service`: active/exited, result `success`, `TimeoutStartUSec=1min`, `KillMode=none`.
- Internal Volume1: `/dev/mapper/vg0-lv0[/@]` mounted at `/Volume1` as Btrfs.
- Btrfs device counters were all zero: write/read/flush/corruption/generation errors.
- Internal system storage was only `/dev/sda` -> md0/vg0. No external USB volume was mounted.

## USB topology

- DAS/hub chain reports as TerraMaster/Realtek TDAS.
- Main USB hub: `0bda:0423`; downstream hubs: `0bda:0432`.
- Disk bridges: `0bda:9201` and `0bda:9210`.
- The attached storage interfaces use the `uas` driver at 10 Gb/s.
- This is not the original Innostor `1f75:0611` bridge.

## External disks observed

| Linux device | Model | Serial | Size | Existing partitions/signature |
|---|---|---|---:|---|
| `/dev/sdb` | `28TDP` | `2349456A7D46` | 119.2 GiB | `sdb1`-`sdb4`; `sdb4` is `linux_raid_member` |
| `/dev/sdc` | `WDC WD10EJRX-89N74Y0` | `WD-WCC4J2YZDVJX` | 931.5 GiB | `sdc1`-`sdc4`; `sdc2`-`sdc4` are `linux_raid_member` |
| `/dev/sdd` | `ST6000VN0041-2EL11C` | `ZA1DYTA4` | 5.5 TiB | `sdd1`-`sdd4`; `sdd4` is `linux_raid_member` |

## Important observations

- Kernel logs show TOS automatically activated external arrays from these disks (`md1`, `md2`, `md3`) and subsequently stopped them.
- StorageManager repeatedly logged `usb get usage failed by mountpoint-:no such file or directory` after the external disk discovery.
- No live `smartctl`, `hdparm`, `IHM`, `mntdata`, `pvs`, `vgs`, or `lvs` worker was stuck during this capture; only file-cache (`vmtouch`) references to the SMART binaries existed.

## Safety boundary before destructive preparation

All three external disks have pre-existing partition layouts and RAID signatures. A wipe must name the exact disk(s) to erase; do not use a broad “all USB disks” command.
