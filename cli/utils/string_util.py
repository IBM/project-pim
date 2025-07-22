import hashlib


def get_system_name(config):
    return config["system"]["name"]

def get_host_address(config):
    return config["system"]["hmc"]["host-address"]

def get_host_username(config):
    return config["system"]["hmc"]["user-name"]

def get_host_password(config):
    return config["system"]["hmc"]["password"]

def get_vios_address(config):
    return config["system"]["vios-server"]["host-address"]

def get_session_key(config):
    return  config["session"]["x-api-key"]

def get_bootstrap_iso(config):
    return hashlib.sha256(get_bootstrap_iso_download_url(config).encode()).hexdigest()[:32] + "_pimb"

def get_cloud_init_iso(config):
    return get_partition_name(config).lower() + "_pimc"

# partition related Getters
def get_desired_memory(config):
    return config["partition-flavor"]["memory"]["desired-memory"]

def get_max_memory(config):
    return config["partition-flavor"]["memory"]["max-memory"]

def get_min_memory(config):
    return config["partition-flavor"]["memory"]["min-memory"]

def get_desired_proc(config):
    return config["partition-flavor"]["cpu"]["dedicated"]["desired-proc-unit"]

def get_max_proc(config):
    return config["partition-flavor"]["cpu"]["dedicated"]["max-proc-unit"]

def get_min_proc(config):
    return config["partition-flavor"]["cpu"]["dedicated"]["min-proc-unit"]

def get_shared_desired_proc(config):
    return config["partition-flavor"]["cpu"]["shared"]["desired-proc-unit"]

def get_shared_max_proc(config):
    return config["partition-flavor"]["cpu"]["shared"]["max-proc-unit"]

def get_shared_min_proc(config):
    return config["partition-flavor"]["cpu"]["shared"]["min-proc-unit"]

def get_shared_desired_virt_proc(config):
    return config["partition-flavor"]["cpu"]["shared"]["desired-virt-proc"]

def get_shared_max_virt_proc(config):
    return config["partition-flavor"]["cpu"]["shared"]["max-virt-proc"]

def get_shared_min_virt_proc(config):
    return config["partition-flavor"]["cpu"]["shared"]["min-virt-proc"]

def has_dedicated_proc(config):
    return  "true" if config["partition-flavor"]["cpu"]["mode"] == "dedicated" else "false"

def get_cpu_mode(config):
    return config["partition-flavor"]["cpu"]["mode"]

def get_sharing_mode(config):
    return config["partition-flavor"]["cpu"]["sharing-mode"]

def get_partition_type(config):
    return "AIX/Linux"

def get_partition_name(config):
    return config["partition"]["name"]

def get_partition_flavor(config):
    return config["partition"]["flavor"]

def has_custom_flavor(config):
    return config["partition"]["flavor"] == "custom"

# Network config Getters
def get_vswitch_name(config):
    return config["partition"]["network"]["connection"]["virtual-switch-name"]

def get_vnetwork_name(config):
    return config["partition"]["network"]["connection"]["virtual-network-name"]

def get_ip_address(config):
    return config["partition"]["network"]["ip"]["address"]

def get_network_prefix_length(config):
    return config["partition"]["network"]["ip"]["prefix-length"]

def get_network_gateway(config):
    return config["partition"]["network"]["ip"]["gateway"]

def get_network_nameserver(config):
    return config["partition"]["network"]["ip"]["nameserver"]

def get_ssh_username(config):
    return config["ssh"]["user-name"]

def get_ssh_priv_key(config):
    return config["ssh"]["priv-key-file"]

def get_ssh_pub_key(config):
    return config["ssh"]["pub-key-file"]

# storage related Getters
def get_volume_group_name(config):
    return config["virtual-disk"]["vg_name"]

def get_virtual_disk_name(config):
    return config["virtual-disk"]["vdisk_name"]

def use_logical_volume(config):
    return config["virtual-disk"].as_bool("use_logical_volume")

def get_virtual_disk_size(config):
    return config["virtual-disk"]["vdisk_size"]

def get_required_disk_size(config):
    return config["partition"]["storage"]["size"]

def get_bootstrap_iso_download_url(config):
    return config["bootstrap-iso"]["url"]

def get_workload_image(config):
    return config["ai"]["image"]

def get_pim_config_json(config):
    return config["ai"]["config-json"]

def get_auth_json(config):
    return config["ai"]["auth-json"]

def get_ai_app_request(config):
    return config["ai"]["validation"]["request"]

def get_ai_app_url(config):
    return config["ai"]["validation"]["url"]

def get_ai_app_method(config):
    return config["ai"]["validation"]["method"]

def get_ai_app_headers(config):
    return config["ai"]["validation"]["headers"]

def get_ai_app_payload(config):
    return config["ai"]["validation"]["payload"]
