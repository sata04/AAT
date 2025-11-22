from core import version


def test_app_version_prefers_pyproject():
    pyproject_version = version._read_from_pyproject()
    assert pyproject_version is not None
    assert pyproject_version == version.APP_VERSION
