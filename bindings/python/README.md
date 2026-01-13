# xmtp-bindings

Python bindings for libxmtp (XMTP v3) generated via UniFFI.

## Install-time build

The Python package now builds the `libxmtp` native library during install. This requires:

- Rust toolchain (`cargo`)
- `git`

Environment overrides:

- `XMTP_LIBXMTP_PATH`: use an existing libxmtp checkout instead of cloning
- `XMTP_LIBXMTP_REF`: git ref (tag/branch/commit) to checkout
- `XMTP_LIBXMTP_REPO`: override the libxmtp git URL
- `XMTP_BINDINGS_SKIP_BUILD=1`: skip native build (requires a prebuilt `libxmtpv3` next to `xmtpv3.py`)
- `XMTP_BINDINGS_FORCE_BUILD=1`: rebuild even if a native library already exists

## Manual build

These bindings are generated from the `libxmtp` Rust workspace. To regenerate manually:

```bash
# Clone libxmtp into .deps if needed
mkdir -p .deps
[ -d .deps/libxmtp ] || git clone --depth 1 https://github.com/xmtp/libxmtp .deps/libxmtp

# Build the native library
cd .deps/libxmtp
cargo build -p xmtpv3 --release

# Generate Python bindings
cd bindings_ffi
cargo run --bin ffi-uniffi-bindgen --release --features uniffi/cli generate \
  --library ../target/release/libxmtpv3.so \
  --out-dir ../../../bindings/python/src/xmtp_bindings \
  --language python

# Copy the shared library next to the generated module
cp ../target/release/libxmtpv3.so ../../../bindings/python/src/xmtp_bindings/
```

## Notes

- The generated `xmtpv3.py` expects `libxmtpv3` to sit next to it.
- This package is intended to be consumed by the higher-level `python-sdk`.
