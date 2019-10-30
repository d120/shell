#!/bin/bash

#
# VM Backup Script
#
# syncs current VM dumps from hypervisor without mirroring deletions
# locally deletes backups per VM, if any, such that the newest 5 remain
#
# Authors: Jan Hohmann <jhohmann@d120.de>, Johannes Lauinger <jlauinger@d120.de>
# 01.12.2016
#

PRODUCTION_SERVER=localhost
BACKUP_PATH="/backup/vm/"
MAX_BACKUP_COUNT=6

rsync -r -t --bwlimit=40960 --ignore-existing $PRODUCTION_SERVER:/mnt/backup/dump/ $BACKUP_PATH

find $BACKUP_PATH -type f -printf '%f\n' | sort | cut -d- -f1-3 | uniq | while read group; do
	COUNT=$(find $BACKUP_PATH -type f -name "$group*" | grep -ve "log$" | wc -l)
	if [[ $COUNT -ge $MAX_BACKUP_COUNT ]]; then
		ls -t $BACKUP_PATH | grep $group | grep -ve "log$" | tail -n +$MAX_BACKUP_COUNT | awk -v p="$BACKUP_PATH" '$0=p$0' | xargs rm
	fi
done

find $BACKUP_PATH -type f -name "*.log" -delete

