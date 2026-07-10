import json
import requests

import cli.utils.string_util as util

def check_app(config):
    try:
        headers = json.loads(util.get_ai_app_headers(config)) if util.get_ai_app_headers(config) != "" else None
        verify = util.get_ai_app_verify_ssl(config)
        response = requests.request(util.get_ai_app_method(config), util.get_ai_app_url(config), data=util.get_ai_app_payload(config), headers=headers, verify=verify)
        if response.status_code >= 200 and response.status_code < 300:
            return True, response.text
    except Exception as e:
        return False, f"AI application validation request errored, error: {e}, will retry..."
    
    return False, f"AI application validation request didn't succeed yet, response: '{response.text}', code: '{response.status_code}', will retry..."
