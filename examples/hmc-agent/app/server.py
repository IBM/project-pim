from mcp.server.fastmcp import FastMCP
from tabulate import tabulate
import urllib3

import hmc

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create MCP server, if MCP server needs to be run on differnt port make sure to use same port in MCP_SERVER_URL in agent.py
mcp = FastMCP("ibmhmcserver", host="0.0.0.0", port="8001")

# Add hmc version retriever tool
@mcp.tool()
def get_hmc_version() -> str:
    """This tool returns the HMC version.
    Returns:
        str:"Major version: 1, minor version: 0, service pack version: 1110"
    """
    major_ver, min_ver, serv_pack_name = hmc.get_hmc_version()
    return str(f"Major version: {major_ver}, minor version: {min_ver}, service pack version: {serv_pack_name}")

@mcp.tool()
def list_all_systems() -> str:
    """This tool returns all systems managed by HMC.
    Returns:
        str: "list of systems managed by HMC: <list of system names>"
    """
    systems = hmc.list_all_systems()
    res = '\n'.join(systems)
    return str(f"list of systems managed by HMC: {res}")

@mcp.tool()
def get_logical_partitions(system_name) -> str:
    """This tool returns the logical partitions created under a given system in HMC.
    Returns:
        str: "Formatted table contains 'Logical Partition Name: <name>, ID: <id>, State: <state>'"
    """
    partitions_json = hmc.get_logical_partitions(system_name)
    partitions = hmc.compose_parititon_data(partitions_json)

    if not partitions:
        return "No logical partitions found."

    result = []
    # Iterate through the partitions and format the output
    for partition in partitions:
        name = partition["name"]
        lpar_id = partition["id"]
        state = partition["state"]
        result.append([name, lpar_id, state])
    
    headers = ["Logical Partition Name", "ID", "State"]
    return tabulate(result, headers=headers, tablefmt="grid")
    
@mcp.tool()
def partition_stats(partition_name, system_name) -> str:
    """
    This tool returns the stats of given parititon under the given system
    Returns:
        str: Current stats of partition:: <current parititon's stats>
    """
    # Get lpar UUID from partition name
    stats = hmc.paritition_stats(partition_name, system_name)
    parititon_stats = {"partition_stats": stats}
    return str(f"Current stats of partition: \n{parititon_stats}")

@mcp.tool()
def get_compute_usage(system_name) -> str:
    """
    This tool returns current usage of given system's cpu and memory.
    Returns:
        str: Compute usage details: <compute usage of given>
    """
    sys_uuid = hmc.get_system_uuid(system_name)
    compute_details = hmc.get_compute_usage(sys_uuid)
    compute_usage = {"compute_usage": compute_details}
    return str(f"Compute usage details: \n{compute_usage}")

# Kick off MCP server
if __name__ == "__main__":
    try:
        hmc.authenticate_hmc()
        mcp.run(transport="sse")
    finally:
        hmc.delete_session()
