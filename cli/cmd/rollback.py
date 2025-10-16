import cli.utils.common as common
import cli.utils.validator as validator
import cli.utils.monitor_util as monitor_util
import cli.utils.string_util as util

logger = common.get_logger("pim-rollback")


def rollback(config_file_path):
    try:
        logger.info("Rollback PIM partition")
        config = common.initialize_config(config_file_path)

        logger.debug("Validate configuration")
        is_config_valid = validator.validate_rollback_config(config)
        logger.debug("Configuration validated")
        if not is_config_valid:
            return
        
        logger.debug("Rollback to the previous PIM image")
        rollbacked = _rollback(config)

        if rollbacked:
            logger.info("Monitor booting")
            monitor_util.monitor_pim(config)
            logger.info("PIM partition successfully rollbacked")
    except Exception as e:
        logger.error(f"encountered an error: {e}")


def _rollback(config):
    try:
        if not util.get_ssh_priv_key(config) or not util.get_ssh_pub_key(config):
            logger.debug("Load SSH keys generated during launch to config")
            config = common.load_ssh_keys(config)
        ssh_client = common.ssh_to_partition(config)

        bootc_rollback_cmd = "sudo bootc rollback"
        _, stdout, stderr = ssh_client.exec_command(
            bootc_rollback_cmd, get_pty=True)
        if stdout.channel.recv_exit_status() != 0:
            out = ' '.join(stdout.readlines())
            if "No rollback available" in out:
                logger.info("Nothing to Rollback")
            else: 
                logger.error(f"failed to rollback, error: {out}, {stderr.readlines()}")
            return False
        else:
            logger.info("Rollback succeeded")

        logger.info("Reboot to apply the rollback")
        _, stdout, stderr = ssh_client.exec_command(
            "sudo reboot", get_pty=True)
        if stdout.channel.recv_exit_status() != 0:
            logger.error(
                f"failed to reboot, error: {stdout.readlines()}, {stderr.readlines()}")
            return False
        return True
    except Exception as e:
        raise Exception(f"failed to rollback PIM partition, error: {e}")
