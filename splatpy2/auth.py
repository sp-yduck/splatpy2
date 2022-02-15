import os
import base64
import hashlib
import json
import time
import uuid

import requests
from urllib.parse import urljoin

from splatpy2.utils import qsd_from_url_fragment


class SplatpyAuth(object):
    def __init__(self):
        self.nintendo_url = "https://accounts.nintendo.com/connect/1.0.0/"
        self.version = "1.14.0"

    
    def auth_flow(self):
        session_token = self.get_session_token()
        service_token, _ = self.get_service_token(session_token)
        user_info = self.get_user_info(service_token)
        login_params = self.get_login_params(service_token, user_info)
        access_token = self.login_to_account(login_params, service_token)
        splatoon_access_token = self.get_splatoon_access_token(access_token)
        print("now you can use Splatoon2 Web API !!  <コ:ミ ~ ")
        return splatoon_access_token


    def gen_login_url(self):
        state = base64.urlsafe_b64encode(os.urandom(36))

        code_verifier = base64.urlsafe_b64encode(os.urandom(32))
        hash = hashlib.sha256()
        hash.update(code_verifier.replace(b"=", b""))
        code_challenge = base64.urlsafe_b64encode(hash.digest())
        
        head = {
            'Host': 'accounts.nintendo.com',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': f"OnlineLounge/{self.version} NASDKAPI iOS",
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8n',
            'DNT': '1',
            'Accept-Encoding': 'gzip,deflate,br',
        }

        body = {
            'state': state,
            'redirect_uri': 'npf71b963c1b7b6d119://auth', # for Nintendo Switch Online. It's different from for Nintendo Parental Online
            'client_id': '71b963c1b7b6d119', # client_id is a constant value (common to all users)
            'scope': 'openid user user.birthday user.mii user.screenName',
            'response_type': 'session_token_code',
            'session_token_code_challenge': code_challenge.replace(b"=", b""),
            'session_token_code_challenge_method': 'S256',
            'theme': 'login_form',
        }

        authorize_url = urljoin(self.nintendo_url, "authorize")
        r = requests.get(authorize_url, params=body, headers=head)
        try:
            r.raise_for_status()
            login_url = r.history[0].url
            print("Successful generate the login-url. Open the link down below.")
            print(login_url)
        except requests.exceptions.RequestException as e:
            print(r.text, e)
            raise e

        return login_url, code_verifier


    def get_session_token(self):
        _, code_verifier = self.gen_login_url()
        auth_url = input("Paste copied link address here: \n")
        session_token_code = qsd_from_url_fragment(auth_url)["session_token_code"][0]

        body = {
            'client_id': '71b963c1b7b6d119',
            'session_token_code': session_token_code,
            'session_token_code_verifier': code_verifier.replace(b"=", b""),
	    }

        session_token_url = urljoin(self.nintendo_url, "api/session_token")
        r = requests.post(session_token_url, data=body)
        try:
            r.raise_for_status()
            session_token = json.loads(r.text)["session_token"]
            print('Successful get the session-token !!')
        except requests.exceptions.RequestException as e:
            print(r.text, e)
            raise e

        return session_token

    
    def get_service_token(self, session_token):
        head = {
            'Host': "accounts.nintendo.com",
            'Content-Type': "application/json; charset=utf-8",
            'Connection': "keep-alive",
            'User-Agent': f"OnlineLounge/{self.version} NASDKAPI iOS",
            'Accept-Language': "en-US",
            'Accept-Encording': "gzip,deflate",
        }
        body = {
            'client_id': "71b963c1b7b6d119",
            'grant_type': "urn:ietf:params:oauth:grant-type:jwt-bearer-session-token",
            "session_token": session_token,
        }

        token_url = urljoin(self.nintendo_url, "api/token")
        r = requests.post(token_url, json=body, headers=head)
        try:
            r.raise_for_status()
            service_token = json.loads(r.text)["access_token"]
            id_token = json.loads(r.text)["id_token"]
            print('Successful get the service-token.')
        except requests.exceptions.RequestException as e:
            print(r.text, e)
            raise e

        return service_token, id_token


    def login_to_account(self, login_params, service_token):
        head = {
            'Host': "api-lp1.znc.srv.nintendo.net",
            'Content-Type': "application/json",
            'Connection': "keep-alive",
            'User-Agent': f"OnlineLounge/{self.version} NASDKAPI Android",
            'Accept-Language': "en-US",
            'Accept-Encording': "gzip",
            "Authorization": f"Bearer {service_token}",
            "X-Platform": "Android", # you need to specify Android (may be due to the Android emulator used in flapg_api)
            "X-ProductVersion": f"{self.version}"
        }
        body = {
            "parameter": login_params
        }

        account_login_url = "https://api-lp1.znc.srv.nintendo.net/v1/Account/Login"
        r = requests.post(account_login_url, json=body, headers=head)
        try:
            r.raise_for_status()
            try:
                access_token = json.loads(r.text)["result"]["webApiServerCredential"]["accessToken"]
                print('Successful get the access-token.')
            except:
                print(r.text)
        except requests.exceptions.RequestException as e:
            print(r.text, e)
            raise e

        return access_token


    def get_login_params(self, service_token, user_info):
        flapg_nso = self.call_flapg_api(service_token, 'nso')
        
        parameter = {
            'f':          flapg_nso["f"],
			'naIdToken':  flapg_nso["p1"],
			'timestamp':  flapg_nso["p2"],
			'requestId':  flapg_nso["p3"],
			'naCountry':  user_info["country"],
			'naBirthday': user_info["birthday"],
			'language':   user_info["language"],
		}

        return parameter


    def call_flapg_api(self, service_token, type):
        timestamp = int(time.time())
        guid = str(uuid.uuid4())
        
        head = {
            'x-token': service_token,
            'x-time':  str(timestamp),
            'x-guid':  guid,
            'x-hash':  self.call_s2s_api(service_token, timestamp),
            'x-ver':   '3',
            'x-iid':   type
        }
        flapg_api_url = "https://flapg.com/ika2/api/login?public"
        r = requests.get(flapg_api_url, headers=head)
        try:
            r.raise_for_status()
            f = json.loads(r.text)["result"]
            print('Successful get the f-parameter.')
        except requests.exceptions.RequestException as e:
            print(r.text, e)
            raise e
            
        return f


    def call_s2s_api(self, id_token, timestamp):
        head = {'User-Agent': f"OnlineLounge/{self.version} NASDKAPI iOS"}
        body = {'naIdToken': id_token, 'timestamp': timestamp }
        s2s_url = "https://elifessler.com/s2s/api/gen2"
        r = requests.post(s2s_url, headers=head, data=body)
        try:
            r.raise_for_status()
            hash = json.loads(r.text)["hash"]
            print('Successful get the hash.')
        except requests.exceptions.RequestException as e:
            print(r.text, e)
            raise e

        return hash


    def get_user_info(self, service_token):
        print(service_token)
        head = {
			'User-Agent': f"OnlineLounge/{self.version} NASDKAPI iOS",
			'Accept-Language': "en-US",
			'Accept': 'application/json',
			'Authorization': f'Bearer {service_token}',
			'Host': 'api.accounts.nintendo.com',
			'Connection': 'Keep-Alive',
			'Accept-Encoding': 'gzip'
		}
        me_url = "https://api.accounts.nintendo.com/2.0.0/users/me"
        r = requests.get(me_url, headers=head)
        try:
            r.raise_for_status()
            user_info = json.loads(r.text)
            print('Successful get the user(your) infomation.')
        except requests.exceptions.RequestException as e:
            print(r.text, e)
            raise e

        return user_info


    def get_splatoon_access_token(self, access_token):
        head = {
            "Host": "api-lp1.znc.srv.nintendo.net",
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": "0",
            "Connection": "keep-alive",
            "X-ProductVersion": f"{self.version}",
            "Accept": "application/json",
            "User-Agent": f"OnlineLounge/{self.version} NASDKAPI iOS",
            "Accept-Language": "en-us",
            "X-Platform": "iOS",
            "Authorization": f"Bearer"
        }

        flapg_app = self.call_flapg_api(access_token, 'app')
        body = {
            "parameter": {
                'id':                5741031244955648,
                'f':                 flapg_app["f"],
                'registrationToken': flapg_app["p1"],
                'timestamp':         flapg_app["p2"],
                'requestId':         flapg_app["p3"],
            }
        }

        game_token_url = "https://api-lp1.znc.srv.nintendo.net/v2/Game/GetWebServiceToken"
        r = requests.post(game_token_url, headers=head, json=body)
        try:
            r.raise_for_status()
            splatoon_access_token = json.loads(r.text)
            print('Successful get the splatoon access token.')
        except requests.exceptions.RequestException as e:
            print(r.text, e)
            raise e

        return splatoon_access_token