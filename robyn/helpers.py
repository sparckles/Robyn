from typing import Any, Type, Tuple
from pydantic_settings import BaseSettings, EnvSettingsSource, PydanticBaseSettingsSource
from pydantic import ConfigDict

import importlib
import pkgutil
import logging

from robyn import Robyn

logger = logging.getLogger(__name__)


def discover_routes(handler_path: str = "api.handlers") -> Robyn:
    mux: Robyn = Robyn(__file__)
    package = importlib.import_module(handler_path)
    for _, module_name, _ in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
        module = importlib.import_module(module_name)
        logger.info(f"member: {module}")
        mux.include_router(module.router)
    return mux


class AcceptArrayEnvsSource(EnvSettingsSource):
    def prepare_field_value(self, field_name: str, field: Any, value: Any, value_is_complex: bool) -> Any:
        if isinstance(field.annotation, type) and issubclass(field.annotation, list) and isinstance(value, str):
            return [x.strip() for x in value.split(",") if x]
        return value


class BaseConfig(BaseSettings):
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (AcceptArrayEnvsSource(settings_cls),)

    model_config = ConfigDict(extra="ignore")  # Ignore extra environment variables
