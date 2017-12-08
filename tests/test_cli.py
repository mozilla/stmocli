import pytest
import click
import os
from click.testing import CliRunner
from stmocli import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_init(runner):
    with runner.isolated_filesystem():
        runner.invoke(cli.init)

        assert os.path.isfile('.stmocli.conf')
