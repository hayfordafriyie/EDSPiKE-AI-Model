from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

from .languages import LanguageConfig, get_language
from .plugins import PluginContext, PluginHook, get_plugin_registry
from .sandbox import Sandbox, SandboxResult

logger = logging.getLogger(__name__)


@dataclass
class ExecResult:
    id: str = ""
    language: str = ""
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    timed_out: bool = False
    duration_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class CodeExecutor:
    def __init__(
        self,
        work_dir: str | None = None,
        cleanup: bool = True,
        sandbox: Sandbox | None = None,
    ):
        self._work_dir = work_dir
        self._cleanup = cleanup
        self._sandbox = sandbox

    def execute(
        self,
        code: str,
        language: str = "python",
        timeout: float | None = None,
        env: dict[str, str] | None = None,
        stdin: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ExecResult:
        exec_id = uuid.uuid4().hex[:12]
        lang_config = get_language(language)
        effective_timeout = timeout if timeout is not None else lang_config.timeout_default

        sandbox = self._sandbox or Sandbox(work_dir=self._work_dir, cleanup=self._cleanup)

        ctx = PluginContext(
            code=code, language=language, env=env or {},
            metadata=metadata or {},
        )

        registry = get_plugin_registry()

        with sandbox:
            ctx.work_dir = sandbox.work_dir

            ctx = registry.run(PluginHook.VALIDATE, ctx)
            if ctx.errors:
                return ExecResult(
                    id=exec_id, language=language,
                    stdout="", stderr="", exit_code=-1,
                    errors=ctx.errors, metadata=metadata or {},
                )

            ctx = registry.run(PluginHook.PRE_EXEC, ctx)
            if ctx.errors:
                return ExecResult(
                    id=exec_id, language=language,
                    stdout="", stderr="", exit_code=-1,
                    errors=ctx.errors, metadata=metadata or {},
                )

            script_name = lang_config.filename or f"script{lang_config.extensions[0]}"
            script_path = sandbox.write_file(script_name, code)
            command = lang_config.command

            try:
                result: SandboxResult = sandbox.execute(
                    command, stdin=stdin,
                    timeout=effective_timeout,
                    env=ctx.env, script_path=script_path,
                )
            except Exception as exc:
                logger.error("Sandbox execution failed: %s", exc)
                return ExecResult(
                    id=exec_id, language=language,
                    stdout="", stderr=str(exc), exit_code=-1,
                    errors=[str(exc)], metadata=metadata or {},
                )

            ctx.result = result
            ctx = registry.run(PluginHook.POST_EXEC, ctx)

        return ExecResult(
            id=exec_id,
            language=language,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            timed_out=result.timed_out,
            duration_ms=result.duration_ms,
            errors=ctx.errors,
            metadata=metadata or {},
        )
