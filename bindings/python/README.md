# xmtp-bindings

Python bindings for libxmtp (XMTP v3) generated via UniFFI.

## Local build

These bindings are generated from the `libxmtp` Rust workspace. To regenerate:

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
