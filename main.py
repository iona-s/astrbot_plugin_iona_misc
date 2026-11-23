"""AstrBot loader shim for the iona misc plugin."""

from .core.plugin import IonaMiscPlugin, bind_loader_module

bind_loader_module(__name__)
del bind_loader_module

__all__ = ["IonaMiscPlugin"]
