# Local State Store Contract

The shared file-backed state store writes one JSON document per key in `.state/`.

- Key: logical name, normalized into `<key>.json`
- Read semantics: missing file returns the caller-supplied default
- Write semantics: pretty-printed JSON with stable key ordering
