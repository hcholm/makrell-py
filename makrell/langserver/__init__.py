import argparse
import asyncio
import re
import time
import uuid
from typing import Optional

from lsprotocol import types as lsp

from pygls.server import LanguageServer
from makrell.ast import Sequence
from makrell.baseformat import src_to_baseformat

import makrell.makrellpy.compiler as mrc
from makrell.parsing import flatten
import makrell.parsing
from makrell.tokeniser import regular

COUNT_DOWN_START_IN_SECONDS = 10
COUNT_DOWN_SLEEP_IN_SECONDS = 1


class MakrellLanguageServer(LanguageServer):
    CMD_COUNT_DOWN_BLOCKING = "countDownBlocking"
    CMD_COUNT_DOWN_NON_BLOCKING = "countDownNonBlocking"
    CMD_PROGRESS = "progress"
    CMD_REGISTER_COMPLETIONS = "registerCompletions"
    CMD_SHOW_CONFIGURATION_ASYNC = "showConfigurationAsync"
    CMD_SHOW_CONFIGURATION_CALLBACK = "showConfigurationCallback"
    CMD_SHOW_CONFIGURATION_THREAD = "showConfigurationThread"
    CMD_UNREGISTER_COMPLETIONS = "unregisterCompletions"

    CONFIGURATION_SECTION = "makrell.server"

    def __init__(self, *args):
        super().__init__(*args)


mr_server = MakrellLanguageServer("makrell-language-server", "v0.8.0")


def _validate(ls, params):
    ls.show_message_log("Validating ...")

    text_doc = ls.workspace.get_document(params.text_document.uri)

    source = text_doc.source
    diagnostics = _validate_mr("A" + source) if source else []

    ls.publish_diagnostics(text_doc.uri, diagnostics)


def _validate_mr(source):
    """Validates mr file."""
    diagnostics = []

    # d = lsp.Diagnostic(
    #     range=lsp.Range(
    #         start=lsp.Position(line=1, character=1),
    #         end=lsp.Position(line=2, character=2),
    #     ),
    #     message="Feil her " + source[:50],
    #     source=type(mr_server).__name__,
    #     severity=lsp.DiagnosticSeverity.Error,
    # )
    # diagnostics.append(d)
    # d = lsp.Diagnostic(

    #     range=lsp.Range(
    #         start=lsp.Position(line=3, character=0),
    #         end=lsp.Position(line=3, character=3),
    #     ),
    #     message="Feil der",
    #     source=type(mr_server).__name__,
    #     severity=lsp.DiagnosticSeverity.Warning,
    # )
    # diagnostics.append(d)

    cc = mrc.CompilerContext()
    nodes = src_to_baseformat(source)
    s = Sequence(flatten(regular(nodes)))
    mrc.compile_mr(s, cc)
    for i in cc.diag.items:
        n = i.node
        # line = i.node._start_line
        # column = i.node._start_column
        severity = lsp.DiagnosticSeverity.Information
        match i.severity:
            case makrell.parsing.DiagnosticSeverity.Error:
                severity = lsp.DiagnosticSeverity.Error
            case makrell.parsing.DiagnosticSeverity.Warning:
                severity = lsp.DiagnosticSeverity.Warning
            case makrell.parsing.DiagnosticSeverity.Info:
                severity = lsp.DiagnosticSeverity.Information
            case makrell.parsing.DiagnosticSeverity.Hint:
                severity = lsp.DiagnosticSeverity.Hint

        d = lsp.Diagnostic(
            range=lsp.Range(
                start=lsp.Position(line=n._start_line - 1, character=n._start_column - 1),
                end=lsp.Position(line=n._end_line - 1, character=n._end_column - 1),
            ),
            message=i.message,
            source=type(mr_server).__name__,
            severity=severity,
        )
        diagnostics.append(d)
    return diagnostics


@mr_server.feature(lsp.WORKSPACE_DIAGNOSTIC)
def workspace_diagnostic(
    params: lsp.WorkspaceDiagnosticParams,
) -> lsp.WorkspaceDiagnosticReport:
    """Returns diagnostic report."""
    documents = mr_server.workspace.text_documents.keys()

    if len(documents) == 0:
        items = []
    else:
        first = list(documents)[0]
        document = mr_server.workspace.get_document(first)
        items = [
            lsp.WorkspaceFullDocumentDiagnosticReport(
                uri=document.uri,
                version=document.version,
                items=_validate_mr("C"+document.source),
                kind=lsp.DocumentDiagnosticReportKind.Full,
            )
        ]

    return lsp.WorkspaceDiagnosticReport(items=items)


