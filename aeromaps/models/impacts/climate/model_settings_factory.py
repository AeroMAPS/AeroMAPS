"""Factory to register and create AeroMAPS models."""

from __future__ import annotations
import pkgutil
from typing import Any, ClassVar, Iterator
from importlib import import_module

from aeromaps.models.impacts.climate.climate_models_settings.settings import ClimateModelSettings


class ModelSettingsFactory:
    """A factory to register and create Climate model settings."""

    _base_class: ClassVar[type[ClimateModelSettings]] = ClimateModelSettings
    """The base class the factory can build."""
    _package_names: ClassVar[list[str]] = ["aeromaps.models.impacts.climate.default_models"]
    """The name of the package from which the models are discovered."""

    @classmethod
    def _discover(cls) -> dict[str, type[ClimateModelSettings]]:
        """Import the settings packages and map each model settings to their name.

        Returns:
            The discovered model settings mapped to their names.
        """
        cls.import_model_packages()
        registry = {}

        for model_cls in cls._iter_subclasses(cls._base_class):
            name = model_cls.model_fields["climate_model"].default
            if name in registry:
                raise ValueError(
                    f"Duplicate model name {name}: "
                    f"{registry[name].__module__} and {model_cls.__module__}"
                )
            registry[name] = model_cls
        return registry

    def create(self, settings_model: str, *args, **kwargs: Any) -> ClimateModelSettings:
        """Create an instance of an ClimateModelSettings subclass.

        Args:
            settings_model: The name of the model settings.
            *args: The positional arguments to be passed to the class constructor.
            **kwargs: The keyword arguments passed to the model constructor.

        Returns:
            An instance of the given model settings.

        Raises:
            KeyError If the model settings name is unknown.
        """
        settings = self._discover()
        settings_cls = settings.get(settings_model)
        setting_instance = ClimateModelSettings._instances.get(settings_model)
        if settings_cls and not setting_instance:
            return settings_cls(*args, **kwargs)
        elif setting_instance:
            return setting_instance
        else:
            raise KeyError(
                f"Unknown model {settings_model}, available models are: "
                f"{sorted(settings)}. Available instances are: "
                f"{sorted(ClimateModelSettings._instances.keys())}"
            )

    @classmethod
    def import_model_packages(cls, extra_packages: list[str] | str | None = None) -> None:
        """Import the models that inherit from `ClimateModelSettings` found in :attr:`_package_names`.

        Args:
            extra_packages: Packages to discover on top of the shipped model packages.
        """
        packages = list(cls._package_names)

        if extra_packages:
            if isinstance(extra_packages, str):
                packages.append(extra_packages)
            else:
                packages.extend(extra_packages)

        for package_name in packages:
            package = import_module(package_name)

            if not hasattr(package, "__path__"):
                continue

            for module_info in pkgutil.walk_packages(
                package.__path__,
                prefix=package.__name__ + ".",
            ):
                import_module(module_info.name)

    @classmethod
    def _iter_subclasses(cls, parent: type) -> Iterator[type[ClimateModelSettings]]:
        """Retrieve the available ClimateModelSettings subclasses.

        Returns:
            An iterator with the discover ClimateModelSettings subclasses.
        """
        for subclass in parent.__subclasses__():
            yield subclass
            yield from cls._iter_subclasses(subclass)

    @classmethod
    def get_available_model_settings_names(cls) -> list[str]:
        """Get the available AeroMAPS climate model settings.

        Returns:
            A list with the names of the discovered ClimateModelSettings subclasses.
        """
        return sorted(cls._discover())

    @classmethod
    def get_available_model_settings_instances(cls) -> list[str]:
        """Get the available AeroMAPS climate model settings instances."""

        return sorted(ClimateModelSettings._instances.keys())
