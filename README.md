# kalkan-xml-signer

XML signing using KalkanCrypt library (Kazakhstan PKI).

## Installation

```bash
pip install kalkan-xml-signer
```


## Requirements

- Python >= 3.10
- Native library `libkalkancryptwr-64.so` (KalkanCrypt)
- PKCS#12 certificate file (`.p12`)

## Usage

```python
from kalkan_xml_signer import XMLSigner

with XMLSigner(
    lib_path="/path/to/libkalkancryptwr-64.so.2.0.2",
    cert_path="/path/to/cert.p12",
    cert_password="your_password",
) as signer:
    signed_xml = signer.sign_xml("<root><data>test</data></root>")
    print(signed_xml)
```

### With timestamp

```python
with XMLSigner(
    lib_path="/path/to/libkalkancryptwr-64.so.2.0.2",
    cert_path="/path/to/cert.p12",
    cert_password="your_password",
    tsa_url="http://tsp.pki.gov.kz:80",
) as signer:
    signed_xml = signer.sign_xml(
        xml="<root><data>test</data></root>",
        flags=XMLSigner.KC_WITH_TIMESTAMP,
    )
```

### Manual init/finalize

```python
signer = XMLSigner(lib_path="/path/to/lib.so")
signer.init()
signer.load_certificate("/path/to/cert.p12", "password")
signed_xml = signer.sign_xml("<root/>")
signer.finalize()
```