@mr_server.feature(
    lsp.TEXT_DOCUMENT_COMPLETION,
    lsp.CompletionOptions(trigger_characters=[","], all_commit_characters=[":"]),
)
def completions(params: Optional[lsp.CompletionParams] = None) -> lsp.CompletionList:
    """Returns completion items."""
    return lsp.CompletionList(
        is_incomplete=False,
        items=[
            lsp.CompletionItem(label='"'),
            lsp.CompletionItem(label="["),
            lsp.CompletionItem(label="]"),
            lsp.CompletionItem(label="{"),
            lsp.CompletionItem(label="}"),
        ],
    )


@mr_server.command(MakrellLanguageServer.CMD_COUNT_DOWN_BLOCKING)
def count_down_10_seconds_blocking(ls, *args):
    """Starts counting down and showing message synchronously.
    It will `block` the main thread, which can be tested by trying to show
    completion items.
    """
    for i in range(COUNT_DOWN_START_IN_SECONDS):
        ls.show_message(f"Counting down... {COUNT_DOWN_START_IN_SECONDS - i}")
        time.sleep(COUNT_DOWN_SLEEP_IN_SECONDS)


@mr_server.command(MakrellLanguageServer.CMD_COUNT_DOWN_NON_BLOCKING)
async def count_down_10_seconds_non_blocking(ls, *args):
    """Starts counting down and showing message asynchronously.
    It won't `block` the main thread, which can be tested by trying to show
    completion items.
    """
    for i in range(COUNT_DOWN_START_IN_SECONDS):
        ls.show_message(f"Counting down... {COUNT_DOWN_START_IN_SECONDS - i}")
        await asyncio.sleep(COUNT_DOWN_SLEEP_IN_SECONDS)


@mr_server.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls, params: lsp.DidChangeTextDocumentParams):
    """Text document did change notification."""
    _validate(ls, params)


@mr_server.feature(lsp.TEXT_DOCUMENT_DID_CLOSE)
def did_close(server: MakrellLanguageServer, params: lsp.DidCloseTextDocumentParams):
    pass


@mr_server.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params: lsp.DidOpenTextDocumentParams):
    pass
    _validate(ls, params)


@mr_server.feature(
    lsp.TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL,
    lsp.SemanticTokensLegend(token_types=["operator"], token_modifiers=[]),
)
def semantic_tokens(ls: MakrellLanguageServer, params: lsp.SemanticTokensParams):
    """See https://microsoft.github.io/language-server-protocol/specification#textDocument_semanticTokens
    for details on how semantic tokens are encoded."""

    TOKENS = re.compile('".*"(?=:)')

    uri = params.text_document.uri
    doc = ls.workspace.get_document(uri)

    last_line = 0
    last_start = 0

    data = []

    for lineno, line in enumerate(doc.lines):
        last_start = 0

        for match in TOKENS.finditer(line):
            start, end = match.span()
            data += [(lineno - last_line), (start - last_start), (end - start), 0, 0]

            last_line = lineno
            last_start = start

    return lsp.SemanticTokens(data=data)


@mr_server.feature(lsp.TEXT_DOCUMENT_INLINE_VALUE)
def inline_value(params: lsp.InlineValueParams):
    """Returns inline value."""
    return [lsp.InlineValueText(range=params.range, text="Inline value")]


@mr_server.command(MakrellLanguageServer.CMD_PROGRESS)
async def progress(ls: MakrellLanguageServer, *args):
    """Create and start the progress on the client."""
    token = str(uuid.uuid4())
    # Create
    await ls.progress.create_async(token)
    # Begin
    ls.progress.begin(
        token,
        lsp.WorkDoneProgressBegin(title="Indexing", percentage=0, cancellable=True),
    )
    # Report
    for i in range(1, 10):
        # Check for cancellation from client
        if ls.progress.tokens[token].cancelled():
            # ... and stop the computation if client cancelled
            return
        ls.progress.report(
            token,
            lsp.WorkDoneProgressReport(message=f"{i * 10}%", percentage=i * 10),
        )
        await asyncio.sleep(2)
    # End
    ls.progress.end(token, lsp.WorkDoneProgressEnd(message="Finished"))


