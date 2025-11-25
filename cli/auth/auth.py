import requests

from bs4 import BeautifulSoup
import cli.utils.common as common
import cli.utils.string_util as util

from cli.auth.auth_exception import AuthError

CONTENT_TYPE = "application/vnd.ibm.powervm.web+xml; type=LogonRequest"
ACCEPT = "application/vnd.ibm.powervm.web+xml; type=LogonResponse"
URI = "/rest/api/web/Logon"

logger = common.get_logger("auth")


def populate_payload(config):
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<LogonRequest xmlns="http://www.ibm.com/xmlns/systems/power/firmware/web/mc/2012_10/" schemaVersion="V1_1_0">
    <Metadata>
        <Atom/>
    </Metadata>
    <UserID kb="CUR" kxe="false">{util.get_host_username(config)}</UserID>
    <Password kb="CUR" kxe="false">{util.get_host_password(config)}</Password>
</LogonRequest>
'''

def authenticate_hmc(config):
    try:
        # Populate Authentication payload
        payload = populate_payload(config)
        url = "https://" + util.get_host_address(config) + URI
        headers = {"Content-Type": CONTENT_TYPE, "Accept": ACCEPT}
        response = requests.put(url, headers=headers, data=payload, verify=False)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'xml')
        session_key = soup.find("X-API-Session")
    except requests.exceptions.RequestException as e:
        raise AuthError(f"failed to authenticate HMC while making http request, error: {e}, response: {e.response.text}")
    except Exception as e:
        raise AuthError(f"failed to authenticate HMC, error: {e}")
    return session_key.text, response.cookies

def delete_session(config, cookies):
    try:
        url = "https://" + util.get_host_address(config) + URI
        headers = {"x-api-key": util.get_session_key(config)}
        response = requests.delete(url, cookies=cookies, headers=headers, verify=False)
        response.raise_for_status()

        logger.debug("Logged off HMC session successfully")
    except requests.exceptions.RequestException as e:
        raise AuthError(f"failed to delete session on HMC while making http request, error: {e}, response: {e.response.text}")
    except Exception as e:
        raise AuthError(f"failed to delete session on HMC, error: {e}")
    return
