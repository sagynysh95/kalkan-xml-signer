# kalkan-xml-signer

Python-библиотека для подписи XML документов с использованием KalkanCrypt (Kazakhstan PKI).

Работает через ctypes-обёртку над нативной библиотекой `libkalkancryptwr-64.so`, предоставляемой НУЦ РК.

> **Поддерживаемые ОС:** только Debian-подобные дистрибутивы Linux (Debian, Ubuntu, Astra Linux и т.д.).

## Installation

```bash
pip install kalkan-xml-signer
```

## Prerequisites

### 1. Получение библиотеки KalkanCrypt SDK

Библиотека `libkalkancryptwr-64.so.2.0.2` не включена в пакет и должна быть получена отдельно.

1. Перейдите на [pki.gov.kz/en/get-sdk-3](https://pki.gov.kz/en/get-sdk-3/) и запросите SDK
2. Скачайте SDK и найдите файл `libkalkancryptwr-64.so.2.0.2` в папке `C/Linux/C/libs/v2.0.2 (Сертифицированная версия)/libkalkancryptwr-64.so.2.0.2`
3. Скопируйте библиотеку в локальную папку вашего проекта, например:

```
your-project/
├── libs/
│   └── libkalkancryptwr-64.so.2.0.2
├── certs/
│   └── your_cert.p12
└── main.py
```

### 2. Установка корневых сертификатов НУЦ РК

После установки пакета выполните:

```bash
sudo kalkan-install-certs
```

Эта команда установит корневые сертификаты НУЦ РК в системное хранилище (`/etc/ssl/certs/`).

### 3. Сертификат для подписи

Для подписи XML вам понадобится сертификат формата PKCS#12 (`.p12`), выданный НУЦ РК.

## Usage

```python
from kalkan_xml_signer import XMLSigner

with XMLSigner(
    lib_path="libs/libkalkancryptwr-64.so.2.0.2",
    cert_path="certs/your_cert.p12",
    cert_password="your_password",
) as signer:
    signed_xml = signer.sign_xml("<root><data>test</data></root>")
    print(signed_xml)
```

### With timestamp

Для добавления метки времени от сервера TSA НУЦ РК:

```python
with XMLSigner(
    lib_path="libs/libkalkancryptwr-64.so.2.0.2",
    cert_path="certs/your_cert.p12",
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
signer = XMLSigner(lib_path="libs/libkalkancryptwr-64.so.2.0.2")
signer.init()
signer.load_certificate("certs/your_cert.p12", "password")
signed_xml = signer.sign_xml("<root/>")
signer.finalize()
```

## Docker

```dockerfile
FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends libltdl7 libpcsclite1 && rm -rf /var/lib/apt/lists/*

# Копируем библиотеку KalkanCrypt
COPY libs/libkalkancryptwr-64.so.2.0.2 /usr/lib/libkalkancryptwr-64.so.2.0.2

# Устанавливаем пакет
RUN pip install kalkan-xml-signer

# Устанавливаем корневые сертификаты НУЦ РК
RUN kalkan-install-certs

COPY . /app
WORKDIR /app
```

В коде указываете путь к библиотеке в контейнере:

```python
with XMLSigner(
    lib_path="/usr/lib/libkalkancryptwr-64.so.2.0.2",
    cert_path="certs/your_cert.p12",
    cert_password="your_password",
) as signer:
    signed_xml = signer.sign_xml("<root><data>test</data></root>")
```

## Requirements

- Python >= 3.10
- Linux (библиотека KalkanCrypt доступна только для Linux)
- Нативная библиотека `libkalkancryptwr-64.so` ([запросить SDK](https://pki.gov.kz/en/get-sdk-3/))
- Сертификат PKCS#12 (`.p12`), выданный НУЦ РК

## License

MIT