@mr_server.command(MakrellLanguageServer.CMD_REGISTER_COMPLETIONS)
async def register_completions(ls: MakrellLanguageServer, *args):
    """Register completions method on the client."""
    params = lsp.RegistrationParams(
        registrations=[
            lsp.Registration(
                id=str(uuid.uuid4()),
                method=lsp.TEXT_DOCUMENT_COMPLETION,
                register_options={"triggerCharacters": "[':']"},
            )
        ]
    )
    response = await ls.register_capability_async(params)
    if response is None:
        ls.show_message("Successfully registered completions method")
    else:
        ls.show_message(
            "Error happened during completions registration.", lsp.MessageType.Error
        )


@mr_server.command(MakrellLanguageServer.CMD_SHOW_CONFIGURATION_ASYNC)
async def show_configuration_async(ls: MakrellLanguageServer, *args):
    """Gets exampleConfiguration from the client settings using coroutines."""
    try:
        config = await ls.get_configuration_async(
            lsp.WorkspaceConfigurationParams(
                items=[
                    lsp.ConfigurationItem(
                        scope_uri="", section=MakrellLanguageServer.CONFIGURATION_SECTION
                    )
                ]
            )
        )

        example_config = config[0].get("exampleConfiguration")

        ls.show_message(f"makrellServer.exampleConfiguration value: {example_config}")

    except Exception as e:
        ls.show_message_log(f"Error ocurred: {e}")


@mr_server.command(MakrellLanguageServer.CMD_SHOW_CONFIGURATION_CALLBACK)
def show_configuration_callback(ls: MakrellLanguageServer, *args):
    """Gets exampleConfiguration from the client settings using callback."""

    def _config_callback(config):
        try:
            example_config = config[0].get("exampleConfiguration")

            ls.show_message(f"makrellServer.exampleConfiguration value: {example_config}")

        except Exception as e:
            ls.show_message_log(f"Error ocurred: {e}")

    ls.get_configuration(
        lsp.WorkspaceConfigurationParams(
            items=[
                lsp.ConfigurationItem(
                    scope_uri="", section=MakrellLanguageServer.CONFIGURATION_SECTION
                )
            ]
        ),
        _config_callback,
    )


@mr_server.thread()
@mr_server.command(MakrellLanguageServer.CMD_SHOW_CONFIGURATION_THREAD)
def show_configuration_thread(ls: MakrellLanguageServer, *args):
    """Gets exampleConfiguration from the client settings using thread pool."""
    try:
        config = ls.get_configuration(
            lsp.WorkspaceConfigurationParams(
                items=[
                    lsp.ConfigurationItem(
                        scope_uri="", section=MakrellLanguageServer.CONFIGURATION_SECTION
                    )
                ]
            )
        ).result(2)

        example_config = config[0].get("exampleConfiguration")

        ls.show_message(f"makrellServer.exampleConfiguration value: {example_config}")

    except Exception as e:
        ls.show_message_log(f"Error ocurred: {e}")


@mr_server.command(MakrellLanguageServer.CMD_UNREGISTER_COMPLETIONS)
async def unregister_completions(ls: MakrellLanguageServer, *args):
    """Unregister completions method on the client."""
    params = lsp.UnregistrationParams(
        unregisterations=[
            lsp.Unregistration(
                id=str(uuid.uuid4()), method=lsp.TEXT_DOCUMENT_COMPLETION
            )
        ]
    )
    response = await ls.unregister_capability_async(params)
    if response is None:
        ls.show_message("Successfully unregistered completions method")
    else:
        ls.show_message(
            "Error happened during completions unregistration.", lsp.MessageType.Error
        )


def add_arguments(parser):
    parser.description = "simple Makrell server example"

    parser.add_argument("--tcp", action="store_true", help="Use TCP server")
    parser.add_argument("--ws", action="store_true", help="Use WebSocket server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind to this address")
    parser.add_argument("--port", type=int, default=2087, help="Bind to this port")


def main():
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    args = parser.parse_args()

    if args.tcp:
        mr_server.start_tcp(args.host, args.port)
    elif args.ws:
        mr_server.start_ws(args.host, args.port)
    else:
        mr_server.start_io()


if __name__ == "__main__":
    main()
