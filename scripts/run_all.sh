#!/usr/bin/env bash
# غلافٌ متوافق مع الاستعمال القديم. الأمر المعتمد الآن:  python3 -m aslot all
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 -m aslot all "$@"
