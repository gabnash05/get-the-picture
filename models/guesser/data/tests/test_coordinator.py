import json

from guesser_data.cli import main, parser


def test_cli_commands_and_removed_hints(tmp_path, capsys):
    args = parser().parse_args(
        ["download", "--data-root", str(tmp_path), "--class", "cat"]
    )
    assert args.profile == "production" and args.classes == ["cat"]
    assert main(["status", "--data-root", str(tmp_path), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["result"]["path"].startswith(
        str(tmp_path)
    )
    assert main(["freeze", "--json"]) == 2
    assert "export" in json.loads(capsys.readouterr().out)["error"]["hint"]
    assert main(["status", "--unknown-option", "--json"]) == 2
    assert json.loads(capsys.readouterr().out)["error"]["code"] == "usage_error"
