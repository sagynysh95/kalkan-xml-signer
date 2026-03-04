#!/bin/bash

# Install KalkanCrypt PKI certificates (root & NCA)
# Run with sudo: sudo kalkan-install-certs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d /usr/local/share/ca-certificates/extra ]; then
	mkdir -p /usr/local/share/ca-certificates/extra
fi

cp -a "$SCRIPT_DIR"/*.pem /etc/ssl/certs/

# Convert .pem to .crt and copy to ca-certificates
for f in "$SCRIPT_DIR"/*.pem; do
    filename=$(basename "$f" .pem)
    cp "$f" "/usr/local/share/ca-certificates/extra/${filename}.crt"
done

update-ca-certificates

echo "KalkanCrypt PKI certificates installed successfully."
