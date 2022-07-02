<!--
This file is part of cjdk.
Copyright 2022, Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

# Changelog

See also the section on [versioning](versioning-scheme).

## [Unreleased]

[Unreleased]: https://github.com/marktsuchida/cjdk/compare/v0.2.0...HEAD

## [0.2.0] - 2022-07-02

[0.2.0]: https://github.com/marktsuchida/cjdk/compare/v0.1.1...v0.2.0

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

[0.1.1]: https://github.com/marktsuchida/cjdk/compare/v0.1.0...v0.1.1

First release.

## [0.1.0] - 2022-06-23

[0.1.0]: https://github.com/marktsuchida/cjdk/tree/v0.1.0

Tag created but not actually released.
