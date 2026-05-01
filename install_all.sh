#!/usr/bin/env bash

set -eo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
spack_root="${SPACK_ROOT:-${HOME}/spack}"
conda_root="${CONDA_ROOT:-${HOME}/miniconda3}"
conda_env="anacin-x"
python_version="3.8"
mpi_name="openmpi"
spack_env_name="anacin_spack_env"
install_spack="true"
install_conda="true"
install_mpi="true"
with_callstack="true"
force_submodule_clean="false"
accept_conda_tos="false"

usage() {
	cat <<'EOF'
Usage:
  ./install_all.sh [options]

Install a fresh ANACIN-X environment from this checkout. The script can install
Spack, install Miniconda, create the ANACIN-X Conda environment, install/load
MPI with Spack, install ANACIN-X dependencies, and build ANACIN-X.

Default install locations:
  Spack:     $HOME/spack
  Miniconda: $HOME/miniconda3
  Conda env: anacin-x
  MPI:       openmpi

Options:
  --spack-root PATH          Spack install/source path. Default: $HOME/spack.
  --conda-root PATH          Miniconda install/source path. Default: $HOME/miniconda3.
  --conda-env NAME           Conda environment name. Default: anacin-x.
  --mpi NAME                 MPI package name: openmpi, mpich, or mvapich2.
                             Default: openmpi.
  --spack-env NAME           Spack environment for ANACIN-X dependencies.
                             Default: anacin_spack_env.
  --skip-spack-install       Require an existing spack command instead of
                             cloning Spack if it is missing.
  --skip-conda-install       Require an existing conda command instead of
                             installing Miniconda if it is missing.
  --skip-mpi-install         Require an existing mpicc instead of installing
                             and loading MPI with Spack.
  --accept-conda-tos         Run Conda's Terms of Service acceptance commands
                             for Anaconda's default pkgs/main and pkgs/r
                             channels before creating/installing packages.
  --without-callstack        Build without CSMPI callstack tracing.
  --force-submodule-clean    Allow setup.sh to clean and rebuild submodules.
                             Required when local submodule changes are present.
  -h, --help                 Show this help text.

Examples:
  ./install_all.sh
  ./install_all.sh --mpi mpich
  ./install_all.sh --skip-mpi-install --mpi openmpi
EOF
}

log() {
	printf '\n==> %s\n' "$*"
}

info() {
	printf '    %s\n' "$*"
}

die() {
	printf 'ERROR: %s\n' "$*" >&2
	exit 1
}

have_command() {
	command -v "$1" >/dev/null 2>&1
}

run() {
	info "$*"
	"$@"
}

parse_args() {
	while [ "$#" -gt 0 ]; do
		case "$1" in
			--spack-root)
				[ -n "${2:-}" ] || die "--spack-root requires a path"
				spack_root="$2"
				shift 2
				;;
			--spack-root=*)
				spack_root="${1#*=}"
				shift
				;;
			--conda-root)
				[ -n "${2:-}" ] || die "--conda-root requires a path"
				conda_root="$2"
				shift 2
				;;
			--conda-root=*)
				conda_root="${1#*=}"
				shift
				;;
			--conda-env)
				[ -n "${2:-}" ] || die "--conda-env requires a name"
				conda_env="$2"
				shift 2
				;;
			--conda-env=*)
				conda_env="${1#*=}"
				shift
				;;
			--mpi)
				[ -n "${2:-}" ] || die "--mpi requires one of: openmpi, mpich, mvapich2"
				mpi_name="$2"
				shift 2
				;;
			--mpi=*)
				mpi_name="${1#*=}"
				shift
				;;
			--spack-env)
				[ -n "${2:-}" ] || die "--spack-env requires a name"
				spack_env_name="$2"
				shift 2
				;;
			--spack-env=*)
				spack_env_name="${1#*=}"
				shift
				;;
			--skip-spack-install)
				install_spack="false"
				shift
				;;
			--skip-conda-install)
				install_conda="false"
				shift
				;;
			--skip-mpi-install)
				install_mpi="false"
				shift
				;;
			--accept-conda-tos)
				accept_conda_tos="true"
				shift
				;;
			--without-callstack)
				with_callstack="false"
				shift
				;;
			--force-submodule-clean)
				force_submodule_clean="true"
				shift
				;;
			-h|--help)
				usage
				exit 0
				;;
			*)
				die "Unknown option: $1"
				;;
		esac
	done

	case "${mpi_name}" in
		openmpi|mpich|mvapich2)
			;;
		*)
			die "Unsupported MPI '${mpi_name}'. Use one of: openmpi, mpich, mvapich2."
			;;
	esac
}

require_linux_for_bootstrap() {
	if [ "$(uname -s)" != "Linux" ]; then
		die "This automated bootstrap currently supports Linux. Use --skip-spack-install and --skip-conda-install with existing tools on other systems."
	fi
}

miniconda_installer_url() {
	local machine

	machine="$(uname -m)"
	case "${machine}" in
		x86_64|amd64)
			printf '%s\n' "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
			;;
		aarch64|arm64)
			printf '%s\n' "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh"
			;;
		*)
			die "Unsupported Linux architecture for automatic Miniconda install: ${machine}"
			;;
	esac
}

source_spack() {
	local spack_command
	local spack_guess

	if [ -f "${spack_root}/share/spack/setup-env.sh" ]; then
		# shellcheck disable=SC1091
		. "${spack_root}/share/spack/setup-env.sh"
	elif have_command spack; then
		spack_command="$(command -v spack)"
		if [ "${spack_command#/}" != "${spack_command}" ]; then
			spack_guess="$(cd -- "$(dirname -- "${spack_command}")/.." && pwd)"
			if [ -f "${spack_guess}/share/spack/setup-env.sh" ]; then
				# shellcheck disable=SC1090
				. "${spack_guess}/share/spack/setup-env.sh"
			fi
		fi
		info "Using existing spack at $(command -v spack)"
	else
		return 1
	fi
}

