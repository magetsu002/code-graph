# M0 baseline

Upstream source commit: `05542ba9132d21cc404930a9d0aa410bfba723de`

Evaluation branch: `test/adversarial-evaluation`

Host:
- Linux CachyOS, kernel 6.18.50-1-cachyos-lts
- Python 3.14.7
- Node.js 26.10.0 / npm 12.1.0
- PHP 8.5.11 from a user-local extracted Arch package
- Composer 2.10.3
- Rust 1.98.1

Install:
- Python dependencies installed in .venv using the README dependency list.
- TypeScript extractor dependencies installed with npm ci.
- PHP extractor dependencies installed with Composer.

Upstream suite:
- 130 tests collected
- 119 passed
- 11 skipped
- 0 failed
- wall time: about 19 seconds
- working tree remained clean after the suite

Skip reasons:
- 6 Flutter/Dart tests: Dart SDK unavailable
- 2 exact-mode C/C++ tests: scip-clang and/or cmake unavailable
- 3 exact-mode Rust tests: rust-analyzer unavailable

A first run before supplying the documented PHP toolchain produced 54 failures because the Laravel/PHP fixtures could not be indexed. That run is environmental, not recorded as a code-graph defect.

M0 result: PASS. The checked-out upstream state is a valid baseline for adversarial work on the available toolchains.