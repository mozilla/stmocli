import pytest
import click
import os
from redash_client.client import RedashClient
from click.testing import CliRunner
from stmocli import cli


@pytest.fixture
def runner():
    return CliRunner()

# @pytest.fixture
# def redash():
#     return RedashClient("SUPERFAKEAPIKEY")


def test_init(runner):
    with runner.isolated_filesystem():
        runner.invoke(cli.init)

        assert os.path.isfile('.stmocli.conf')

def test_track(runner):
    # gonna need this: https://docs.pytest.org/en/latest/monkeypatch.html
    filename = 'poc.sql'
    query_id = 49741

    with runner.isolated_filesystem():
        runner.invoke(cli.track, [
            query_id,
            filename,
        ])

        assert os.path.isfile(filename)
        with open(filename, 'r') as query:
            assert "SELECT" in query.read()
