"""Unit tests for SkillForge configuration loading."""

import tempfile
from pathlib import Path

import pytest
import yaml

from skillforge import SkillForgeConfig, load_config, find_config_file


class TestSkillForgeConfig:
    """Tests for the SkillForgeConfig dataclass."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        config = SkillForgeConfig()

        assert config.skill_paths == ["./skills/*"]
        assert config.meta_skill is None
        assert config.skill_mode == "progressive"

    def test_custom_values(self) -> None:
        """Test that custom values are accepted."""
        config = SkillForgeConfig(
            skill_paths=["./agents/**/skills/*", "./shared/*"],
            meta_skill="./my-meta-skill",
            skill_mode="eager",
        )

        assert config.skill_paths == ["./agents/**/skills/*", "./shared/*"]
        assert config.meta_skill == "./my-meta-skill"
        assert config.skill_mode == "eager"

    def test_invalid_skill_mode_raises_error(self) -> None:
        """Test that invalid skill_mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid skill_mode"):
            SkillForgeConfig(skill_mode="invalid")


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_returns_defaults_when_no_config_file(self) -> None:
        """Test that defaults are returned when no config file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # No config file in tmpdir
            config = load_config(Path(tmpdir) / "nonexistent.yaml")

            assert config.skill_paths == ["./skills/*"]
            assert config.meta_skill is None
            assert config.skill_mode == "progressive"

    def test_loads_config_from_file(self) -> None:
        """Test that config is loaded from a YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".skillforge.yaml"
            config_data = {
                "skill_paths": ["./custom/path/*"],
                "meta_skill": "./custom-meta",
                "skill_mode": "eager",
            }
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            config = load_config(config_path)

            assert config.skill_paths == ["./custom/path/*"]
            assert config.meta_skill == "./custom-meta"
            assert config.skill_mode == "eager"

    def test_handles_empty_config_file(self) -> None:
        """Test that empty config file returns defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".skillforge.yaml"
            config_path.touch()  # Empty file

            config = load_config(config_path)

            assert config.skill_paths == ["./skills/*"]

    def test_ignores_unknown_fields(self) -> None:
        """Test that unknown fields in config are ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".skillforge.yaml"
            config_data = {
                "skill_paths": ["./skills/*"],
                "unknown_field": "should be ignored",
            }
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            config = load_config(config_path)

            assert config.skill_paths == ["./skills/*"]
            # No error raised for unknown field


class TestFindConfigFile:
    """Tests for the find_config_file function."""

    def test_finds_config_in_current_directory(self) -> None:
        """Test that config file is found in current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = (Path(tmpdir) / ".skillforge.yaml").resolve()
            config_path.touch()

            found = find_config_file(Path(tmpdir))

            assert found == config_path

    def test_finds_config_in_parent_directory(self) -> None:
        """Test that config file is found in parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config in parent
            config_path = (Path(tmpdir) / ".skillforge.yaml").resolve()
            config_path.touch()

            # Create subdirectory
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()

            found = find_config_file(subdir)

            assert found == config_path

    def test_returns_none_when_not_found(self) -> None:
        """Test that None is returned when no config file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # No config file
            found = find_config_file(Path(tmpdir))

            # Since we're in a temp dir with no parents having config,
            # it should return None
            assert found is None

    def test_finds_yml_variant(self) -> None:
        """Test that .skillforge.yml variant is also found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = (Path(tmpdir) / ".skillforge.yml").resolve()
            config_path.touch()

            found = find_config_file(Path(tmpdir))

            assert found == config_path
