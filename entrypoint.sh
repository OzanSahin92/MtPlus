#!/bin/bash --login
set -e

conda activate mtplus
exec "$@"
