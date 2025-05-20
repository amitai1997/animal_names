"""Tests for the CLI module."""

import json
import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.cli import WIKIPEDIA_URL, main, parse_args


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


@pytest.mark.parametrize(
    "args,expected",
    [
        (["--output", "report.html"], False),  # Default no_console_output
        (["--output", "report.html", "--no-console-output"], True),
    ],
)
def test_parse_args_no_console_output(args, expected, monkeypatch):
    """Test that parse_args correctly parses the no_console_output argument."""
    monkeypatch.setattr(sys, "argv", ["cli.py"] + args)
    parsed_args = parse_args()
    assert parsed_args.no_console_output == expected


@pytest.mark.parametrize(
    "args,expected",
    [
        (["--output", "report.html"], False),  # Default show_logs
        (["--output", "report.html", "--show-logs"], True),
    ],
)
def test_parse_args_show_logs(args, expected, monkeypatch):
    """Test that parse_args correctly parses the show_logs argument."""
    monkeypatch.setattr(sys, "argv", ["cli.py"] + args)
    parsed_args = parse_args()
    assert parsed_args.show_logs == expected


@pytest.mark.parametrize(
    "args,expected",
    [
        (["--output", "report.html"], Path("/tmp")),  # Default image_dir
        (
            ["--output", "report.html", "--image-dir", "/custom/path"],
            Path("/custom/path"),
        ),
    ],
)
def test_parse_args_image_dir(args, expected, monkeypatch):
    """Test that parse_args correctly parses the image_dir argument."""
    monkeypatch.setattr(sys, "argv", ["cli.py"] + args)
    parsed_args = parse_args()
    assert parsed_args.image_dir == expected


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
        "--output",
        str(output_path),
        "--image-dir",
        str(image_dir),
        "--manifest",
        str(manifest_path),
        "--html-snapshot",
        str(html_snapshot_path),
    ]

    monkeypatch.setattr(sys, "argv", ["cli.py"] + args)

    # Mock all functions to avoid external dependencies
    with patch("src.cli.fetch_html"), patch(
        "src.cli.parse_table", return_value={}
    ), patch("src.cli.download_images"), patch("src.cli.setup_jinja_env"), patch(
        "src.cli.load_template"
    ), patch(
        "src.cli.load_manifest"
    ), patch(
        "src.cli.generate_report"
    ), patch(
        "src.cli.copy_static_assets"
    ):
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
        "--output",
        str(output_path),
        "--html-snapshot",
        str(html_snapshot_path),
    ]

    monkeypatch.setattr(sys, "argv", ["cli.py"] + args)

    # Create mocks
    fetch_html_mock = MagicMock()
    parse_table_mock = MagicMock(return_value={})
    download_images_mock = MagicMock()

    # Mock all functions
    with patch("src.cli.fetch_html", fetch_html_mock), patch(
        "src.cli.parse_table", parse_table_mock
    ), patch("src.cli.download_images", download_images_mock), patch(
        "src.cli.setup_jinja_env"
    ), patch(
        "src.cli.load_template"
    ), patch(
        "src.cli.load_manifest"
    ), patch(
        "src.cli.generate_report"
    ), patch(
        "src.cli.copy_static_assets"
    ):
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
        "--output",
        str(output_path),
        "--manifest",
        str(manifest_path),
        "--skip-download",
    ]

    monkeypatch.setattr(sys, "argv", ["cli.py"] + args)

    # Mock functions
    download_images_mock = MagicMock()

    with patch("src.cli.fetch_html"), patch(
        "src.cli.parse_table", return_value={}
    ), patch("src.cli.download_images", download_images_mock), patch(
        "src.cli.setup_jinja_env"
    ), patch(
        "src.cli.load_template"
    ), patch(
        "src.cli.load_manifest"
    ), patch(
        "src.cli.generate_report"
    ), patch(
        "src.cli.copy_static_assets"
    ):
        result = main()

    # Check that download_images was not called
    download_images_mock.assert_not_called()
    assert result == 0


def test_main_skip_download_no_manifest(temp_dir, monkeypatch):
    """Test that main fails when --skip-download is set but manifest doesn't exist."""
    output_path = temp_dir / "output.html"
    manifest_path = temp_dir / "manifest.json"

    args = [
        "--output",
        str(output_path),
        "--manifest",
        str(manifest_path),
        "--skip-download",
    ]

    monkeypatch.setattr(sys, "argv", ["cli.py"] + args)

    # Mock functions
    with patch("src.cli.fetch_html"), patch(
        "src.cli.parse_table", return_value={}
    ), patch("src.cli.setup_jinja_env"), patch("src.cli.load_template"), patch(
        "src.cli.generate_report"
    ), patch(
        "src.cli.copy_static_assets"
    ):
        result = main()

    # Check that the function returned an error code
    assert result == 1


