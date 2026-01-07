<!--
This file is part of cjdk.
Copyright 2022-25 Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

# Changelog

See also the section on [versioning](versioning-scheme).

## [Unreleased]

## [0.5.0] - 2026-01-07

### Added

- Add `cjdk clear-cache` and `clear_cache()`.
- Add API exception hierarchy (`CjdkError`, `ConfigError`, `JdkNotFoundError`,
  `InstallError`).
- Command line exit codes by error category.

### Changed

- Environment variables set to empty are now treated as unset.
- API now raises `CjdkError` and subclasses on known errors.

### Fixed

- Improve cleanup of temporary files and directories.
- Better message when a leftover directory blocks a download.

## [0.4.1] - 2025-05-01

### Added

- Add type hints to Python API (@tlambert03).

## [0.4.0] - 2025-04-17

### Added

- Python API functions `list_jdks()` and `list_vendors()` (@ctrueden).
- Command line commands `ls` and `ls-vendors` (@ctrueden).
- Light postprocessing of vendor names, notably `ibm-semeru-openj9`
  (@ctrueden).
- Python 3.13 compatibility.

### Changed

- Command line command `cache-jdk` renamed to `cache`.

## [0.3.0] - 2022-07-09

### Added

- Support running the CLI via `python -m cjdk`.
- Environment variable `CJDK_HIDE_PROGRESS_BARS`.

### Changed

- Source code repository moved to https://github.com/cachedjdk/cjdk.

### Fixed

- Prevent `cjdk exec` from displaying warnings about multiprocessing on macOS.

## [0.2.0] - 2022-07-02

### Added

- Python API functions `cache_jdk()`, `cache_file()`, and `cache_package()`.
- Command line commands `cache-jdk`, `cache-file`, and `cache-package`.
- Command line options `--index-url`, `--index-ttl`, `--os`, and `--arch`.
- Environment variables `CJDK_INDEX_URL`, `CJDK_INDEX_TTL`, `CJDK_OS`, and
  `CJDK_ARCH`.
- Documentation using Jupyter Book, published to GitHub Pages.

### Changed

- Rename environment variable `CJDK_DEFAULT_VENDOR` to `CJDK_VENDOR`.

### Fixed

- Always print progress messages to standard error.
- Correctly restore environment when exiting the `java_env()` context manager,
  even when there was an error.
- Always check HTTP status code for downloads.

## [0.1.1] - 2022-06-23

First release.

## [0.1.0] - 2022-06-23

Tag created but not actually released.

[0.1.0]: https://github.com/cachedjdk/cjdk/tree/v0.1.0
[0.1.1]: https://github.com/cachedjdk/cjdk/compare/v0.1.0...v0.1.1
[0.2.0]: https://github.com/cachedjdk/cjdk/compare/v0.1.1...v0.2.0
[0.3.0]: https://github.com/cachedjdk/cjdk/compare/v0.2.0...v0.3.0
[0.4.0]: https://github.com/cachedjdk/cjdk/compare/v0.3.0...v0.4.0
[0.4.1]: https://github.com/cachedjdk/cjdk/compare/v0.4.0...v0.4.1
[0.5.0]: https://github.com/cachedjdk/cjdk/compare/v0.4.1...v0.5.0
[unreleased]: https://github.com/cachedjdk/cjdk/compare/v0.5.0...HEAD
