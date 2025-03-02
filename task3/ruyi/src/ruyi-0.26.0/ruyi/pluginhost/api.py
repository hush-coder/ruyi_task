from contextlib import AbstractContextManager
import pathlib
import subprocess
import sys
import time
from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from .. import log
from ..cli import user_input
from ..version import RUYI_SEMVER
from .paths import resolve_ruyi_load_path

if TYPE_CHECKING:
    from . import PluginHostContext, SupportsEvalFunction, SupportsGetOption

T = TypeVar("T")
U = TypeVar("U")


class RuyiHostAPI:
    def __init__(
        self,
        phctx: "PluginHostContext[SupportsGetOption, SupportsEvalFunction]",
        this_file: pathlib.Path,
        this_plugin_dir: pathlib.Path,
        allow_host_fs_access: bool,
    ) -> None:
        self._phctx = phctx
        self._this_file = this_file
        self._this_plugin_dir = this_plugin_dir
        self._ev = phctx.make_evaluator()
        self._allow_host_fs_access = allow_host_fs_access

        self._logger = RuyiPluginLogger()

    @property
    def ruyi_version(self) -> str:
        return str(RUYI_SEMVER)

    @property
    def ruyi_plugin_api_rev(self) -> int:
        return 1

    def load_toml(self, path: str) -> object:
        resolved_path = resolve_ruyi_load_path(
            path,
            self._phctx.plugin_root,
            True,
            self._this_file,
            self._allow_host_fs_access,
        )
        with open(resolved_path, "rb") as f:
            return tomllib.load(f)

    @property
    def log(self) -> "RuyiPluginLogger":
        return self._logger

    def cli_ask_for_choice(self, prompt: str, choice_texts: list[str]) -> int:
        return user_input.ask_for_choice(prompt, choice_texts)

    def cli_ask_for_file(self, prompt: str) -> str:
        return user_input.ask_for_file(prompt)

    def cli_ask_for_kv_choice(self, prompt: str, choices_kv: dict[str, str]) -> str:
        return user_input.ask_for_kv_choice(prompt, choices_kv)

    def cli_ask_for_yesno_confirmation(
        self,
        prompt: str,
        default: bool = False,
    ) -> bool:
        return user_input.ask_for_yesno_confirmation(prompt, default)

    def call_subprocess_argv(
        self,
        argv: list[str],
    ) -> int:
        # TODO: restrictions on this
        return subprocess.call(argv)

    def sleep(self, seconds: float, /) -> None:
        return time.sleep(seconds)

    def with_(
        self,
        cm: AbstractContextManager[T],
        fn: object | Callable[[T], U],
    ) -> U:
        with cm as obj:
            return cast(U, self._ev.eval_function(fn, obj))


class RuyiPluginLogger:
    def __init__(self) -> None:
        pass

    def stdout(
        self,
        message: str,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
    ) -> None:
        log.stdout(message, *objects, sep=sep, end=end)

    def D(
        self,
        message: str,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
    ) -> None:
        log.D(message, *objects, sep=sep, end=end, _stack_offset_delta=1)

    def W(
        self,
        message: str,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
    ) -> None:
        log.W(message, *objects, sep=sep, end=end)

    def I(  # noqa: E743 # the name intentionally mimics Android logging for brevity
        self,
        message: str,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
    ) -> None:
        log.I(message, *objects, sep=sep, end=end)

    def F(
        self,
        message: str,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
    ) -> None:
        log.F(message, *objects, sep=sep, end=end)


def _ruyi_plugin_rev(
    phctx: "PluginHostContext[SupportsGetOption, SupportsEvalFunction]",
    this_file: pathlib.Path,
    this_plugin_dir: pathlib.Path,
    allow_host_fs_access: bool,
    rev: object,
) -> RuyiHostAPI:
    if not isinstance(rev, int):
        raise TypeError("rev must be int in ruyi_plugin_rev calls")
    if rev != 1:
        raise ValueError(
            f"Ruyi plugin API revision {rev} is not supported by this Ruyi"
        )
    return RuyiHostAPI(
        phctx,
        this_file,
        this_plugin_dir,
        allow_host_fs_access,
    )


def make_ruyi_plugin_api_for_module(
    phctx: "PluginHostContext[SupportsGetOption, SupportsEvalFunction]",
    this_file: pathlib.Path,
    this_plugin_dir: pathlib.Path,
    is_cmd: bool,
) -> Callable[[object], RuyiHostAPI]:
    # Only allow access to host FS when we're being loaded as a command plugin
    allow_host_fs_access = is_cmd

    return lambda rev: _ruyi_plugin_rev(
        phctx,
        this_file,
        this_plugin_dir,
        allow_host_fs_access,
        rev,
    )
