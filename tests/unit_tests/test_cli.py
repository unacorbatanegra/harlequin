from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner
from harlequin import Harlequin
from harlequin.cli import build_cli
from harlequin_duckdb import DUCKDB_OPTIONS, DuckDbAdapter


@pytest.fixture()
def mock_adapter(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_adapter = MagicMock(name="mock_duckdb_adapter", spec=DuckDbAdapter)
    mock_adapter.ADAPTER_OPTIONS = DUCKDB_OPTIONS
    mock_entrypoint = MagicMock(name="mock_entrypoint")
    mock_entrypoint.name = "duckdb"
    mock_entrypoint.load.return_value = mock_adapter
    mock_entry_points = MagicMock()
    mock_entry_points.return_value = [mock_entrypoint]
    monkeypatch.setattr("harlequin.cli.entry_points", mock_entry_points)
    return mock_adapter


@pytest.fixture()
def mock_harlequin(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = MagicMock(spec=Harlequin)
    monkeypatch.setattr("harlequin.cli.Harlequin", mock)
    return mock


@pytest.mark.parametrize("harlequin_args", ["", ":memory:"])
def test_default(
    mock_harlequin: MagicMock, mock_adapter: MagicMock, harlequin_args: str
) -> None:
    runner = CliRunner()
    res = runner.invoke(build_cli(), args=harlequin_args)
    assert res.exit_code == 0
    mock_adapter.assert_called_once_with(
        conn_str=(harlequin_args,) if harlequin_args else tuple()
    )
    mock_harlequin.assert_called_once_with(
        adapter=mock_adapter.return_value,
        max_results=100_000,
        theme="monokai",
    )


@pytest.mark.parametrize(
    "harlequin_args", ["--init-path foo", ":memory: -i foo", "-init foo"]
)
def test_custom_init_script(
    mock_harlequin: MagicMock, mock_adapter: MagicMock, harlequin_args: str
) -> None:
    runner = CliRunner()
    res = runner.invoke(build_cli(), args=harlequin_args)
    assert res.exit_code == 0
    mock_adapter.assert_called_once()
    assert mock_adapter.call_args
    assert mock_adapter.call_args.kwargs["init_path"] == Path("foo").resolve()


@pytest.mark.parametrize("harlequin_args", ["--no-init", ":memory: --no-init"])
def test_no_init_script(
    mock_harlequin: MagicMock, mock_adapter: MagicMock, harlequin_args: str
) -> None:
    runner = CliRunner()
    res = runner.invoke(build_cli(), args=harlequin_args)
    assert res.exit_code == 0
    mock_adapter.assert_called_once()
    assert mock_adapter.call_args
    assert mock_adapter.call_args.kwargs["no_init"] is True


@pytest.mark.parametrize(
    "harlequin_args", ["--theme one-dark", ":memory: -t one-dark", "foo.db -t one-dark"]
)
def test_theme(
    mock_harlequin: MagicMock, mock_adapter: MagicMock, harlequin_args: str
) -> None:
    runner = CliRunner()
    res = runner.invoke(build_cli(), args=harlequin_args)
    assert res.exit_code == 0
    mock_harlequin.assert_called_once()
    assert mock_harlequin.call_args
    assert mock_harlequin.call_args.kwargs["theme"] == "one-dark"


@pytest.mark.parametrize(
    "harlequin_args",
    [
        "--limit 10",
        "-l 1000000",
        ":memory: -l 10",
        "foo.db --limit 5000000000",
        "--limit 0",
    ],
)
def test_limit(
    mock_harlequin: MagicMock, mock_adapter: MagicMock, harlequin_args: str
) -> None:
    runner = CliRunner()
    res = runner.invoke(build_cli(), args=harlequin_args)
    assert res.exit_code == 0
    mock_harlequin.assert_called_once()
    assert mock_harlequin.call_args
    assert mock_harlequin.call_args.kwargs["max_results"] != 100_000


@pytest.mark.parametrize(
    "harlequin_args",
    [
        "--adapter duckdb",
        "-a duckdb",
        "-a DUCKDB",
    ],
)
def test_adapter_opt(
    mock_harlequin: MagicMock, mock_adapter: MagicMock, harlequin_args: str
) -> None:
    runner = CliRunner()
    res = runner.invoke(build_cli(), args=harlequin_args)
    assert res.exit_code == 0
    mock_harlequin.assert_called_once()
    assert mock_harlequin.call_args
    assert mock_harlequin.call_args.kwargs["adapter"] == mock_adapter.return_value


@pytest.mark.parametrize(
    "harlequin_args",
    [
        "--adapter foo",
        "-a bar",
    ],
)
def test_bad_adapter_opt(
    mock_harlequin: MagicMock, mock_adapter: MagicMock, harlequin_args: str
) -> None:
    runner = CliRunner()
    res = runner.invoke(build_cli(), args=harlequin_args)
    assert res.exit_code == 2
    assert "Error: Invalid value for '-a' / '--adapter'" in res.stdout