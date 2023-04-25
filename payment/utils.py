import base64

import requests

def get_paypal_access_token(client_id, client_secret, endpoint_url):
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {auth}",
    }
    response = requests.post(f"{endpoint_url}/v1/oauth2/token", data="grant_type=client_credentials", headers=headers)
    data = response.json()
    return data["access_token"]


def generate_client_token(access_token, endpoint_url):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept-Language": "en_US",
        "Content-Type": "application/json",
    }
    response = requests.post(f"{endpoint_url}/v1/identity/generate-token", headers=headers)
    data = response.json()
    return data["client_token"]
