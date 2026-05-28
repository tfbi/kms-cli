def test_package_exposes_version():
    import kms_cli

    assert isinstance(kms_cli.__version__, str)
    assert kms_cli.__version__
