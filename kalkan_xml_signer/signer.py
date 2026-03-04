import ctypes as ct
from pathlib import Path
from typing import Optional


class XMLSigner:
    """
    Подпись XML документов с использованием библиотеки KalkanCrypt (Kazakhstan PKI).

    Поддерживает подпись XML с использованием сертификатов формата PKCS#12 (.p12).
    Работает через ctypes-обёртку над нативной библиотекой libkalkancryptwr-64.so.

    Пример использования:

        with XMLSigner(
            lib_path="/path/to/libkalkancryptwr-64.so.2.0.2",
            cert_path="/path/to/cert.p12",
            cert_password="password",
        ) as signer:
            signed_xml = signer.sign_xml("<root><data>test</data></root>")
    """

    # Флаги для подписи
    KC_WITH_TIMESTAMP = 0x100  # Добавить в подпись метку времени

    def __init__(
        self,
        lib_path: str,
        cert_path: Optional[str] = None,
        cert_password: Optional[str] = None,
        tsa_url: str = "http://tsp.pki.gov.kz:80",
    ):
        """
        Инициализация подписчика XML.

        :param lib_path: путь к библиотеке libkalkancryptwr-64.so
        :param cert_path: путь к файлу сертификата (.p12)
        :param cert_password: пароль от сертификата
        :param tsa_url: URL сервиса временных меток (TSA)
        """
        self.lib_path = lib_path
        self.cert_path = cert_path
        self.cert_password = cert_password
        self.tsa_url = tsa_url
        self._handle = None
        self._initialized = False

    def __enter__(self):
        """Вход в контекстный менеджер."""
        self.init()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекстного менеджера."""
        self.finalize()

    def _load_library(self):
        """Загрузка библиотеки KalkanCrypt."""
        if self._handle is None:
            try:
                self._handle = ct.CDLL(self.lib_path, mode=1)
                if not self._handle:
                    raise OSError(f"Не удалось загрузить библиотеку: {self.lib_path}")
            except OSError as e:
                raise RuntimeError(f"Ошибка при загрузке библиотеки: {e}")

    def _handle_error(self, error_code: int, method_name: str):
        """Обработка ошибок библиотеки."""
        if error_code != 0:
            error_len = ct.c_int(65535)
            error_msg = ct.create_string_buffer(error_len.value)
            if self._handle:
                self._handle.KC_GetLastErrorString(error_msg, ct.byref(error_len))
                error_text = error_msg.value.decode("utf-8", errors="ignore")
            else:
                error_text = "Unknown error"
            raise RuntimeError(f"{method_name} failed (code: 0x{error_code:08X}): {error_text}")

    def init(self):
        """Инициализация библиотеки и загрузка сертификата."""
        if self._initialized:
            return

        self._load_library()

        # Инициализация библиотеки
        err_code = self._handle.Init()
        self._handle_error(err_code, "KC_Init")

        # Загрузка сертификата, если указан
        if self.cert_path and self.cert_password:
            self.load_certificate(self.cert_path, self.cert_password)

        # Установка URL для TSA
        self.set_tsa_url(self.tsa_url)

        self._initialized = True

    def finalize(self):
        """Завершение работы с библиотекой."""
        if self._handle and self._initialized:
            if hasattr(self._handle, "KC_XMLFinalize"):
                self._handle.KC_XMLFinalize()
            if hasattr(self._handle, "KC_Finalize"):
                self._handle.KC_Finalize()
            self._initialized = False

    def load_certificate(self, cert_path: str, cert_password: str):
        """
        Загрузка сертификата.

        :param cert_path: путь к файлу сертификата
        :param cert_password: пароль от сертификата
        """
        if not self._handle:
            raise RuntimeError("Библиотека не загружена. Вызовите init()")

        if not Path(cert_path).exists():
            raise FileNotFoundError(f"Файл сертификата не найден: {cert_path}")

        self._handle.KC_LoadKeyStore.argtypes = [
            ct.c_int,      # storage type (1 = PKCS12)
            ct.c_char_p,   # password
            ct.c_int,      # password length
            ct.c_char_p,   # container path
            ct.c_int,      # container path length
            ct.c_char_p,   # alias
        ]
        self._handle.KC_LoadKeyStore.restype = ct.c_int

        store_type = ct.c_int(1)  # KCST_PKCS12
        password = cert_password.encode("utf-8")
        container = cert_path.encode("utf-8")
        alias = b""

        err_code = self._handle.KC_LoadKeyStore(
            store_type,
            password,
            ct.c_int(len(password)),
            container,
            ct.c_int(len(container)),
            alias,
        )
        self._handle_error(err_code, "KC_LoadKeyStore")

    def set_tsa_url(self, url: str = "http://tsp.pki.gov.kz:80"):
        """
        Установка URL сервиса временных меток (TSA).

        :param url: URL сервиса TSA
        """
        if not self._handle:
            return

        if hasattr(self._handle, "KC_TSASetUrl"):
            self._handle.KC_TSASetUrl.argtypes = [ct.c_char_p]
            self._handle.KC_TSASetUrl.restype = None
            self._handle.KC_TSASetUrl(url.encode("utf-8"))

    def sign_xml(
        self,
        xml: str,
        alias: str = "",
        flags: int = 0,
        sign_node_id: Optional[str] = None,
        parent_sign_node: Optional[str] = None,
        parent_namespace: Optional[str] = None,
    ) -> str:
        """
        Подпись XML документа.

        :param xml: XML документ в виде строки
        :param alias: алиас сертификата (по умолчанию пустая строка)
        :param flags: флаги для подписи (можно использовать KC_WITH_TIMESTAMP)
        :param sign_node_id: ID узла для подписи (опционально)
        :param parent_sign_node: родительский узел для вставки подписи (опционально)
        :param parent_namespace: пространство имен для parent_sign_node (опционально)
        :return: подписанный XML документ в виде строки
        """
        if not self._handle or not self._initialized:
            raise RuntimeError("Библиотека не инициализирована. Вызовите init() или используйте контекстный менеджер")

        xml_bytes = xml.encode("utf-8")
        xml_len = len(xml_bytes)

        out_len = ct.c_int(xml_len * 2 + 100000)
        out_buf = ct.create_string_buffer(out_len.value)

        c_alias = ct.c_char_p(alias.encode("utf-8")) if alias else ct.c_char_p(b"")
        c_xml = ct.c_char_p(xml_bytes)
        c_xml_len = ct.c_int(xml_len)
        c_flags = ct.c_int(flags)
        c_sign_node_id = ct.c_char_p(sign_node_id.encode("utf-8")) if sign_node_id else ct.c_char_p(b"")
        c_parent_sign_node = ct.c_char_p(parent_sign_node.encode("utf-8")) if parent_sign_node else ct.c_char_p(b"")
        c_parent_namespace = ct.c_char_p(parent_namespace.encode("utf-8")) if parent_namespace else ct.c_char_p(b"")

        self._handle.SignXML.argtypes = [
            ct.c_char_p,          # alias
            ct.c_int,             # flags
            ct.c_char_p,          # inData
            ct.c_int,             # inDataLength
            ct.c_char_p,          # outSign
            ct.POINTER(ct.c_int), # outSignLength
            ct.c_char_p,          # signNodeId
            ct.c_char_p,          # parentSignNode
            ct.c_char_p           # parentNamespace
        ]
        self._handle.SignXML.restype = ct.c_int

        err_code = self._handle.SignXML(
            c_alias,
            c_flags,
            c_xml,
            c_xml_len,
            out_buf,
            ct.byref(out_len),
            c_sign_node_id,
            c_parent_sign_node,
            c_parent_namespace,
        )

        self._handle_error(err_code, "SignXML")

        if hasattr(self._handle, "KC_XMLFinalize"):
            self._handle.KC_XMLFinalize()

        signed_xml = out_buf.raw[:out_len.value].decode("utf-8", errors="ignore")
        return signed_xml
