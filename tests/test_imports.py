def test_package_exposes_version():
    import kms_cli

    assert isinstance(kms_cli.__version__, str)
    assert kms_cli.__version__


def test_cli_main_smoke():
    from kms_cli.cli import build_parser

    assert build_parser().prog == "kms"
