from pathlib import Path
import unittest
import re
from unittest.mock import patch

import pytest
from pytest_mock import MockerFixture

from typer.testing import CliRunner

from tempfile import NamedTemporaryFile
from ausdex import main


class TestMain(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_version(self):
        result = self.runner.invoke(main.app, ["--version"])
        assert result.exit_code == 0
        assert re.match(r"\d+\.\d+\.\d+", result.stdout)

    @patch("typer.launch")
    def test_repo(self, mock_launch):
        result = self.runner.invoke(main.app, ["repo"])
        assert result.exit_code == 0
        mock_launch.assert_called_once()
        self.assertIn("https://github.com/rbturnbull/ausdex", str(mock_launch.call_args))

    @patch("subprocess.run")
    def test_docs_live(self, mock_subprocess):
        result = self.runner.invoke(main.app, ["docs"])
        assert result.exit_code == 0
        mock_subprocess.assert_called_once()
        self.assertIn("sphinx-autobuild", str(mock_subprocess.call_args))

    @patch("webbrowser.open_new")
    @patch("subprocess.run")
    def test_docs_static(self, mock_subprocess, mock_open_web):
        result = self.runner.invoke(main.app, ["docs", "--no-live"])
        assert result.exit_code == 0
        mock_subprocess.assert_called_once()
        self.assertIn("sphinx-build", str(mock_subprocess.call_args))
        mock_open_web.assert_called_once()

    def test_inflation(self):
        result = self.runner.invoke(
            main.app,
            ["inflation", "13", "March 1991", "--evaluation-date", "June 2010"],
        )
        assert result.exit_code == 0
        assert "21.14" in result.stdout

    def test_inflation_melbourne(self):
        result = self.runner.invoke(
            main.app,
            ["inflation", "13", "March 1991", "--evaluation-date", "May 2022", "--location", "melbourne"],
        )
        assert result.exit_code == 0
        assert "26.95" in result.stdout

    def test_inflation_perth(self):
        result = self.runner.invoke(
            main.app,
            ["inflation", "1", "March 1979", "--location", "Perth", "--evaluation-date", "May 2022"],
        )
        assert result.exit_code == 0
        assert "5.29" in result.stdout


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_show(mocker: MockerFixture, check_viz):
    from plotly.graph_objects import Figure

    return mocker.patch.object(Figure, "show")


@pytest.fixture
def mock_write_image(mocker: MockerFixture, check_viz):
    from plotly.graph_objects import Figure

    return mocker.patch.object(Figure, "write_image")


@pytest.fixture
def mock_write_html(mocker: MockerFixture, check_viz):
    from plotly.graph_objects import Figure

    return mocker.patch.object(Figure, "write_html")


def test_plot_cpi(check_viz, runner, mock_show):
    result = runner.invoke(
        main.app,
        ["plot-cpi"],
    )
    assert result.exit_code == 0
    mock_show.assert_called_once()


def test_plot_cpi_output(check_viz, runner, mock_show, mock_write_image):
    result = runner.invoke(
        main.app,
        ["plot-cpi", "--output", "tmp.jpg", "--location", "Melbourne"],
    )
    assert result.exit_code == 0
    mock_show.assert_called_once()
    mock_write_image.assert_called_once()


def test_plot_inflation(check_viz, runner, mock_show):
    result = runner.invoke(
        main.app,
        ["plot-inflation", "2022"],
    )
    assert result.exit_code == 0
    mock_show.assert_called_once()


def test_plot_inflation_output(check_viz, runner, mock_show, mock_write_html):
    result = runner.invoke(
        main.app,
        ["plot-inflation", "2022", "--output", "tmp.html", "--location", "Melbourne"],
    )
    assert result.exit_code == 0
    mock_show.assert_called_once()
    mock_write_html.assert_called_once()


def test_plot_cpi_change_output(check_viz, runner, mock_show, mock_write_html):
    result = runner.invoke(
        main.app,
        ["plot-cpi-change", "--output", "tmp.html"],
    )
    assert result.exit_code == 0
    mock_show.assert_called_once()
    mock_write_html.assert_called_once()


def test_plot_inflation_output_exists(check_viz, runner):
    with NamedTemporaryFile(suffix=".html") as tmp:
        result = runner.invoke(
            main.app,
            [
                "plot-inflation",
                "01-01-2019",
                "--no-show",
                "--output",
                tmp.name,
                "--start-date",
                "06-06-1949",
            ],
        )
        assert result.exit_code == 0
        assert Path(tmp.name).exists()


def test_plot_cpi_output_exists(check_viz, runner):
    with NamedTemporaryFile(suffix=".png") as tmp:
        result = runner.invoke(
            main.app,
            [
                "plot-cpi",
                "--no-show",
                "--output",
                tmp.name,
                "--start-date",
                "06-06-1949",
            ],
        )
        assert result.exit_code == 0
        assert Path(tmp.name).exists()


def test_plot_cpi_output_exists(check_viz, runner):
    with NamedTemporaryFile(suffix=".png") as tmp:
        result = runner.invoke(
            main.app,
            [
                "plot-cpi",
                "--no-show",
                "--output",
                tmp.name,
                "--start-date",
                "06-06-1949",
            ],
        )
        assert result.exit_code == 0
        assert Path(tmp.name).exists()


def test_plot_cpi_change_output_exists(check_viz, runner):
    with NamedTemporaryFile(suffix=".png") as tmp:
        result = runner.invoke(
            main.app,
            [
                "plot-cpi-change",
                "--no-show",
                "--output",
                tmp.name,
            ],
        )
        assert result.exit_code == 0
        assert Path(tmp.name).exists()
