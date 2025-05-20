"""Pytest configuration file with common fixtures."""

import os
import json
import shutil
import threading
import http.server
import socketserver
from pathlib import Path
from typing import Dict, List, Generator, Any

import pytest


@pytest.fixture
def temp_dir(tmp_path) -> Path:
    """Provide a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def sample_table_path() -> Path:
    """Return the path to the sample_table.html fixture."""
    return Path(__file__).parent / "fixtures" / "sample_table.html"


@pytest.fixture
def raw_snapshot_path() -> Path:
    """Return the path to the raw_snapshot.html fixture."""
    return Path(__file__).parent / "fixtures" / "raw_snapshot.html"


@pytest.fixture
def sample_image_path() -> Path:
    """Return the path to the sample image fixture."""
    return Path(__file__).parent / "fixtures" / "sample_image.jpg"


@pytest.fixture
def dummy_manifest_path() -> Path:
    """Return the path to the dummy manifest fixture."""
    return Path(__file__).parent / "fixtures" / "dummy_manifest.json"


@pytest.fixture
def placeholder_image_path() -> Path:
    """Return the path to the placeholder image."""
    return Path(__file__).parent.parent / "src" / "assets" / "placeholder.jpg"


@pytest.fixture
def clean_temp_images(temp_dir) -> Generator[Path, None, None]:
    """Create and clean up a temporary images directory."""
    images_dir = temp_dir / "images"
    images_dir.mkdir(exist_ok=True)
    yield images_dir
    shutil.rmtree(images_dir)


@pytest.fixture
def temp_html_snapshot(temp_dir, raw_snapshot_path) -> Path:
    """Create a temporary copy of the raw_snapshot.html."""
    temp_snapshot = temp_dir / "raw_snapshot.html"
    shutil.copy(raw_snapshot_path, temp_snapshot)
    return temp_snapshot


@pytest.fixture
def report_output_path(temp_dir) -> Path:
    """Create a path for the report output."""
    return temp_dir / "report.html"


@pytest.fixture
def temp_manifest_path(temp_dir) -> Path:
    """Create a path for a temporary manifest."""
    return temp_dir / "manifest.json"


@pytest.fixture
def dummy_manifest_content(dummy_manifest_path) -> Dict[str, List[Dict[str, str]]]:
    """Load the dummy manifest content."""
    with open(dummy_manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def test_http_server():
    """Start a test HTTP server for image download tests."""
    # Import the HTTP handler from fixtures
    from tests.fixtures.server import TestHTTPHandler
    
    # Find an available port
    with socketserver.TCPServer(("", 0), None) as s:
        port = s.server_address[1]
    
    # Create and start the server
    handler = TestHTTPHandler
    server = socketserver.TCPServer(("", port), handler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    # Return the server URL
    server_url = f"http://localhost:{port}"
    yield server_url
    
    # Clean up
    server.shutdown()
    server.server_close()


@pytest.fixture
def e2e_test_environment(temp_dir):
    """Set up a complete environment for end-to-end testing."""
    # Create necessary directories
    images_dir = temp_dir / "images"
    images_dir.mkdir(exist_ok=True)
    
    templates_dir = temp_dir / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    static_dir = temp_dir / "static"
    static_dir.mkdir(exist_ok=True)
    
    reports_dir = temp_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    reports_coverage_dir = reports_dir / "coverage"
    reports_coverage_dir.mkdir(exist_ok=True)
    
    # Copy necessary files
    # Copy templates
    project_templates = Path(__file__).parent.parent / "templates"
    if project_templates.exists():
        shutil.copytree(project_templates, templates_dir, dirs_exist_ok=True)
    
    # Copy static assets
    project_static = Path(__file__).parent.parent / "static"
    if project_static.exists():
        shutil.copytree(project_static, static_dir, dirs_exist_ok=True)
    
    # Copy sample image for placeholder
    placeholder_src = Path(__file__).parent / "fixtures" / "sample_image.jpg"
    placeholder_dest = temp_dir / "images" / "placeholder.jpg"
    if placeholder_src.exists():
        shutil.copy(placeholder_src, placeholder_dest)
    
    # Return paths dictionary
    return {
        "root": temp_dir,
        "images": images_dir,
        "templates": templates_dir,
        "static": static_dir,
        "reports": reports_dir,
        "reports_coverage": reports_coverage_dir,
    }