ensure_spack() {
	log "Checking Spack"

	if source_spack; then
		info "Spack is available at $(command -v spack)"
		return
	fi

	[ "${install_spack}" = "true" ] || die "spack was not found. Remove --skip-spack-install or source Spack before running this script."
	require_linux_for_bootstrap

	if [ -e "${spack_root}" ]; then
		die "${spack_root} exists but does not look like a Spack checkout"
	fi

	run git clone --depth=2 https://github.com/spack/spack.git "${spack_root}"
	# shellcheck disable=SC1091
	. "${spack_root}/share/spack/setup-env.sh"
	run spack compiler find
}

source_conda() {
	local conda_base

	if [ -f "${conda_root}/etc/profile.d/conda.sh" ]; then
		# shellcheck disable=SC1091
		. "${conda_root}/etc/profile.d/conda.sh"
		return 0
	fi

	if have_command conda; then
		conda_base="$(conda info --base 2>/dev/null || true)"
		if [ -n "${conda_base}" ] && [ -f "${conda_base}/etc/profile.d/conda.sh" ]; then
			# shellcheck disable=SC1090
			. "${conda_base}/etc/profile.d/conda.sh"
			return 0
		fi
	fi

	return 1
}

ensure_conda() {
	local installer
	local url

	log "Checking Conda"

	if source_conda; then
		info "Conda is available at $(command -v conda)"
		return
	fi

	[ "${install_conda}" = "true" ] || die "conda was not found. Remove --skip-conda-install or initialize Conda before running this script."
	require_linux_for_bootstrap

	if [ -e "${conda_root}" ]; then
		die "${conda_root} exists but does not contain etc/profile.d/conda.sh"
	fi

	url="$(miniconda_installer_url)"
	installer="${TMPDIR:-/tmp}/miniconda-anacin-x.sh"

	if have_command curl; then
		run curl -L -o "${installer}" "${url}"
	elif have_command wget; then
		run wget -O "${installer}" "${url}"
	else
		die "curl or wget is required to download Miniconda"
	fi

	run bash "${installer}" -b -p "${conda_root}"
	# shellcheck disable=SC1091
	. "${conda_root}/etc/profile.d/conda.sh"
}

accept_conda_terms_if_requested() {
	[ "${accept_conda_tos}" = "true" ] || return 0

	log "Accepting Conda channel Terms of Service"
	if ! conda tos --help >/dev/null 2>&1; then
		info "This Conda version does not provide 'conda tos'; skipping Terms of Service acceptance."
		return 0
	fi

	run conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
	run conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
}

ensure_conda_env() {
	log "Checking Conda environment"

	if conda env list | awk '{print $1}' | grep -Fxq "${conda_env}"; then
		info "Using existing Conda environment: ${conda_env}"
	else
		if ! run conda create -n "${conda_env}" "python=${python_version}" -y; then
			die "Conda environment creation failed. If Conda requested Terms of Service acceptance, re-run with --accept-conda-tos or run the conda tos accept commands manually."
		fi
	fi

	run conda activate "${conda_env}"
}

ensure_mpi() {
	log "Checking MPI"

	if [ "${install_mpi}" = "true" ]; then
		run spack install "${mpi_name}"
		run spack load "${mpi_name}"
	elif ! have_command mpicc; then
		die "mpicc was not found. Load MPI first or remove --skip-mpi-install."
	fi

	have_command mpicc || die "mpicc was not found after MPI setup"
	info "mpicc is available at $(command -v mpicc)"
}

ensure_submodule_build_is_safe() {
	local submodule_status

	if ! have_command git || ! git -C "${repo_root}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
		return
	fi

	submodule_status="$(git -C "${repo_root}" status --short submodules 2>/dev/null || true)"
	if [ -z "${submodule_status}" ]; then
		return
	fi

	if [ "${force_submodule_clean}" = "true" ]; then
		info "Local submodule changes are present; continuing because --force-submodule-clean was provided."
		return
	fi

	printf '%s\n' "${submodule_status}" >&2
	die "setup.sh cleans submodules before rebuilding. Re-run with --force-submodule-clean if these changes can be discarded."
}

install_anacin_dependencies() {
	log "Installing ANACIN-X dependencies"

	cd "${repo_root}"
	./setup_deps.sh --check
	# shellcheck disable=SC1091
	if ! . ./setup_deps.sh --mpi "${mpi_name}" --spack-env "${spack_env_name}"; then
		die "ANACIN-X dependency installation failed. If Conda requested Terms of Service acceptance, re-run with --accept-conda-tos or run the conda tos accept commands manually."
	fi
}

build_anacin() {
	log "Building ANACIN-X"

	cd "${repo_root}"
	ensure_submodule_build_is_safe
	if [ "${with_callstack}" = "true" ]; then
		# shellcheck disable=SC1091
		. ./setup.sh -c
	else
		# shellcheck disable=SC1091
		. ./setup.sh
	fi
}

main() {
	parse_args "$@"

	log "Starting ANACIN-X full installation"
	info "Repository: ${repo_root}"
	info "Spack root: ${spack_root}"
	info "Conda root: ${conda_root}"
	info "Conda environment: ${conda_env}"
	info "MPI: ${mpi_name}"
	info "ANACIN-X Spack environment: ${spack_env_name}"

	ensure_spack
	ensure_conda
	accept_conda_terms_if_requested
	ensure_conda_env
	ensure_mpi
	install_anacin_dependencies
	build_anacin

	log "ANACIN-X installation completed"
}

main "$@"
