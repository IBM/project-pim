import json
import re
import requests

from bs4 import BeautifulSoup
from cli.network.virtual_network import get_network_uuid
from cli.utils.common import *
from cli.utils.string_util import *

logger = get_logger("validator")
supported_versions = ["1110.01", "1110.00", "1060.51", "1060.50", "1050.51",  "1050.50"]

def validate_config(config):
    is_mandatory_param_valid = validate_mandatory_params(config)
    is_digit_param_valid = validate_digit_params(config)
    is_param_value_valid = validate_params_value(config)

    return all([is_mandatory_param_valid, is_digit_param_valid, is_param_value_valid])

def validate_rollback_config(config):
    params_validators= [
        validate_ip_addresses,
        validate_ssh_keys,
    ]

    if get_ai_app_request(config) == "yes":
        params_validators.append(validate_ai_app_validator)

    return all ( validator(config) for validator in params_validators)

def validate_upgrade_config(config):
    params_validators= [
        validate_ip_addresses,
        validate_ssh_keys,
        validate_auth_json,
    ]

    if get_ai_app_request(config) == "yes":
        params_validators.append(validate_ai_app_validator)

    return all ( validator(config) for validator in params_validators)

def validate_mandatory_params(config):
    parameter_list = [
        # System parameter validations
        (get_system_name, "system.name"),
        (get_host_address, "system.hmc.host-address"),
        (get_host_username, "system.hmc.user-name"),
        (get_host_password, "system.hmc.password"),

        # AI parameter validations
        (get_bootstrap_iso_download_url, "bootstrap-iso.url"),
        (get_workload_image, "ai.image"),
        
        # Partition parameter validations
        (get_partition_name, "partition.name"),
        (get_partition_flavor, "partition.flavor"),
        (get_vswitch_name, "partition.network.connection.virtual-switch-name"),
        (get_vnetwork_name, "partition.network.connection.virtual-network-name"),
        (get_ip_address, "partition.network.ip.address"),
        (get_network_gateway, "partition.network.ip.gateway"),
        (get_network_nameserver, "partition.network.ip.nameserver"),

        (get_sharing_mode, f"{get_flavor_name(config)}.cpu.sharing-mode")
    ]

    if get_ai_app_request(config) == "yes":
        parameter_list.append((get_ai_app_url, "ai.validation.url"))
        parameter_list.append((get_ai_app_method, "ai.validation.method"))

    is_valid = True
    for get_param_value, param_name in parameter_list:
        if get_param_value(config) == "":
            logger.error(f"validation failed: '{param_name}' must not be empty")
            is_valid = False

    return is_valid

def validate_digit_params(config):
    flavor_name = get_flavor_name(config)
    parameter_list =  [
        (get_network_prefix_length, "partition.network.ip.prefix-length"),
        # Memory validations
        (get_required_disk_size, "partition.storage.size"),
    ]
    memory_params = [
        (get_desired_memory, f"{flavor_name}.memory.desired-memory"),
        (get_max_memory, f"{flavor_name}.memory.max-memory"),
        (get_min_memory, f"{flavor_name}.memory.min-memory")
    ]
    cpu_params = []
    if has_dedicated_proc(config) == "true":
        cpu_params = [
            (get_desired_proc, f"{flavor_name}.cpu.dedicated.desired-proc-unit"),
            (get_max_proc, f"{flavor_name}.cpu.dedicated.max-proc-unit"),
            (get_min_proc, f"{flavor_name}.cpu.dedicated.min-proc-unit")
        ]
    else:
        cpu_params = [
            (get_shared_desired_proc, f"{flavor_name}.cpu.shared.desired-proc-unit"),
            (get_shared_max_proc, f"{flavor_name}.cpu.shared.max-proc-unit"),
            (get_shared_min_proc, f"{flavor_name}.cpu.shared.min-proc-unit"),
            (get_shared_desired_virt_proc, f"{flavor_name}.cpu.shared.desired-virt-proc"),
            (get_shared_max_virt_proc, f"{flavor_name}.cpu.shared.max-virt-proc"),
            (get_shared_min_virt_proc, f"{flavor_name}.cpu.shared.min-virt-proc")
        ]
    parameter_list.extend(cpu_params)
    parameter_list.extend(memory_params)
        
    is_valid = True
    for get_digit, param_name in parameter_list:
        if not get_digit(config).isdigit():
            logger.error(f"validation failed: '{param_name}' must be an integer")
            is_valid = False
    
    for get_memory_param, param_name in memory_params:
        value = get_memory_param(config)
        if value.isdigit() and int(value) % 2 != 0:
            logger.error(f"validation failed: '{param_name}' must be an even integer")
            is_valid = False

    return is_valid

