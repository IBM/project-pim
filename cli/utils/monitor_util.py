import time

from cli.app.ai_app_exception import AIAppError
import cli.app.ai_app as app
import cli.utils.common as common

from cli.utils.string_util import *

logger = common.get_logger("monitor")


def monitor_pim_boot(config):
    # Re-run scenario: If lpar is in 2nd boot stage, check base service logs
    logger.debug("PIM boot: Checking base.service")
    try:
        ssh_client = common.ssh_to_partition(config)

        base_svc_exists = "ls /etc/systemd/system/base.service"
        _, stdout, _ = ssh_client.exec_command(
            base_svc_exists, get_pty=True)
        if stdout.channel.recv_exit_status() == 0:
            logger.debug("base.service exists")

            logger.debug("Checking base.service logs")
            base_cfg_svc_cmd = "sudo journalctl -u base.service -f 2>&1 | awk '{print} /base.sh base.service completed successfully/ {print \"Match found: \" $0; exit 0}'"
            _, stdout, _ = ssh_client.exec_command(
                base_cfg_svc_cmd, get_pty=True)
            while True:
                out = stdout.readline()
                logger.debug(out)
                if stdout.channel.exit_status_ready():
                    if stdout.channel.recv_exit_status() == 0:
                        logger.debug(
                            "Found 'base.service completed successfully' message")
                        ssh_client.close()
                        return
                if "base.service: Failed with result 'exit-code'" in out:
                    ssh_client.close()
                    logger.error(f"failed to start AI application. error: {out}")
                    raise Exception(f"failed to start AI application. error: {out}")
        else:
            ssh_client.close()
            logger.error(
                "failed to find '/etc/systemd/system/base.service', please check console for more possible errors")
            raise Exception(
                "failed to  find '/etc/systemd/system/base.service', please check console for more possible errors")
    except Exception as e:
        logger.error(f"failed to monitor PIM boot, error: {e}")
        raise Exception(f"failed to monitor PIM boot, error: {e}")


def monitor_pim(config):
    monitor_pim_boot(config)
    logger.info("Partition booted with PIM image")

    # No need to validate the AI application deployed via PIM flow if 'ai.validation.request' set to no, can complete the workflow
    if get_ai_app_request(config) == "no":
        logger.info(
            "Skipping AI application validation since 'ai.validation.request' set to False")

    # Validate the AI application deployed via PIM partition with the request details provided in 'ai.validation'
    logger.info("Validate AI application launched via PIM")
    logger.debug(
        f"Validation request details\n Method: {get_ai_app_method(config)}\n URL: {get_ai_app_url(config)}\n Payload: {get_ai_app_payload(config)}")
    err = ""
    for i in range(50):
        up, msg = app.check_app(config)
        if not up:
            logger.debug(
                f"AI application is still not up and running, message: {msg} retrying..")
            time.sleep(30)
            continue
        else:
            logger.info(f"AI application is up and running, Response: {msg}")
            return
    logger.error(
        f"failed to bring up AI application from PIM image, error: {msg}")
    raise AIAppError(
        f"failed to bring up AI application from PIM image, error: {msg}")


def monitor_bootstrap_boot(config):
    logger.debug("Bootstrap boot: Checking getcontainer.service")
    try:
        ssh_client = common.ssh_to_partition(config)

        get_container_svc_exists = "ls /usr/lib/systemd/system/getcontainer.service"
        _, stdout, _ = ssh_client.exec_command(
            get_container_svc_exists, get_pty=True)
        if stdout.channel.recv_exit_status() == 0:
            logger.debug("getcontainer.service exists")

            get_container_svc_cmd = "sudo journalctl -u getcontainer.service -f 2>&1 | awk '{print} /Installation complete/ {print \"Match found: \" $0; exit 0}'"
            _, stdout, stderr = ssh_client.exec_command(
                get_container_svc_cmd, get_pty=True)
            while True:
                out = stdout.readline()
                logger.debug(out)
                if stdout.channel.exit_status_ready():
                    if stdout.channel.recv_exit_status() == 0:
                        logger.debug(
                            "Bootc based PIM AI image install to disk complete!!")
                        # Sleep is required to give time for reboot to happen to boot from the disk
                        time.sleep(10)
                        ssh_client.close()
                        break
                    else:
                        logger.error(
                            "Failed to detect bootc based PIM AI image install completion signature. Please check console logs for more information\n")
                if "getcontainer.service: Failed with result 'exit-code'" in out:
                    ssh_client.close()
                    logger.error(f"failed to detect bootc based PIM AI image install completion signature. error: {out}")
                    raise Exception(f"failed to detect bootc based PIM AI image install completion signature. error: {out}")
        else:
            logger.debug(
                "Could not find 'getcontainer.service', will look for 'base.service' in PIM boot since it could be a re-run and bootstrap might have already finished")
            ssh_client.close()
    except Exception as e:
        logger.error(f"failed to monitor bootstrap boot, error: {e}")
        raise Exception(f"failed to monitor bootstrap boot, error: {e}")

    return
