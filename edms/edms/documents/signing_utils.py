import base64
import hashlib
import logging
import datetime
import pickle
from io import BytesIO

import requests
from asn1crypto import cms, core, util, x509, algos
from endesive import pdf
from pyhanko.pdf_utils import images
from pyhanko.sign.fields import SigSeedSubFilter
from pyhanko import stamp
import asyncio
from pyhanko.sign import signers, fields
logger = logging.getLogger(__name__)

OID_NIST_SHA1 = "1.3.14.3.2.26"
OID_NIST_SHA256 = "2.16.840.1.101.3.4.2.1"
OID_RSA_RSA = "1.2.840.113549.1.1.1"
BASE_URL = "https://remotesigning.viettel.vn:8773"
BYTES_RESERVED = 16384


class Signer:
    def __init__(self, cert, sig, tosign):
        self.cert = cert
        self.sig = sig
        self.tosign = tosign
        self.mech = None

    def certificate(self):
        return 1, self.cert

    def sign(self, keyid, data, mech):
        if self.tosign:
            assert self.tosign == data
        self.tosign = data
        self.mech = mech
        if self.sig is None:
            sig = None
            if mech == "sha256":
                sig = b"\0" * 256
            return sig
        return self.sig


class MySignHelper:
    @staticmethod
    def get_all_certificates(user_id, base_url, client_id, client_secret, profile_id):
        cert_list = {}
        access_token = ""
        try:
            # Step 1: Login to Cloud CA
            response = MySignHelper.login(user_id, base_url, client_id, client_secret, profile_id)
            if not response or not response.get("access_token"):
                logger.error("ERROR: Login to Cloud CA")
                return cert_list, access_token

            access_token = response["access_token"]
            credentials_response = MySignHelper.get_credentials_list(client_id, client_secret, profile_id, user_id, access_token, base_url)
            if not credentials_response or credentials_response.status_code == 400:
                logger.error("ERROR: Get Credentials list: %s", credentials_response.json().get("error_description"))
                return cert_list, access_token

            for item in credentials_response.json():
                cert_list[item["credential_id"]] = item["cert"]
            return cert_list, access_token
        except Exception as e:
            logger.error(e)
        return cert_list, access_token

    @staticmethod
    def sign_hash(hash_list, document_id, document_name, client_id, client_secret, credential_id, base_url, access_token):
        try:
            # Step 4: Get SAD
            num_signatures = len(hash_list)
            documents = [{"document_id": document_id, "document_name": document_name} for _ in range(num_signatures)]

            # Step 5: Sign hash
            hash_algo = OID_NIST_SHA1 if len(hash_list[0]) == 28 else OID_NIST_SHA256
            sign_algo = OID_RSA_RSA

            sign_hash_response = MySignHelper.sign_hash_api(client_id, client_secret, credential_id, access_token, num_signatures, documents, hash_list, hash_algo, sign_algo, base_url)

            if not sign_hash_response or sign_hash_response.get("error"):
                logger.error("ERROR: Sign Hash: %s", sign_hash_response.get("error_description"))
                return None

            return sign_hash_response
        except Exception as e:
            logger.error(e)
        return None

    @staticmethod
    def login(user_id, base_url, client_id, client_secret, profile_id):
        try:
            url = f"{base_url}/vtss/service/ras/v1/login"
            request_data = {
                "client_id": client_id,
                "user_id": user_id,
                "client_secret": client_secret,
                "profile_id": profile_id
            }
            response = requests.post(url, json=request_data).json()
            return response
        except Exception as e:
            logger.error("Error: %s", e)
            return None

    @staticmethod
    def client_authenticate(base_url, client_id, client_secret):
        try:
            url = f"{base_url}/vtss/service/ras/v1/authenticate"
            request_data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials"
            }
            response = requests.post(url, data=request_data)
            return response
        except Exception as e:
            logger.error("Error: %s", e)
            return None

    @staticmethod
    def get_credentials_list(client_id, client_secret, profile_id, user_id, access_token, base_url):
        try:
            url = f"{base_url}/vtss/service/certificates/info"
            request_data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "profile_id": profile_id,
                "user_id": user_id,
                "certificates": "chain",
                "certInfo": True,
                "authInfo": True
            }
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.post(url, json=request_data, headers=headers)
            return response
        except Exception as e:
            logger.error("Error: %s", e)
            return None

    @staticmethod
    def get_sign_status(access_token, base_url, transaction_id):
        try:
            url = f"{base_url}/vtss/service/requests/status"
            request_data = {
                "transactionId": transaction_id,
            }
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.post(url, json=request_data, headers=headers).json()
            return response
        except Exception as e:
            logger.error("Error: %s", e)
            return None

    @staticmethod
    def sign_hash_api(client_id, client_secret, credential_id, access_token, num_signatures, documents, hashes, hash_algo, sign_algo, base_url):
        try:
            url = f"{base_url}/vtss/service/signHash"
            request_data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "credentialID": credential_id,
                "numSignatures": num_signatures,
                "documents": documents,
                "hash": hashes,
                "hashAlgo": hash_algo,
                "signAlgo": sign_algo,
                "async": 2
            }
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.post(url, json=request_data, headers=headers).json()
            return response
        except Exception as e:
            logger.error("Error: %s", e)
            return None

    @staticmethod
    def convert_string2base64(s):
        encoded_name = base64.b64encode(s.encode('utf-8')).decode('utf-8')
        return encoded_name

    @staticmethod
    def get_cert509(base64_certificate: str):
        decoded_certificate = base64.b64decode(base64_certificate)
        cert = x509.Certificate.load(decoded_certificate)
        return cert

    @staticmethod
    def generate_base64_sha256(file_data):
        sha256_hash = hashlib.sha256(file_data).digest()
        base64_hash = base64.b64encode(sha256_hash).decode("utf-8")
        return base64_hash

    @staticmethod
    def generate_attrs(signed_value, signed_time):
        return [
            cms.CMSAttribute(
                {"type": cms.CMSAttributeType("content_type"), "values": ("data",)}
            ),
            cms.CMSAttribute(
                {
                    "type": cms.CMSAttributeType("message_digest"),
                    "values": (signed_value,),
                }
            ),
            cms.CMSAttribute(
                {
                    "type": cms.CMSAttributeType("signing_time"),
                    "values": (cms.Time({"utc_time": core.UTCTime(signed_time)}),),
                }
            ),
        ]

    @staticmethod
    def get_signing_time():
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        signing_date_str = now.strftime("%Y%m%d%H%M%S+00'00'")
        signing_time = datetime.datetime(
            now.year, now.month, now.day, now.hour, now.minute, now.second, 0, timezone.utc
        )
        return signing_date_str, signing_time

    @staticmethod
    def generate_dtbs(file_data, sigpage, signature_box, signature_img, cert, signer, id, new_id):
        def attrs(signed_value):
            result = [
                cms.CMSAttribute(
                    {"type": cms.CMSAttributeType("content_type"), "values": ("data",)}
                ),
                cms.CMSAttribute(
                    {
                        "type": cms.CMSAttributeType("message_digest"),
                        "values": (signed_value,),
                    }
                ),
                cms.CMSAttribute(
                    {
                        "type": cms.CMSAttributeType("signing_time"),
                        "values": (cms.Time({"utc_time": core.UTCTime(signed_time)}),),
                    }
                ),
            ]
            return result

        dct = {
            "aligned": 16384,
            "sigflags": 3,
            "sigflagsft": 132,
            "sigpage": sigpage,
            "auto_sigfield": True,
            "contact": f"{signer.email}",
            "location": "Đà Nẵng",
            "reason": f"{signer.name}<{signer.email}> đã ký lên văn bản này!",
            "application": "DMT Office",
            "signature_img": signature_img,
            "signaturebox": signature_box,
            "newid": str(new_id),
            "id": str(id).encode(),
            "attrs": attrs
        }
        when = datetime.datetime.now(tz=datetime.timezone.utc)
        signing_date = when.strftime("%Y%m%d%H%M%S+00'00'")
        dct["signingdate"] = signing_date.encode()
        signed_time = datetime.datetime(
            when.year, when.month, when.day, when.hour, when.minute, when.second, 0, util.timezone.utc
        )
        cert = cert.encode('ascii')

        clshsm = Signer(cert, None, None)
        cls = pdf.cms.SignedData()
        cls.sign(file_data, dct, None, None, [], "sha256", clshsm, mode="sign")

        tosign = b"".join(base64.encodebytes(clshsm.tosign).split()).decode('ascii')
        b64decoded_tosign = base64.b64decode(tosign)
        hashed_tosign = hashlib.sha256(b64decoded_tosign).digest()
        dtbs = base64.b64encode(hashed_tosign).decode("utf-8")
        dct.pop("attrs")
        return dtbs, tosign, dct

    @staticmethod
    def generate_signed_pdf(signature_data, pdf_data):
        def attrs(signed_value):
            result = [
                cms.CMSAttribute(
                    {"type": cms.CMSAttributeType("content_type"), "values": ("data",)}
                ),
                cms.CMSAttribute(
                    {
                        "type": cms.CMSAttributeType("message_digest"),
                        "values": (signed_value,),
                    }
                ),
                cms.CMSAttribute(
                    {
                        "type": cms.CMSAttributeType("signing_time"),
                        "values": (cms.Time({"utc_time": core.UTCTime(signed_time)}),),
                    }
                ),
            ]
            return result
        dct = signature_data["dct"]
        signingdate_str = dct["signingdate"].decode()
        signed_time = datetime.datetime.strptime(signingdate_str, "%Y%m%d%H%M%S+00'00'")
        signed_time = signed_time.replace(tzinfo=datetime.timezone.utc)
        dct["attrs"] = attrs
        cert = signature_data["certificate"].encode("ascii")
        signed_bytes = signature_data["signed_bytes"]
        if signed_bytes is not None:
            signed_bytes = base64.decodebytes(signed_bytes.encode("ascii"))
        tosign = signature_data["tosign"]
        if tosign is not None:
            tosign = base64.decodebytes(tosign.encode("ascii"))

        clshsm = Signer(cert, signed_bytes, tosign)

        datas = pdf.cms.SignedData().sign(pdf_data, dct, None, None, [], "sha256", clshsm, mode="sign")
        return pdf_data + datas

    @staticmethod
    def generate_pem_file_content(input_data):
        lines = input_data.strip().split("\n")
        base64_cert_data = "\n".join(lines)

        pem_content = (
            "-----BEGIN CERTIFICATE-----\n"
            f"{base64_cert_data}\n"
            "-----END CERTIFICATE-----\n"
        )
        return pem_content

    @staticmethod
    def instantiate_external_signer(signature_value, cert):
        return signers.ExternalSigner(
            signing_cert=cert,
            cert_registry=None,
            signature_value=signature_value,
            signature_mechanism=algos.SignedDigestAlgorithm({"algorithm": "sha256_rsa"}),
        )

    @staticmethod
    def prepare_document(file_data, sig_name, sigpage, signature_box, signature_img, cert, signer):
        ext_signer = MySignHelper.instantiate_external_signer(bytes(256), cert)
        pdf_signer = signers.PdfSigner(
            signature_meta=signers.PdfSignatureMetadata(
                field_name=sig_name,
                md_algorithm="sha256",
                location="Đà Nẵng",
                reason=f"{signer.name}<{signer.email}> đã ký lên văn bản này!",
                contact_info=f"{signer.email}",
                subfilter=SigSeedSubFilter.PADES
            ),
            new_field_spec=fields.SigFieldSpec(
                sig_field_name=sig_name,
                on_page=sigpage,
                box=signature_box,
            ),
            stamp_style=stamp.TextStampStyle(
                background=images.PdfImage(signature_img),
                stamp_text="",
                background_opacity=1,
                border_width=0
            ),
            signer=ext_signer,
        )
        prep_digest, tbs_document, output = asyncio.run(pdf_signer.async_digest_doc_for_signing(
            pdf_out=file_data,
            bytes_reserved=BYTES_RESERVED
        ))
        psi = tbs_document.post_sign_instructions
        signed_attrs = asyncio.run(ext_signer.signed_attrs(
            data_digest=prep_digest.document_digest,
            digest_algorithm='sha256',
            use_pades=True,
        ))
        return prep_digest, psi, signed_attrs, output

    @staticmethod
    def insert_signature_into_pdf(signature_data, signed_bytes):
        signature_data = pickle.loads(signature_data)
        prep_digest = signature_data['prep_digest']
        signed_attrs = cms.CMSAttributes.load(signature_data['signed_attrs'])
        psi = signature_data['psi']
        output = BytesIO(signature_data['output_handle'])
        cert = MySignHelper.get_cert509(signature_data['cert'])
        signature = base64.b64decode(signed_bytes)
        ext_signer = MySignHelper.instantiate_external_signer(signature, cert)
        content_info = asyncio.run(ext_signer.async_sign_prescribed_attributes(
            digest_algorithm="sha256",
            signed_attrs=signed_attrs,
        ))
        asyncio.run(signers.pdf_signer.PdfTBSDocument.async_finish_signing(
            output,
            prep_digest,
            content_info,
            post_sign_instr=psi,
        ))
        return output