def validate_params_value(config):
    params_validators = [
        validate_partition_name,
        validate_partition_flavor,
        validate_prefix_length,
        validate_desired_memory,
        validate_system_name,
        validate_bootstrap_url,
        validate_ip_addresses,
        validate_ssh_keys,
        validate_auth_json,
        validate_pim_config_json,
        validate_cpu_mode
    ]
    if has_dedicated_proc(config):
        params_validators.append(validate_dedicated_desired_proc)

    if get_ai_app_request(config) == "yes":
        params_validators.append(validate_ai_app_validator)

    return all ( validator(config) for validator in params_validators)

def validate_networks(config, cookies, system_uuid):
    network_validator = [
        validate_virtual_network_name,
        validate_virtual_switch_name
    ]

    return all( validator(config, cookies, system_uuid) for validator in network_validator )

def validate_ip_addresses(config):
    pattern = r"^((25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)$"
    parameter_list = [
        (get_ip_address, "partition.network.ip.address"),
        (get_network_gateway, "partition.network.ip.gateway")
    ]

    is_valid = True
    for get_param_value, name in parameter_list:
        result = re.match(pattern, get_param_value(config))
        if not bool(result):
            logger.error(f"validation failed: '{name}' must be a ip address.")
            is_valid = False
    return is_valid

def validate_prefix_length(config):
    value = get_network_prefix_length(config)
    if value.isdigit() and int(value) <= 32:
        return True
    logger.error("validation failed: 'partition.network.ip.prefix-length' value must be less then or equal to 32.")

# Validating partition is in correct format
def validate_partition_name(config):
    pattern = r"^[^()\<>*\$&?\|\[\]'\"`]{1,47}$"
    result = re.match(pattern, get_partition_name(config))
    if not bool(result):
        logger.error(f"validation failed: 'partition.name' value '{get_partition_name(config)}' have invalid format.")
    return bool(result)

def validate_partition_flavor(config):
    value = get_partition_flavor(config)
    defined_flavor_list = list_defined_partition_flavor()
    possible_values = ["custom"]
    possible_values.extend(defined_flavor_list)
    if value in possible_values:
        return True
    logger.error(f"validation failed: 'partition.flavor' must filled with {possible_values}.")
    return False

# Validating memory parameter:  Memory should be greater then or equal to 32GB
def validate_desired_memory(config):
    value = get_desired_memory(config)
    if value.isdigit() and int(value) >= 32:
        return True
    logger.error(f"validation failed: '{get_flavor_name(config)}.memory.desired-memory' must have greater then or equal to 32 GB of memory")
    return False

def validate_cpu_mode(config):
    value = get_cpu_mode(config)
    possible_values = [ "dedicated", "shared"]
    if value in possible_values:
        return True
    logger.error(f"validation failed: '{get_flavor_name(config)}.cpu.mode' must filled with {possible_values}")

# Validating cpu parameter: Minimum requiment for the desired cpu must be greater or equal to 1 
def validate_dedicated_desired_proc(config):
    value = get_desired_proc(config)
    if value.isdigit() and int(value) >= 1:
        return True
    logger.error(f"validation failed: '{get_flavor_name(config)}.cpu.dedicated.desired-proc-unit' must be greater then or equal to 1 proc-unit")
    return False

# A System Name must contain 1-31 characters. The only special characters that are disallowed are: ( ) < > * $ & ? | [ ] ' " `
def validate_system_name(config):
    pattern = r"^[^\(\)<>\*\$\&\?|\[\]\'\"\`]{1,31}$"
    result = re.match(pattern, get_system_name(config))
    if not bool(result):
        logger.error(f"validation failed: 'system.name' value '{get_system_name(config)}' have invalid format.")
    return bool(result)

