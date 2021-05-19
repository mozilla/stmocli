from functools import partial
import hashlib
import json
import os

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from click.testing import CliRunner
from httmock import all_requests, HTTMock, urlmatch
import pytest

from stmocli import cli
from stmocli.conf import default_path as conf_path
from stmocli.conf import Conf


with open('tests/data/49741.json', 'rt') as infile:
    query_49741_response = infile.read()

with open('tests/data/62375.json', 'rt') as infile:
    query_62375_response = infile.read()


@all_requests
def response_49741_content(url, request):
    return {
        'status_code': 200,
        'content': query_49741_response
    }


@all_requests
def response_62375_content(url, request):
    return {
        'status_code': 200,
        'content': query_62375_response
    }


@all_requests
def push_response(url, request):
    return {'status_code': 200,
            'content': '{}'}


@all_requests
def push_response_fail(url, request):
    return {'status_code': 500,
            'content': '{}'}


@urlmatch(path=r'.*/fork')
def fork_response(url, request):
    return {
        'status_code': 200,
        'content': json.dumps({
            'id': '1234',
            'query': 'SELECT * FROM foo',
            'data_source_id': 0,
        })}


@all_requests
def not_found_response(url, request):
    return {'status_code': 404}


@pytest.fixture
def runner():
    r = CliRunner()
    r.invoke = partial(r.invoke, catch_exceptions=False)
    return r


def test_init(runner):
    with runner.isolated_filesystem():
        runner.invoke(cli.cli, ["init"])
        assert os.path.isfile(conf_path)


def test_init_is_idempotent(runner):
    spam = '{"spam": "spam"}\n'
    with runner.isolated_filesystem():
        assert not os.path.exists(conf_path)
        r1 = runner.invoke(cli.cli, ["init"])
        assert r1.exit_code == 0
        assert os.path.exists(conf_path)
        with open(conf_path, "w") as f:
            f.write(spam)
        r2 = runner.invoke(cli.cli, ["init"])
        assert r2.exit_code == 0
        with open(conf_path, "r") as f:
            assert f.read() == spam


def test_track(runner):
    query_id = '49741'
    file_name = 'poc.sql'

    with runner.isolated_filesystem():
        with HTTMock(response_49741_content):
            result = runner.invoke(cli.cli, [
                '--redash_api_key',
                'TOTALLY_FAKE_KEY',
                "track",
                query_id,
                file_name,
            ])
            assert result.exit_code == 0

        # Verify we save the query to the right file
        assert os.path.isfile(file_name)
        with open(file_name, 'r') as query:
            assert "SELECT" in query.read()

        # Verify we save the query_id to the config file
        assert os.path.isfile(conf_path)
        with open(conf_path, 'r') as conf_file:
            config = json.loads(conf_file.read())
            assert file_name in config
            assert config[file_name]['id'] == query_id


def test_track_autostub(runner):
    query_id = '49741'
    expected_filename = "st_mocli_poc.sql"

    with runner.isolated_filesystem():
        with HTTMock(response_49741_content):
            runner.invoke(
                cli.cli, [
                    "--redash_api_key",
                    "TOTALLY_FAKE_KEY",
                    "track",
                    query_id,
                 ],
                input="\n")

        assert os.path.isfile(expected_filename)


def setup_tracked_query(runner, query_id, file_name, content):
    with HTTMock(content):
        runner.invoke(cli.cli, [
            "track",
            query_id,
            file_name
        ])

    # Read the saved query
    assert os.path.isfile(file_name)
    with open(file_name, 'r') as fin:
        query_contents = fin.read()
    return query_contents


def update_tracked_query(file_name, original_query):
    updated_query = original_query + "--appended"
    with open(file_name, 'w') as fout:
        fout.write(updated_query)
    return updated_query


def test_pull(runner):
    with runner.isolated_filesystem():
        query_49741_before = setup_tracked_query(runner, '49741', '49741.sql',
                                                 response_49741_content)
        setup_tracked_query(runner, '62375', '62375.sql', response_62375_content)

        with open('49741.sql', 'w') as query_49741_contents:
            query_49741_contents.write("SELECT nonsense FROM testing")
        with open('62375.sql', 'w') as query_62375_contents:
            query_62375_contents.write("SELECT gibberish FROM testing")

        with HTTMock(response_49741_content):
            result = runner.invoke(cli.cli, [
                '--redash_api_key',
                'TOTALLY_FAKE_KEY',
                "pull",
                "49741.sql",
            ])
            assert result.exit_code == 0

        with open('49741.sql', 'r') as query_49741_contents:
            assert query_49741_contents.read() == query_49741_before

        with open('62375.sql', 'r') as query_62375_contents:
            assert query_62375_contents.read() == "SELECT gibberish FROM testing"


def test_push_tracked(runner):
    query_id = '49741'
    file_name = 'poc.sql'

    with runner.isolated_filesystem():
        # Track the example query
        query_before = setup_tracked_query(runner, query_id, file_name, response_49741_content)
        # Overwrite with a new query string
        query_after = update_tracked_query(file_name, query_before)

        # Now push the result
        with HTTMock(push_response):
            push_result = runner.invoke(cli.cli, [
                "push",
                file_name
            ])

        m = hashlib.md5(query_after.encode("utf-8"))
        expected_output = "Query ID {} updated with content from {} (md5 {})".format(
            query_id, file_name, m.hexdigest())
        assert push_result.output.strip() == expected_output


