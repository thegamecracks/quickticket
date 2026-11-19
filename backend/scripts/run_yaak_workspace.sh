#!/usr/bin/env bash
# Send every request in the Yaak workspace in sortPriority order and check status.
#
# The workspace is read with `yaak export` because `yaak request list` prints
# neither folders nor sortPriority. `yaak send <workspace>` and
# `yaak send <folder>` list requests newest-created first, so this script sends
# one request at a time in the order the app displays.
#
# Each request description starts with its expected status, for example
# "201. Creates the venue fixture...". A missing or mismatched status fails the
# run.
#
# By default the manual `00 Setup` and `80 Auth login` folders are skipped.
# Run those in the app first, or pass --include-manual.
#
# Usage: scripts/run_yaak_workspace.sh [--include-manual] [workspace-id]
set -euo pipefail

include_manual=0
workspace=""

for arg in "$@"; do
	case "$arg" in
		--include-manual)
			include_manual=1
			;;
		-h|--help)
			awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"
			exit 0
			;;
		-*)
			echo "unknown option: $arg" >&2
			exit 2
			;;
		*)
			if [ -n "$workspace" ]; then
				echo "only one workspace ID may be given" >&2
				exit 2
			fi
			workspace="$arg"
			;;
	esac
done

if ! command -v jq >/dev/null 2>&1; then
	echo "jq is required to run the Yaak workspace" >&2
	exit 1
fi
if ! command -v yaak >/dev/null 2>&1; then
	echo "the yaak CLI is required to run the Yaak workspace" >&2
	exit 1
fi

# `yaak export` writes a neighbouring temp file and renames it into place, so
# it needs a real path rather than a pipe or /dev/stdout.
export_file="$(mktemp)"
trap 'rm -f "$export_file" "$export_file".tmp*' EXIT

if [ -n "$workspace" ]; then
	yaak export "$export_file" "$workspace" >/dev/null
else
	yaak export "$export_file" >/dev/null
fi

plan="$(jq -r --argjson include_manual "$include_manual" '
	(.resources.folders // []) as $folders
	| .resources.httpRequests[]?
	| . as $request
	| ($folders | map(select(.id == $request.folderId)) | first) as $folder
	| (($folder.name // "") | tostring) as $folder_name
	| select($include_manual == 1 or (($folder_name | startswith("00 ")) | not))
	| select($include_manual == 1 or (($folder_name | startswith("80 ")) | not))
	| [
		(($folder.sortPriority // 0) | tostring),
		(($request.sortPriority // 0) | tostring),
		$request.id,
		($request.name // $request.id),
		(($request.description // "") | try capture("^(?<code>[0-9]{3})").code catch "-")
	]
	| @tsv
' "$export_file" | sort -t$'\t' -k1,1g -k2,2g)"

if [ -z "$plan" ]; then
	echo "no requests found in the Yaak workspace" >&2
	exit 1
fi

status=0
checked=0
while IFS=$'\t' read -r _folder_priority _request_priority id name expected; do
	[ -n "$id" ] || continue
	checked=$((checked + 1))

	if ! yaak request send "$id" >/dev/null; then
		printf '%-7s %s (send failed)\n' "-" "$name" >&2
		status=1
		continue
	fi

	actual="$(yaak response show "$id" | jq -r '.status // "-"')"
	if [ "$actual" != "$expected" ]; then
		printf '%-7s %-7s %s\n' "$actual" "want $expected" "$name" >&2
		status=1
	else
		printf '%-7s %s\n' "$actual" "$name"
	fi
done <<<"$plan"

if [ "$status" -ne 0 ]; then
	echo "status mismatch in the Yaak workspace" >&2
else
	echo "all $checked requests returned their expected status"
fi
exit "$status"
