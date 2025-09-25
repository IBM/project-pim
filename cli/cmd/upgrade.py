import cli.utils.common as common
import cli.utils.monitor_util as monitor_util
import cli.utils.string_util as util
import cli.utils.validator as validator

logger = common.get_logger("pim-upgrade")
bootc_auth_json = "/etc/ostree/auth.json"


def upgrade(config_file_path):
    try:
        logger.info("Upgrading PIM partition")
        config = common.initialize_config(config_file_path)

        logger.debug("Validating configuration")
        is_config_valid = validator.validate_upgrade_config(config)
        logger.debug("Configuration validated")
        if not is_config_valid:
            return
        
        logger.debug("Upgrade to the latest PIM image")
        if not _upgrade(config):
            return

        logger.debug("Monitor booting")
        monitor_util.monitor_pim(config)
        logger.info("PIM partition successfully upgraded")
    except Exception as e:
        logger.error(f"encountered an error: {e}")


def _upgrade(config):
    try:
        if not util.get_ssh_priv_key(config) or not util.get_ssh_pub_key(config):
            logger.debug("Load SSH keys generated during launch to config")
            config = common.load_ssh_keys(config)

        ssh_client = common.ssh_to_partition(config)

        logger.info(f"Updating PIM partition's '{bootc_auth_json}' with the latest one provided")
        auth_json = "{}" if util.get_auth_json(config) == "" else util.get_auth_json(config)
        sftp_client = ssh_client.open_sftp()
        with sftp_client.open("/tmp/auth.json", 'w') as f:
            f.write(auth_json)
        sftp_client.close()

        move_command = f"sudo mv /tmp/auth.json {bootc_auth_json}"
        _, stdout, stderr = ssh_client.exec_command(move_command, get_pty=True)
        if stdout.channel.recv_exit_status() != 0:
            raise Exception(
                f"failed to load auth.json in {bootc_auth_json}, error: {stdout.readlines()}, {stderr.readlines()}")

        upgraded = False
        bootc_upgrade_cmd = "sudo bootc upgrade"
        _, stdout, _ = ssh_client.exec_command(bootc_upgrade_cmd, get_pty=True)
        upgrade_stdout = ""
        while True:
            out = stdout.readline()
            upgrade_stdout += out + "\n"
            logger.debug(f"{out}")
            if stdout.channel.exit_status_ready():
                break
        if "No update available" in upgrade_stdout:  
            logger.info("No upgrade available, PIM image is at latest level.")
            return
        
        if "Queued for next boot" in upgrade_stdout:
            logger.info("Successfully upgraded the PIM image to latest level")
        else:
            raise Exception("unsusccessful upgrade command execution")

        # Need to do linux reboot instead of HMC reboot
        reboot_cmd = "sudo reboot"
        _, stdout, _ = ssh_client.exec_command(reboot_cmd, get_pty=True)
        if stdout.channel.recv_exit_status() == 0:
            logger.info("Partition rebooted to apply the upgrade")
        else:
            raise Exception(f"failed to reboot the partition, error: {stdout.readlines()}")
        
        logger.info("Monitoring boot process, this will take a while")
        monitor_util.monitor_pim(config)
    except Exception as e:
        logger.error(f"failed to upgrade PIM partition, error: {e}")
        raise Exception(f"failed to upgrade PIM partition, error: {e}")

    return upgraded
