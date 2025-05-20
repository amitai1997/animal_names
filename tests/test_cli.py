"""Tests for the CLI module."""

import sys
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

from src.cli import main, parse_args, WIKIPEDIA_URL


@pytest.mark.parametrize(
    "args,expected",
    [
        (["--output", "report.html"], Path("report.html")),
        (["--output", "report.html", "--workers", "16"], Path("report.html")),
        (["--output", "report.html", "--skip-download"], Path("report.html")),
        (["--output", "report.html", "--verbose"], Path("report.html")),
        (["--output", "report.html", "--quiet"], Path("report.html")),
    ],
)
def test_parse_args_output(args, expected, monkeypatch):
    """Test that parse_args correctly parses the output argument."""
    monkeypatch.setattr(sys, "argv", ["cli.py"] + args)
    parsed_args = parse_args()
    assert parsed_args.output == expected


@pytest.mark.parametrize(
    "args,expected",
    [
        (["--output", "report.html"], 8),  # Default workers
        (["--output", "report.html", "--workers", "16"], 16),
        (["--output", "report.html", "--workers", "4"], 4),
    ],
)
def test_parse_args_workers(args, expected, monkeypatch):
    """Test that parse_args correctly parses the workers argument."""
    monkeypatch.setattr(sys, "argv", ["cli.py"] + args)
    parsed_args = parse_args()
    assert parsed_args.workers == expected


@pytest.mark.parametrize(
    "args,expected",
    [
        (["--output", "report.html"], False),  # Default skip_download
        (["--output", "report.html", "--skip-download"], True),
    ],
)
def test_parse_args_skip_download(args, expected, monkeypatch):
    """Test that parse_args correctly parses the skip_download argument."""
    monkeypatch.setattr(sys, "argv", ["cli.py"] + args)
    parsed_args = parse_args()
    assert parsed_args.skip_download == expected


def test_parse_args_help(monkeypatch, capsys):
    """Test that parse_args shows help and exits when called with --help."""
    monkeypatch.setattr(sys, "argv", ["cli.py", "--help"])
    with pytest.raises(SystemExit):
        parse_args()
    captured = capsys.readouterr()
    assert "Animal names collateral adjective scraper" in captured.out
    assert "--output" in captured.out


def test_main_creates_directories(temp_dir, monkeypatch):
    """Test that main creates required directories."""
    output_path = temp_dir / "output.html"
    image_dir = temp_dir / "images"
    manifest_path = temp_dir / "manifest.json"
    html_snapshot_path = temp_dir / "snapshot.html"

    args = [
        "--output", str(output_path),
        "--image-dir", str(image_dir),
        "--manifest", str(manifest_path),
        "--html-snapshot", str(html_snapshot_path),
    ]

    monkeypatch.setattr(sys, "argv", ["cli.py"] + args)

    # Mock all functions to avoid external dependencies
    with patch("src.cli.fetch_html"), \
         patch("src.cli.parse_table", return_value={}), \
         patch("src.cli.download_images"), \
         patch("src.cli.setup_jinja_env"), \
         patch("src.cli.load_template"), \
         patch("src.cli.load_manifest"), \
         patch("src.cli.generate_report"), \
         patch("src.cli.copy_static_assets"):
         
        main()

    # Check that directories were created
    assert output_path.parent.exists()
    assert image_dir.exists()
    assert manifest_path.parent.exists()
    assert html_snapshot_path.parent.exists()


def test_main_fetch_html_when_snapshot_not_exists(temp_dir, monkeypatch):
    """Test that main calls fetch_html when the snapshot doesn't exist."""
    output_path = temp_dir / "output.html"
    html_snapshot_path = temp_dir / "snapshot.html"
    
    args = [
        "--output", str(output_path),
        "--html-snapshot", str(html_snapshot_path),
    ]

    monkeypatch.setattr(sys, "argv", ["cli.py"] + args)

    # Create mocks
    fetch_html_mock = MagicMock()
    parse_table_mock = MagicMock(return_value={})
    download_images_mock = MagicMock()
    
    # Mock all functions
    with patch("src.cli.fetch_html", fetch_html_mock), \
         patch("src.cli.parse_table", parse_table_mock), \
         patch("src.cli.download_images", download_images_mock), \
         patch("src.cli.setup_jinja_env"), \
         patch("src.cli.load_template"), \
         patch("src.cli.load_manifest"), \
         patch("src.cli.generate_report"), \
         patch("src.cli.copy_static_assets"):
         
        main()

    # Check that fetch_html was called
    fetch_html_mock.assert_called_once_with(WIKIPEDIA_URL, html_snapshot_path)


