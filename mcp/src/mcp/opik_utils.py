import os

import opik
from loguru import logger
from opik.configurator.configure import OpikConfigurator

from mcp.config import get_settings

config = get_settings()

def initialize_monitoring() -> None:
    if config.OPIK_API_KEY and config.OPIK_PROJECT:
        try:
            configurator_client = OpikConfigurator(api_key=config.OPIK_API_KEY)
            primary_workspace = configurator_client._get_default_workspace()
        except Exception:
            logger.warning(
                "Primary workspace not found. Setting workspace to None and enabling interactive mode."
            )
            primary_workspace = None

        os.environ["OPIK_PROJECT_NAME"] = config.OPIK_PROJECT

        try:
            opik.configure(
                api_key=config.OPIK_API_KEY,
                workspace=primary_workspace,
                use_local=False,
                force=True,
            )
            logger.info(
                f"Opik monitoring configured successfully using workspace '{primary_workspace}'"
            )
        except Exception as e:
            logger.error(e)
            logger.warning(
                "Failed to configure Opik monitoring. There is probably an issue with the COMET_API_KEY or COMET_PROJECT environment variables or with the Opik server connection."
            )
    else:
        logger.warning(
            "COMET_API_KEY and COMET_PROJECT are not set. Configure them to enable prompt monitoring with Opik (powered by Comet ML)."
        )