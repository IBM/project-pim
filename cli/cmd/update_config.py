import shutil
from scp import SCPClient
import os

import cli.network.virtual_network as virtual_network
import cli.partition.partition as partition
import cli.utils.monitor_util as monitor_util
import cli.utils.command_util as command_util
import cli.utils.common as common
import cli.utils.iso_util as iso_util
import cli.utils.string_util as util


logger = common.get_logger("pim-update-config")

def update_config(config_file_path):
    cookies = None
    try:
        logger.info("Updating PIM partition's config")
        config = common.initialize_config(config_file_path)
        # Invoking initialize_command to perform common actions like validation, authentication etc.
        is_config_valid, cookies, sys_uuid, _ = command_util.initialize_command(
            config)
        if is_config_valid:
            _update_config(config, cookies, sys_uuid)
            logger.info("PIM partition's config successfully updated")
    except Exception as e:
        logger.error(f"encountered an error: {e}")
    finally:
        if cookies:
            command_util.cleanup(config, cookies)

def _update_config(config, cookies, sys_uuid):
    try:
        logger.debug("Checking partition exists")
        exists, _, partition_uuid = partition.check_partition_exists(config, cookies, sys_uuid)
        if not exists:
            logger.info(f"Partition named '{util.get_partition_name(config)}' not found, nothing to update")
            return

        if not util.get_ssh_priv_key(config) or not util.get_ssh_pub_key(config):
            logger.debug("Load SSH keys generated during launch to config")
            config = common.load_ssh_keys(config)

        config["ssh"]["pub-key"] = common.readfile(
            util.get_ssh_pub_key(config))
        
        logger.debug("Partition exists, generating cloud init config")

        # Get VLAN ID and VSWITCH ID
        vlan_id, vswitch_id = virtual_network.get_vlan_details(config, cookies, sys_uuid)

        # Check if network adapter is already attached to lpar. If not, do attach
        _, slot_num = virtual_network.check_network_adapter(config, cookies, partition_uuid, vlan_id, vswitch_id)

        iso_util.generate_cloud_init_iso_config(config, slot_num, common.cloud_init_update_config_dir)
        if not common.compare_dir(common.cloud_init_config_dir, common.cloud_init_update_config_dir):
            logger.info("No change in config, skipping the update")
            shutil.rmtree(common.cloud_init_update_config_dir)
            return
        logger.info("Detected config change, updating")

        # Create pim_config.json file
        pim_config = util.get_pim_config_json(config)
        with open(f"{common.cloud_init_update_config_dir}/pim_config.json", "w") as config_file:
            config_file.write(pim_config)

        ssh_client = common.ssh_to_partition(config)

        with SCPClient(ssh_client.get_transport()) as scp:
            scp.put(f'{common.cloud_init_update_config_dir}/pim_config.json', '/tmp')
        
        move_cmd = "sudo mv /tmp/pim_config.json /etc/pim/"
        _, stdout, stderr = ssh_client.exec_command(move_cmd)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            logger.info("Successfully updated the config of the partition.")
        else:
            errorMsg = stderr.read().decode('utf-8')
            logger.error(f"failed to update config of the partition. error: {errorMsg}")
            raise Exception(errorMsg)

        
        # Restart pim_init.service
        restart_command = "sudo systemctl restart pim_init.service"
        _, stdout, stderr = ssh_client.exec_command(restart_command)
        exit_status = stdout.channel.recv_exit_status()

        if exit_status == 0:
            logger.info("Successfully restarted pim_init.service")
        else:
            errorMsg = stderr.read().decode('utf-8')
            logger.error(f"failed to restart pim_init.service. error: {errorMsg}")
            raise Exception(errorMsg)
        
        os.remove(f"{common.cloud_init_update_config_dir}/pim_config.json")
        # Cleanup existing config and move updated config
        shutil.rmtree(common.cloud_init_config_dir)
        shutil.move(common.cloud_init_update_config_dir, common.cloud_init_config_dir)
        logger.info("Monitoring AI application, this will take a while")
        monitor_util.monitor_pim(config)
    except Exception as e:
        raise e
