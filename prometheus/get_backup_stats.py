#!/usr/bin/env python3

import os
import re
from datetime import datetime

BACKUP_DIR = "/backup/vm/"
BACKUP_FILE_REGEX = "^vzdump-qemu-.*vma\.gz$"
OUTPUT_FILE = "/var/lib/node_exporter/textfile_collector/backup_state.prom"


def getServerName(serverId):
    lookup = {}
    lookup["111"] = "host02"
    lookup["200"] = "glados"
    lookup["201"] = "storagecube"
    lookup["202"] = "turret"
    lookup["203"] = "atlas"
    if serverId in lookup:
        return lookup[serverId]
    return serverId


def getBackupFiles():
    files = os.listdir(BACKUP_DIR)
    r = re.compile(BACKUP_FILE_REGEX)
    files = [os.path.join(BACKUP_DIR, a) for a in files if r.match(a)]
    return files


def getLastBackupDate(files):
    times = [os.stat(a).st_mtime for a in files]
    return str(int(max(times)))


def getBackupSize(ifile):
    fsize = str(os.stat(ifile).st_size)
    ftime = datetime.fromtimestamp(os.stat(ifile).st_mtime).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    return ftime, fsize


def groupBackups(files):
    reg = re.compile("^vzdump-qemu-([^-]+)")
    results = {}
    for ifile in files:
        bname = os.path.basename(ifile)
        match = reg.match(bname)
        if not match:
            continue
        server = match.groups()[0]
        if not server in results:
            results[server] = []
        results[server].append(ifile)
    return results


def writeBackupStats(serverId, files, fhdl):
    servername = getServerName(serverId)
    fhdl.write('backup_last_date{type="image",vm="')
    fhdl.write(servername)
    fhdl.write('"} ')
    fhdl.write(getLastBackupDate(files))
    fhdl.write("\n")
    for f in files:
        ftime, fsize = getBackupSize(f)
        fhdl.write('backup_size{type="image",vm="')
        fhdl.write(servername)
        fhdl.write('",date="')
        fhdl.write(ftime)
        fhdl.write('"} ')
        fhdl.write(fsize)
        fhdl.write("\n")

    fhdl.write("\n")


def main():
    files = getBackupFiles()
    if not files:
        # Write empty stat file!!
        exit()
    date = getLastBackupDate(files)
    # print getBackupSize(files[0])
    bname = [os.path.basename(a) for a in files]
    bcks = groupBackups(files)
    f = open(OUTPUT_FILE + ".tmp", "w")
    for bset, data in bcks.items():
        writeBackupStats(bset, data, f)
    f.close()
    os.rename(OUTPUT_FILE + ".tmp", OUTPUT_FILE)
    # print bname[0]
    # print reg.match(bname[0]).groups()[0]


if __name__ == "__main__":
    main()
