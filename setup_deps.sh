#!/usr/bin/env bash

usage() {
	cat <<'EOF'
Usage:
  . ./setup_deps.sh [options]
  ./setup_deps.sh --check [options]

Install ANACIN-X package dependencies into the active Conda environment and a
Spack environment. Source this script for a full install so Spack package loads
remain available in your current shell before running setup.sh.

Options:
  --check                 Check the local environment and exit before installing.
  --mpi NAME              MPI package name for Spack: openmpi, mpich, or mvapich2.
                          Default: openmpi.
  --spack-env NAME        Spack environment name to create or refresh.
                          Default: anacin_spack_env.
  -h, --help              Show this help text.

Required before install:
  - spack must be available in PATH.
  - conda must be available in PATH.
  - a Conda environment with Python 3.8 must be active.
  - mpicc must be available in PATH.

Examples:
  . /path/to/spack/share/spack/setup-env.sh
  conda activate anacin-x
  ./setup_deps.sh --check
  . ./setup_deps.sh --mpi openmpi
EOF
}

print_error() {
	printf 'ERROR: %s\n' "$*" >&2
}

print_ok() {
	printf 'OK: %s\n' "$*"
}

print_info() {
	printf 'INFO: %s\n' "$*"
}

main() {
	local mpi_name="openmpi"
	local spack_env_name="anacin_spack_env"
	local check_only="false"
	local repo_root
	local python_bin
	local python_version
	local install_status
	local failure_count=0

	while [ "$#" -gt 0 ]; do
		case "$1" in
			--check)
				check_only="true"
				shift
				;;
			--mpi)
				if [ -z "${2:-}" ]; then
					print_error "--mpi requires one of: openmpi, mpich, mvapich2"
					return 2
				fi
				mpi_name="$2"
				shift 2
				;;
			--mpi=*)
				mpi_name="${1#*=}"
				shift
				;;
			--spack-env)
				if [ -z "${2:-}" ]; then
					print_error "--spack-env requires a non-empty environment name"
					return 2
				fi
				spack_env_name="$2"
				shift 2
				;;
			--spack-env=*)
				spack_env_name="${1#*=}"
				shift
				;;
			-h|--help)
				usage
				return 0
				;;
			*)
				print_error "Unknown option: $1"
				usage >&2
				return 2
				;;
		esac
	done

	case "${mpi_name}" in
		openmpi|mpich|mvapich2)
			;;
		*)
			print_error "Unsupported MPI '${mpi_name}'. Use one of: openmpi, mpich, mvapich2."
			return 2
			;;
	esac

	if [ -z "${spack_env_name}" ]; then
		print_error "--spack-env requires a non-empty environment name"
		return 2
	fi

	if [ "${check_only}" != "true" ] && [ "${BASH_SOURCE[0]}" = "$0" ]; then
		print_error "Source this script for a full install so Spack package loads remain in your current shell."
		printf '       Run: . ./setup_deps.sh --mpi %s\n' "${mpi_name}" >&2
		printf '       For validation without installing, run: ./setup_deps.sh --check\n' >&2
		return 1
	fi

	repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
	python_bin="${ANACIN_X_PYTHON:-}"

	echo "Checking ANACIN-X dependency installer prerequisites..."
	echo

	if command -v spack >/dev/null 2>&1; then
		print_ok "spack found at $(command -v spack)"
	else
		print_error "spack was not found in PATH."
		printf '       Source Spack first, for example: . /path/to/spack/share/spack/setup-env.sh\n' >&2
		failure_count=$((failure_count + 1))
	fi

	if command -v conda >/dev/null 2>&1; then
		print_ok "conda found at $(command -v conda)"
	else
		print_error "conda was not found in PATH."
		printf '       Install Miniconda or Anaconda, then ensure conda is initialized in this shell.\n' >&2
		failure_count=$((failure_count + 1))
	fi

	if command -v mpicc >/dev/null 2>&1; then
		print_ok "mpicc found at $(command -v mpicc)"
	else
		print_error "mpicc was not found in PATH."
		printf '       Load your MPI compiler wrapper, for example: spack load %s\n' "${mpi_name}" >&2
		failure_count=$((failure_count + 1))
	fi

	if command -v cc >/dev/null 2>&1; then
		print_ok "C compiler found at $(command -v cc)"
	elif command -v gcc >/dev/null 2>&1; then
		print_ok "C compiler found at $(command -v gcc)"
	elif command -v clang >/dev/null 2>&1; then
		print_ok "C compiler found at $(command -v clang)"
	else
		print_error "No C compiler was found in PATH."
		printf '       Install or load a C compiler, then run: spack compiler find\n' >&2
		failure_count=$((failure_count + 1))
	fi

	if [ -n "${CONDA_PREFIX:-}" ]; then
		print_ok "Active Conda environment: ${CONDA_PREFIX}"
		if [ -d "${CONDA_PREFIX}/bin" ]; then
			export PATH="${CONDA_PREFIX}/bin:${PATH}"
		fi
	else
		print_error "No active Conda environment detected."
		printf '       Create and activate one with: conda create -n anacin-x python=3.8 -y && conda activate anacin-x\n' >&2
		failure_count=$((failure_count + 1))
	fi

	if [ -z "${python_bin}" ] && [ -n "${CONDA_PREFIX:-}" ] && [ -x "${CONDA_PREFIX}/bin/python" ]; then
		python_bin="${CONDA_PREFIX}/bin/python"
	fi
	if [ -z "${python_bin}" ] && [ -n "${CONDA_PREFIX:-}" ] && [ -x "${CONDA_PREFIX}/bin/python3" ]; then
		python_bin="${CONDA_PREFIX}/bin/python3"
	fi
	if [ -z "${python_bin}" ]; then
		python_bin="$(command -v python 2>/dev/null || command -v python3 2>/dev/null || true)"
	fi

	if [ -z "${python_bin}" ]; then
		print_error "No Python executable was found."
		printf '       Activate a Conda environment with Python 3.8 before running this script.\n' >&2
		failure_count=$((failure_count + 1))
	else
		python_version="$("${python_bin}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
		if [ "${python_version}" = "3.8" ]; then
			print_ok "Python 3.8 found at ${python_bin}"
		else
			print_error "ANACIN-X requires Python 3.8, but detected Python ${python_version:-unknown} at ${python_bin}."
			printf '       Run: conda create -n anacin-x python=3.8 -y && conda activate anacin-x\n' >&2
			failure_count=$((failure_count + 1))
		fi
	fi

	echo

	if [ "${failure_count}" -gt 0 ]; then
		print_error "Preflight checks failed with ${failure_count} issue(s). Resolve them and run ./setup_deps.sh --check again."
		return 1
	fi

	print_ok "Preflight checks passed."
	print_info "MPI package: ${mpi_name}"
	print_info "Spack environment: ${spack_env_name}"

	if [ "${check_only}" = "true" ]; then
		print_info "Check-only mode completed. No packages were installed."
		return 0
	fi

	echo
	echo "Installing ANACIN-X dependencies. This can take a while, especially when Spack builds packages from source."
	echo

	cd "${repo_root}/install" || return 1
	. ./install_anacin_deps.sh "${mpi_name}" "linux86" "${spack_env_name}" "yes" "yes" "yes" "yes" "yes"
	install_status=$?
	cd "${repo_root}" || return "${install_status}"
	return "${install_status}"
}

main "$@"
setup_deps_status=$?
return "${setup_deps_status}" 2>/dev/null || exit "${setup_deps_status}"
