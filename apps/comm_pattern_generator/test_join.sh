#!/usr/bin/env bash

kdts_job_deps=()
kdts_job_deps+=("1234")
kdts_job_deps+=("5678")

function join_by { local IFS="$1"; shift; echo "$*"; }
kdts_job_dep_str=$( join_by '&&' ${kdts_job_deps[@]} )
echo ${kdts_job_dep_str}
