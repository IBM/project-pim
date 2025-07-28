import json
import logging
import os
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("hmc")

CONTENT_TYPE = "application/vnd.ibm.powervm.web+xml; type=LogonRequest"
ACCEPT = "application/vnd.ibm.powervm.web+xml; type=LogonResponse"
URI = "/rest/api/web/Logon"

def populate_payload(username, password):
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<LogonRequest xmlns="http://www.ibm.com/xmlns/systems/power/firmware/web/mc/2012_10/" schemaVersion="V1_1_0">
    <Metadata>
        <Atom/>
    </Metadata>
    <UserID kb="CUR" kxe="false">{username}</UserID>
    <Password kb="CUR" kxe="false">{password}</Password>
</LogonRequest>
'''
session_key = None
cookies = None

def authenticate_hmc():
    global session_key
    global cookies

    if session_key != None and cookies != None:
        return
    
    # Populate Authentication payload
    payload = populate_payload(os.getenv("HMC_USERNAME"), os.getenv("HMC_PASSWORD"))
    url = "https://" + os.getenv("HMC_IP") + URI
    headers = {"Content-Type": CONTENT_TYPE, "Accept": ACCEPT}
    response = requests.put(url, headers=headers, data=payload, verify=False)
    if response.status_code != 200:
        logger.error(f"failed to authenticate HMC, error: {response.text}")
        raise Exception(f"failed to authenticate HMC, error: {response.text}")

    soup = BeautifulSoup(response.text, 'xml')
    session = soup.find("X-API-Session")
    session_key = session.text
    cookies = response.cookies

def delete_session():
    url = "https://" + os.getenv("HMC_IP") + "/rest/api/web/Logon"
    headers = {"x-api-key": session_key}
    requests.delete(url, cookies=cookies, headers=headers, verify=False)
    return

def get_hmc_version():
    uri = f"/rest/api/uom/ManagementConsole"
    url =  "https://" + os.getenv("HMC_IP") + uri
    headers = {"x-api-key": session_key}
    response = requests.get(url, headers=headers, cookies=cookies, verify=False)
    if response.status_code != 200:
        logger.error(f"failed to get hmc version: {response.text}")
        return

    soup = BeautifulSoup(response.text, 'xml')
    version_info = soup.find("VersionInfo")
    major_ver = version_info.find("Version").text
    min_ver = version_info.find("Minor").text
    serv_pack_name = version_info.find("ServicePackName").text
    return major_ver, min_ver, serv_pack_name

def list_systems():
    uri = f"/rest/api/uom/ManagedSystem/quick/All"
    url =  "https://" + os.getenv("HMC_IP") + uri
    headers = {"x-api-key": session_key}
    response = requests.get(url, headers=headers, cookies=cookies, verify=False)
    if response.status_code != 200:
        logger.error(f"failed to get hmc version: {response.text}")
        return
    list_of_systems = response.json()
    return list_of_systems

def list_all_systems():
    list_of_systems = list_systems()
    list_of_sys_names = []
    for system in list_of_systems:
        list_of_sys_names.append(system["SystemName"])
    return list_of_sys_names

def compose_parititon_data(partitions):
    vm_list = []
    for lpar in partitions:
        name = lpar["PartitionName"] 
        lpar_id = lpar["PartitionID"]
        state = lpar["PartitionState"]
        vm_list.append({
            "name": name,
            "id": lpar_id,
            "state": state
        })

    return vm_list

def get_logical_partitions(system_name):
    system_uuid = ""
    list_of_systems = list_systems()
    for system in list_of_systems:
        if system["SystemName"] == system_name:
            system_uuid = system["UUID"]
    if system_uuid == "":
        return f"failed to find system with name '{system_name}'"
    
    uri = f"/rest/api/uom/LogicalPartition/quick/All"
    url = f"https://{os.getenv("HMC_IP")}/{uri}"
    headers = {"x-api-key": session_key}
    response = requests.get(url, headers=headers, cookies=cookies, verify=False)
    if response.status_code != 200:
        logger.error(f"failed to get logical partitions: {response.text}")
        return []
    partitions = response.json()
    filtered_partition = []
    for partition in partitions:
        if system_uuid in partition["AssociatedManagedSystem"]:
            filtered_partition.append(partition)

    return filtered_partition

def partition_stats(lpar_name, system_name):
    partitions = get_logical_partitions(system_name)
    lpar_id = ""
    for partition in partitions:
        if lpar_name == partition["PartitionName"]:
            lpar_id = partition["UUID"]
    uri = f"/rest/api/uom/LogicalPartition/{lpar_id}"
    url = f"https://{os.getenv("HMC_IP")}/{uri}"
    headers = {"x-api-key": session_key}
    response = requests.get(url, headers=headers, cookies=cookies, verify=False)
    if response.status_code != 200:
        logger.error(f"failed to get partition details: {response.text}")
        return ""

    partition_stats = {"memory": {}, "cpu": {}}
    soup = BeautifulSoup(response.text, 'xml')
    memory_config = soup.find("PartitionMemoryConfiguration")
    curr_memory = memory_config.find("CurrentMemory").text
    max_memory = memory_config.find("CurrentMaximumMemory").text
    partition_stats["memory"]["current_memory"] = curr_memory
    partition_stats["memory"]["max_memory"] = max_memory

    proc_config = soup.find("CurrentSharedProcessorConfiguration")
    allocated_vpu = proc_config.find("AllocatedVirtualProcessors").text
    curr_cpu = proc_config.find("CurrentProcessingUnits").text
    partition_stats["cpu"]["allocated_vpu"] = allocated_vpu
    partition_stats["cpu"]["current_cpu"] = curr_cpu

    status = soup.find("PartitionState").text
    partition_stats["partition_status"] = status
    stats_str = json.dumps(partition_stats)
    return stats_str

def get_system_uuid(sys_name):
    uri = "/rest/api/uom/ManagedSystem/quick/All"
    url = f"https://{os.getenv("HMC_IP")}/{uri}"
    headers = {"x-api-key": session_key}
    response = requests.get(url, headers=headers, cookies=cookies, verify=False)
    if response.status_code != 200:
        return f"failed to get system UUID, error: {response.text}"
    systems = response.json()
    uuid = ""

    for system in systems:
        if system["SystemName"] == sys_name:
            uuid = system["UUID"]
            break
    return uuid

def get_compute_usage(sys_uuid):
    uri = f"/rest/api/uom/ManagedSystem/{sys_uuid}"
    url = f"https://{os.getenv("HMC_IP")}/{uri}"
    headers = {"x-api-key": session_key}
    response = requests.get(url, headers=headers, cookies=cookies, verify=False)
    if response.status_code != 200:
        logger.error(f"failed to get system compute details: {response.text}")
        return ""
    compute_usage = {"Processor": {}, "Memory": {}}
    soup = BeautifulSoup(response.text, 'xml')
    processor = soup.find("AssociatedSystemProcessorConfiguration")
    curr_proc = processor.find("ConfigurableSystemProcessorUnits").text
    avail_proc = processor.find("CurrentAvailableSystemProcessorUnits").text
    installed_proc = processor.find("InstalledSystemProcessorUnits").text

    compute_usage["Processor"]["ConfigurableSystemProcessorUnits"] = curr_proc
    compute_usage["Processor"]["CurrentAvailableSystemProcessorUnits"] = avail_proc
    compute_usage["Processor"]["InstalledSystemProcessorUnits"] = installed_proc

    memory = soup.find("AssociatedSystemMemoryConfiguration")
    config_memory = memory.find("ConfigurableSystemMemory").text
    curr_system_memory = memory.find("CurrentAvailableSystemMemory").text
    installed_system_memory = memory.find("InstalledSystemMemory").text
    partition_assigned_memory = memory.find("CurrentAssignedMemoryToPartitions").text

    compute_usage["Memory"]["ConfigurableSystemMemory"] = config_memory
    compute_usage["Memory"]["CurrentAvailableSystemMemory"] = curr_system_memory
    compute_usage["Memory"]["InstalledSystemMemory"] = installed_system_memory
    compute_usage["Memory"]["CurrentAssignedMemoryToPartitions"] = partition_assigned_memory

    return json.dumps(compute_usage)
