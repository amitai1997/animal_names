"""
Test for the fix to handle root-relative URLs in the downloader module.
"""

from unittest import mock

import pytest
import requests

from src.downloader import extract_image_url


@mock.patch("src.downloader.get_session")
def test_extract_image_url_root_relative(mock_get_session):
    """Test extracting root-relative URLs from Wikipedia pages."""
    # Setup mock response with root-relative URL in infobox
    mock_response = mock.Mock()
    mock_response.text = """
    <html>
        <body>
            <table class="infobox">
                <tr>
                    <td><img src="/static/images/icons/wikipedia.png" alt="Wikipedia Icon"></td>
                </tr>
            </table>
        </body>
    </html>
    """
    mock_response.raise_for_status = mock.Mock()

    # Setup mock session
    mock_session = mock.Mock()
    mock_session.get.return_value = mock_response
    mock_get_session.return_value = mock_session

    # Test root-relative URL conversion
    result = extract_image_url("https://en.wikipedia.org/wiki/Test")
    assert result == "https://en.wikipedia.org/static/images/icons/wikipedia.png"

    # Test with a different domain
    result = extract_image_url("https://example.com/wiki/Test")
    assert result == "https://example.com/static/images/icons/wikipedia.png"
