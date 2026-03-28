#!/usr/bin/bash

for img in $(podman images -q); do
    # 提取第一个 Tag，如果没有则显示 ID
    NAME=$(podman inspect "$img" --format '{{if .RepoTags}}{{index .RepoTags 0}}{{else}}{{.Id}}{{end}}')
    TYPE=$(podman inspect "$img" --format '{{.ManifestType}}')
    printf "%-50s | %s\n" "$NAME" "$TYPE"
done