def test_main_skip_download(temp_dir, monkeypatch):
    """Test that main skips download when --skip-download is set."""
    output_path = temp_dir / "output.html"
    manifest_path = temp_dir / "manifest.json"
    
    # Create a fake manifest file
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_data = {"adjective": [{"name": "animal", "image_path": "image.jpg"}]}
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)
    
    args = [
        "--output", str(output_path),
        "--manifest", str(manifest_path),
        "--skip-download",
    ]

    monkeypatch.setattr(sys, "argv", ["cli.py"] + args)

    # Mock functions
    download_images_mock = MagicMock()
    
    with patch("src.cli.fetch_html"), \
         patch("src.cli.parse_table", return_value={}), \
         patch("src.cli.download_images", download_images_mock), \
         patch("src.cli.setup_jinja_env"), \
         patch("src.cli.load_template"), \
         patch("src.cli.load_manifest"), \
         patch("src.cli.generate_report"), \
         patch("src.cli.copy_static_assets"):
         
        result = main()

    # Check that download_images was not called
    download_images_mock.assert_not_called()
    assert result == 0


def test_main_skip_download_no_manifest(temp_dir, monkeypatch):
    """Test that main fails when --skip-download is set but manifest doesn't exist."""
    output_path = temp_dir / "output.html"
    manifest_path = temp_dir / "manifest.json"
    
    args = [
        "--output", str(output_path),
        "--manifest", str(manifest_path),
        "--skip-download",
    ]

    monkeypatch.setattr(sys, "argv", ["cli.py"] + args)

    # Mock functions
    with patch("src.cli.fetch_html"), \
         patch("src.cli.parse_table", return_value={}), \
         patch("src.cli.setup_jinja_env"), \
         patch("src.cli.load_template"), \
         patch("src.cli.generate_report"), \
         patch("src.cli.copy_static_assets"):
         
        result = main()

    # Check that the function returned an error code
    assert result == 1


@pytest.mark.parametrize(
    "verbose,quiet,expected_level",
    [
        (True, False, "DEBUG"),
        (False, True, "ERROR"),
        (False, False, "INFO"),  # Default
    ],
)
def test_main_logging_level(temp_dir, monkeypatch, verbose, quiet, expected_level):
    """Test that main sets the correct logging level based on verbosity flags."""
    output_path = temp_dir / "output.html"
    
    args = ["--output", str(output_path)]
    if verbose:
        args.append("--verbose")
    if quiet:
        args.append("--quiet")

    monkeypatch.setattr(sys, "argv", ["cli.py"] + args)

    # Mock set_level function
    set_level_mock = MagicMock()
    
    with patch("src.cli.logging.getLogger", return_value=MagicMock(setLevel=set_level_mock)), \
         patch("src.cli.fetch_html"), \
         patch("src.cli.parse_table", return_value={}), \
         patch("src.cli.download_images"), \
         patch("src.cli.setup_jinja_env"), \
         patch("src.cli.load_template"), \
         patch("src.cli.load_manifest"), \
         patch("src.cli.generate_report"), \
         patch("src.cli.copy_static_assets"):
         
        main()

    # Check that setLevel was called with the expected level
    if expected_level == "DEBUG":
        set_level_mock.assert_any_call(pytest.importorskip("logging").DEBUG)
    elif expected_level == "ERROR":
        set_level_mock.assert_any_call(pytest.importorskip("logging").ERROR)
    # No need to check INFO case as it's the default and not explicitly set


@pytest.mark.integration
def test_end_to_end_integration(temp_dir, monkeypatch):
    """Test an end-to-end integration of the CLI with minimal mocks."""
    # Create necessary paths
    output_path = temp_dir / "output.html"
    image_dir = temp_dir / "images"
    manifest_path = temp_dir / "manifest.json"
    html_snapshot_path = temp_dir / "snapshot.html"
    template_dir = temp_dir / "templates"
    static_dir = temp_dir / "static"
    
    # Create template dir and copy template
    template_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        Path(__file__).parent.parent / "templates", 
        template_dir,
        dirs_exist_ok=True
    )

    # Create static dir and copy static files
    static_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        Path(__file__).parent.parent / "static", 
        static_dir,
        dirs_exist_ok=True
    )

    args = [
        "--output", str(output_path),
        "--image-dir", str(image_dir),
        "--manifest", str(manifest_path),
        "--html-snapshot", str(html_snapshot_path),
        "--template-dir", str(template_dir),
        "--static-dir", str(static_dir),
        "--skip-download",  # Skip download to avoid network requests
    ]

    monkeypatch.setattr(sys, "argv", ["cli.py"] + args)

    # Mock only the fetch_html and parse_table functions
    # This keeps most of the real functionality intact
    animal_data = {"feline": [{"name": "cat", "image_path": "cat.jpg"}]}
    
    # Create a manifest file
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(animal_data, f)
    
    with patch("src.cli.fetch_html"), \
         patch("src.cli.parse_table", return_value=animal_data):
         
        result = main()

    # Verify output
    assert result == 0
    assert output_path.exists()
    
    # Verify content of the HTML file
    with open(output_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        assert "feline" in html_content
        assert "cat" in html_content