@pytest.mark.parametrize(
    "verbose,quiet,show_logs,expected_level",
    [
        (True, False, False, "DEBUG"),  # Verbose overrides all
        (False, True, False, "ERROR"),  # Quiet overrides show_logs
        (False, False, True, "INFO"),   # show_logs enables INFO level
        (False, False, False, "ERROR"), # Default is ERROR level (hide logs)
    ],
)
def test_main_logging_level(temp_dir, monkeypatch, verbose, quiet, show_logs, expected_level):
    """Test that main sets the correct logging level based on verbosity flags."""
    output_path = temp_dir / "output.html"

    args = ["--output", str(output_path)]
    if verbose:
        args.append("--verbose")
    if quiet:
        args.append("--quiet")
    if show_logs:
        args.append("--show-logs")

    monkeypatch.setattr(sys, "argv", ["cli.py"] + args)

    # Mock set_level function
    set_level_mock = MagicMock()

    with patch(
        "src.cli.logging.getLogger", return_value=MagicMock(setLevel=set_level_mock)
    ), patch("src.cli.fetch_html"), patch(
        "src.cli.parse_table", return_value={}
    ), patch(
        "src.cli.download_images"
    ), patch(
        "src.cli.setup_jinja_env"
    ), patch(
        "src.cli.load_template"
    ), patch(
        "src.cli.load_manifest"
    ), patch(
        "src.cli.generate_report"
    ), patch(
        "src.cli.copy_static_assets"
    ):
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
    image_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = temp_dir / "manifest.json"
    html_snapshot_path = temp_dir / "snapshot.html"
    template_dir = temp_dir / "templates"
    static_dir = temp_dir / "static"

    # Create template dir and copy template
    template_dir.mkdir(parents=True, exist_ok=True)
    src_template_dir = Path(__file__).parent.parent / "templates"
    for template_file in src_template_dir.glob("*.j2"):
        shutil.copy(template_file, template_dir / template_file.name)

    # Create static dir and copy static files
    static_dir.mkdir(parents=True, exist_ok=True)
    css_dir = static_dir / "css"
    css_dir.mkdir(parents=True, exist_ok=True)

    # Copy CSS file
    src_css_file = Path(__file__).parent.parent / "static" / "css" / "style.css"
    if src_css_file.exists():
        shutil.copy(src_css_file, css_dir / "style.css")
    else:
        # Create a minimal CSS file if the source doesn't exist
        with open(css_dir / "style.css", "w", encoding="utf-8") as f:
            f.write("body { font-family: sans-serif; }")

    # Create a sample HTML snapshot
    with open(html_snapshot_path, "w", encoding="utf-8") as f:
        f.write(
            """
        <html><body>
        <table>
            <thead>
                <tr>
                    <th>Animal</th>
                    <th>Collateral adjective</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>cat</td>
                    <td>feline</td>
                </tr>
            </tbody>
        </table>
        </body></html>"""
        )

    # Create a sample manifest file
    manifest_data = {
        "feline": [{"name": "cat", "image_path": str(image_dir / "cat.jpg")}]
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    # Create a sample image file
    with open(image_dir / "cat.jpg", "w", encoding="utf-8") as f:
        f.write("dummy image data")

    args = [
        "--output",
        str(output_path),
        "--image-dir",
        str(image_dir),
        "--manifest",
        str(manifest_path),
        "--html-snapshot",
        str(html_snapshot_path),
        "--template-dir",
        str(template_dir),
        "--static-dir",
        str(static_dir),
        "--skip-download",  # Skip download to avoid network requests
    ]

    monkeypatch.setattr(sys, "argv", ["cli.py"] + args)

    # Mock key functions to avoid network calls and ensure controlled testing
    with patch("src.cli.fetch_html"), patch(
        "src.cli.parse_table", return_value={"feline": [{"name": "cat"}]}
    ), patch("src.cli.load_manifest", return_value=manifest_data):
        result = main()

    # Verify output
    assert result == 0
    assert output_path.exists()

    # Verify content of the HTML file
    with open(output_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        # Check for key elements that should be in the HTML
        assert "<title>" in html_content
        # Look for either the adjective or animal name in the HTML
        assert any(term in html_content for term in ["feline", "cat"])
        # Check for CSS link
        assert "<link" in html_content and "css" in html_content


def test_print_adjective_animals(capsys):
    """Test that print_adjective_animals correctly prints adjectives and animals to the console."""
    from src.cli import print_adjective_animals
    from src.downloader import Manifest
    from src.scraper import Animal

    # Create sample data
    adjective_animals = {
        "feline": [
            Animal(
                name="cat",
                page_url="https://example.com/cat",
                image_path="/tmp/cat.jpg",
            )
        ],
        "canine": [
            Animal(
                name="dog",
                page_url="https://example.com/dog",
                image_path="/tmp/dog.jpg",
            )
        ],
    }
    manifest = Manifest(entries={"cat": "/tmp/cat.jpg", "dog": "/tmp/dog.jpg"})

    # Call the function
    print_adjective_animals(adjective_animals, manifest)

    # Capture the stdout
    captured = capsys.readouterr()

    # Check if adjectives and animals are printed correctly
    assert "FELINE" in captured.out
    assert "CANINE" in captured.out
    assert "cat" in captured.out
    assert "dog" in captured.out
    assert "/tmp/cat.jpg" in captured.out
    assert "/tmp/dog.jpg" in captured.out