def validate_url(url):
    pattern = "^https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)$"
    return re.match(pattern, url)

# Validate the correctness of the bootstrap URL format
def validate_bootstrap_url(config):
    result = validate_url(get_bootstrap_iso_download_url(config))
    if not bool(result):
        logger.error(f"validation failed: 'bootstrap-iso.url' value '{get_bootstrap_iso_download_url(config)}' must be a url")
    return bool(result)

# Validate ssh key section
def validate_ssh_keys(config):
    pub_key_file = get_ssh_pub_key(config)
    priv_key_file = get_ssh_priv_key(config)

    if pub_key_file != "" and priv_key_file != "":
        return True
    elif pub_key_file != "" or priv_key_file != "":
        return False
    return True

# Validate if the provided virtual network name exists in the system
def validate_virtual_network_name(config, cookies, system_uuid):
    uuid = get_network_uuid(config, cookies, system_uuid)
    return uuid != ""

# Validate if the provided virtual switch name exists in the system
def validate_virtual_switch_name(config, cookies, system_uuid):
    uri = f"/rest/api/uom/ManagedSystem/{system_uuid}/VirtualSwitch/quick/All"
    url = "https://" +  get_host_address(config) + uri
    headers = {"x-api-key": get_session_key(config), "Content-Type": "application/vnd.ibm.powervm.uom+xml"}
    response = requests.get(url, headers=headers, cookies=cookies, verify=False)
    if response.status_code != 200:
        logger.error(f"failed to list virtual switch. {response.text}")
        raise Exception("failed to list virtual switch")
    
    found = False
    for switch in response.json():
        # Remove '(Default)' from switch name before checking equality
        if switch["SwitchName"].rstrip("(Default)") == get_vswitch_name(config):
            found = True
            break
    
    if not found:
        logger.error(f"validation failed: 'partition.network.connection.virtual-switch-name' value '{get_vswitch_name(config)}' is not present in system")

    return found

def validate_json(value, field):
    if value != "":
        try:
            json.loads(value)
            return True
        except Exception as e:
            logger.error(f"validation failed: '{field}' must have valid json value. {e}")
            return False
    return True

def validate_auth_json(config):
    return validate_json(get_auth_json(config), "ai.auth-json")

def validate_pim_config_json(config):
    return validate_json(get_pim_config_json(config), "ai.config-json")

def validate_ai_app_validator(config):
    result = True

    url = get_ai_app_url(config)
    if not bool(validate_url(url)):
        logger.error(f"validation failed: 'ai.validation.url' value '{url}' must be a url")
        result = False

    method = get_ai_app_method(config)
    if method != "GET" and method != "POST":
        logger.error(f"validation failed: 'ai.validation.method' value '{method}' must be either GET or POST")
        result = False

    payload = get_ai_app_payload(config)
    if not validate_json(payload, "ai.validation.payload"):
        result = False

    headers = get_ai_app_headers(config)
    if headers != "" and not validate_json(headers, "ai.validation.headers"):
        result = False
    
    return result

def get_flavor_name(config):
     if has_custom_flavor(config):
        return "custom-flavor"
     return get_partition_flavor(config)


def validate_host_config(config, cookies, system_uuid):
    uri = f"/rest/api/uom/ManagedSystem/{system_uuid}"
    url =  "https://" + util.get_host_address(config) + uri
    headers = {"x-api-key": util.get_session_key(config)}
    response = requests.get(url, headers=headers, cookies=cookies, verify=False)
    if response.status_code != 200:
        logger.error(f"failed to get system firmware version: {response.text}")
        return

    soup = BeautifulSoup(response.text, 'xml')
    fw_version = soup.find("SystemFirmware").text

    for supported_version in supported_versions:
        if supported_version in fw_version:
            return True
    logger.error(f"Unsupported firmware version: '{fw_version}', supported versions: '{supported_versions}'")
    return False
