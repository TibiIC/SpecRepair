#!/bin/bash

############################
# ====== CONFIG ===========
############################

RUN_FOLDER="traffic_updated_2025-11-19"   # <-- CHANGE THIS
BASENAME="traffic_updated"            # <-- CHANGE THIS

REMOTE_BASE="/vol/bitbucket/tg4018/PhD/SpecRepair/tests/test_files/out"
REMOTE_SUBDIR="maximal_specs"
LOCAL_DEST="$HOME/Documents/PhD/SpecRepair/tests/test_files/out/maximal_solutions_from_ssh"

REMOTE_HOST="gpu11"

############################
# ====== SCRIPT ===========
############################

i=0

ssh $REMOTE_HOST "ls ${REMOTE_BASE}/${RUN_FOLDER}/${REMOTE_SUBDIR}/*.spectra" | sort | while read f; do
    scp "${REMOTE_HOST}:$f" "${LOCAL_DEST}/${BASENAME}_${i}.spectra"
    ((i++))
done

echo "Done."