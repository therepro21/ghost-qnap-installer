#!/bin/sh
set -eu
if [ "${MODE:-compose}" = qnap ]; then exec python3 qnap_app.py; fi
exec python3 app.py