def test_push_multi(runner):
    with runner.isolated_filesystem():
        query_49741_before = setup_tracked_query(runner, '49741', '49741.sql',
                                                 response_49741_content)
        query_62375_before = setup_tracked_query(runner, '62375', '62375.sql',
                                                 response_62375_content)

        # Overwrite with a new query string
        query_49741_after = update_tracked_query('49741.sql', query_49741_before)
        query_62375_after = update_tracked_query('62375.sql', query_62375_before)

        # Now push the result
        with HTTMock(push_response):
            push_result = runner.invoke(cli.cli, [
                "push",
                "49741.sql",
                "62375.sql"
            ])

        m = hashlib.md5(query_62375_after.encode("utf-8"))
        expected_output_62375 = "Query ID 62375 updated with content from 62375.sql " + \
                                "(md5 {})".format(m.hexdigest())
        m = hashlib.md5(query_49741_after.encode("utf-8"))
        expected_output_49741 = "Query ID 49741 updated with content from 49741.sql " + \
                                "(md5 {})".format(m.hexdigest())

        assert push_result.output.strip() == expected_output_49741 + "\n" + expected_output_62375


def test_push_all(runner):
    with runner.isolated_filesystem():
        query_49741_before = setup_tracked_query(runner, '49741', '49741.sql',
                                                 response_49741_content)
        query_62375_before = setup_tracked_query(runner, '62375', '62375.sql',
                                                 response_62375_content)

        # Overwrite with a new query string
        query_49741_after = update_tracked_query('49741.sql', query_49741_before)
        query_62375_after = update_tracked_query('62375.sql', query_62375_before)

        # Now push the result
        with HTTMock(push_response):
            push_result = runner.invoke(cli.cli, [
                "push"
            ])

        expected_output = set([
            "Query ID 62375 updated with content from 62375.sql " +
            "(md5 {})".format(hashlib.md5(query_62375_after.encode("utf-8")).hexdigest()),

            "Query ID 49741 updated with content from 49741.sql " +
            "(md5 {})".format(hashlib.md5(query_49741_after.encode("utf-8")).hexdigest())
        ])

        actual_output = set(push_result.output.strip().split("\n"))

        assert expected_output == actual_output


def test_push_fail(runner):
    query_id = '49741'
    file_name = 'poc.sql'

    with runner.isolated_filesystem():
        query_before = setup_tracked_query(runner, query_id, file_name, response_49741_content)
        update_tracked_query(file_name, query_before)

        # Now push the result, expecting a failure
        with HTTMock(push_response_fail):
            push_result = runner.invoke(cli.cli, [
                "push",
                file_name
            ])

        expected_output = "Failed to update query from {}:".format(file_name)
        assert push_result.output.startswith(expected_output)
        assert "500" in push_result.output


def test_push_untracked(runner):
    file_name = 'missing.sql'

    # Try to push a nonexistent query
    with HTTMock(push_response):
        push_result = runner.invoke(cli.cli, [
            "push",
            file_name
        ])

    assert "No such query" in push_result.output


@patch("click.launch")
def test_view_unknown(launch, runner):
    with runner.isolated_filesystem():
        result = runner.invoke(cli.cli, ["view", "spam"])
        assert result.exit_code != 0
        assert "No such query" in result.output
        launch.assert_not_called()


@patch("click.launch")
def test_view(launch, runner):
    query_id = '49741'
    file_name = 'poc.sql'

    with runner.isolated_filesystem():
        setup_tracked_query(runner, query_id, file_name, response_49741_content)
        result = runner.invoke(cli.cli, ["view", file_name])
    assert result.exit_code == 0
    launch.assert_called_once()
    args, _kwargs = launch.call_args
    assert args[0].endswith("/" + query_id)


def test_fork(runner):
    query_id = '49741'
    file_name = 'poc.sql'

    with runner.isolated_filesystem():
        setup_tracked_query(runner, query_id, file_name, response_49741_content)
        with HTTMock(fork_response, response_49741_content):
            result = runner.invoke(cli.cli, ["fork", file_name, "fork.sql"])
        assert os.path.exists("fork.sql")
        assert Conf().get_query("fork.sql")
    assert result.exit_code == 0


def test_fork_rejects_bogus_filename(runner):
    with runner.isolated_filesystem():
        result = runner.invoke(cli.cli, ["fork", "spam", "fork.sql"])
    assert result.exit_code == 1
    assert not os.path.exists("fork.sql")
    assert "no file or query" in result.output


def test_fork_handles_404(runner):
    with runner.isolated_filesystem():
        with HTTMock(not_found_response):
            result = runner.invoke(cli.cli, ["fork", "99999", "fork.sql"])
    assert result.exit_code == 1
    assert "Couldn't find a query with ID" in result.output


def test_fork_rejects_untracked_file(runner):
    with runner.isolated_filesystem():
        with open("spam.sql", "w") as f:
            f.write("eggs")
        result = runner.invoke(cli.cli, ["fork", "spam.sql", "fork.sql"])
    assert result.exit_code == 1
    assert "track" in result.output
