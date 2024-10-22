import base64
import hashlib
import logging
import requests

logger = logging.getLogger(__name__)

OID_NIST_SHA1 = "1.3.14.3.2.26"
OID_NIST_SHA256 = "2.16.840.1.101.3.4.2.1"
OID_RSA_RSA = "1.2.840.113549.1.1.1"
BASE_URL = "https://remotesigning.viettel.vn:8773"


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
                "async": 1
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
    def generate_base64_sha256(file_data):
        sha256_hash = hashlib.sha256(file_data).digest()
        base64_hash = base64.b64encode(sha256_hash).decode("utf-8")
        print("base64_hash", base64_hash)
        print("base64_hash Len", len(base64_hash))
        return base64_hash
