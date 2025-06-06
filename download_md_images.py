#!/usr/bin/env python3
# filepath: /Users/admin/Downloads/how to blog post/download_md_images.py

import argparse
import os
import re
import requests
from urllib.parse import urlparse
from PIL import Image
from io import BytesIO
import unicodedata
import string
import sys
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def sanitize_filename(filename):
    """Convert spaces and special chars to make a valid and safe filename"""
    # Replace spaces with underscores and remove invalid filename characters
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    cleaned_name = (
        unicodedata.normalize("NFKD", filename)
        .encode("ASCII", "ignore")
        .decode("ASCII")
    )
    return "".join(c for c in cleaned_name if c in valid_chars).replace(" ", "_")


def get_image_dimensions(image_data):
    """Get image dimensions from binary data"""
    try:
        img = Image.open(BytesIO(image_data))
        return img.size  # Returns (width, height)
    except Exception as e:
        print(f"Warning: Could not determine image dimensions: {e}")
        return (0, 0)  # Default if we can't determine size


def create_session_with_retries():
    """Create a session with retry capabilities"""
    session = requests.Session()

    # Common browser user-agent to avoid being blocked
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    # Setup retries for common failures
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        backoff_factor=1,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(headers)

    return session


def extract_original_image_url(url):
    """Extract the original image URL from a Substack CDN URL"""
    # Check if this is a Substack CDN URL
    if "substackcdn.com/image/fetch" in url:
        # Look for the encoded URL patterns
        encoded_http_pattern = "http%3A%2F%2F"
        encoded_https_pattern = "https%3A%2F%2F"

        # Find where the original URL starts (either encoded or decoded)
        encoded_http_pos = url.find(encoded_http_pattern)
        encoded_https_pos = url.find(encoded_https_pattern)
        http_pos = url.find(
            "http://", 10
        )  # Skip the first http:// in the CDN URL itself
        https_pos = url.find(
            "https://", 10
        )  # Skip the first https:// in the CDN URL itself

        # Get the position of whichever pattern is found first (ignoring -1 values)
        positions = [
            pos
            for pos in [encoded_http_pos, encoded_https_pos, http_pos, https_pos]
            if pos != -1
        ]

        if positions:
            start_pos = min(positions)
            original_url = url[start_pos:]

            # If we found an encoded URL, decode it
            if start_pos == encoded_http_pos or start_pos == encoded_https_pos:
                from urllib.parse import unquote

                original_url = unquote(original_url)

            # Some URLs might have extra parameters, trim those off
            return original_url

        # Alternative: try to split by common patterns in CDN URLs
        for pattern in [
            "/progressive:steep/",
            "/fl_progressive:steep/",
            "/q_auto:good,fl_progressive:steep/",
        ]:
            parts = url.split(pattern, 1)
            if len(parts) == 2:
                original_url = parts[1]
                if "%" in original_url:
                    from urllib.parse import unquote

                    original_url = unquote(original_url)
                return original_url

    # If not a Substack URL or can't extract, return the original
    return url


def download_image(url, save_path, session=None, timeout=30):
    """Download image from URL and return its dimensions"""
    if session is None:
        session = create_session_with_retries()

    original_url = url

    # Handle Substack CDN URLs
    if "substackcdn.com/image/fetch" in url:
        original_url = extract_original_image_url(url)
        print(f"Detected Substack CDN URL. Using original: {original_url}")

    try:
        print(f"Downloading: {original_url}")
        # Use the timeout parameter that was passed in
        response = session.get(original_url, timeout=timeout)

        # If original URL fails, fall back to the CDN URL
        if response.status_code != 200 and original_url != url:
            print(f"Original URL failed, trying CDN URL: {url}")
            response = session.get(url, timeout=timeout)

        response.raise_for_status()

        # Save the image
        with open(save_path, "wb") as f:
            f.write(response.content)

        # Get dimensions
        width, height = get_image_dimensions(response.content)

        # Add a small delay between requests to avoid rate limiting
        time.sleep(0.5)

        return True, (width, height)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {original_url}: {e}")

        # If we tried the original URL and it failed, try the CDN URL as fallback
        if original_url != url:
            try:
                print(f"Trying CDN URL as fallback: {url}")
                response = session.get(url, timeout=timeout)
                response.raise_for_status()

                # Save the image
                with open(save_path, "wb") as f:
                    f.write(response.content)

                # Get dimensions
                width, height = get_image_dimensions(response.content)
                return True, (width, height)
            except Exception as e2:
                print(f"Fallback also failed: {e2}")

        return False, (0, 0)
    except Exception as e:
        print(f"Unexpected error with {original_url}: {e}")
        return False, (0, 0)


def setup_output_directory(file_path):
    """Create output directory for downloaded images"""
    base_name = os.path.basename(file_path)
    file_name_without_ext = os.path.splitext(base_name)[0]
    output_dir_name = f"{file_name_without_ext}-images"

    if not os.path.exists(output_dir_name):
        os.makedirs(output_dir_name)
        print(f"Created directory: {output_dir_name}")

    return output_dir_name


def analyze_markdown_images(content):
    """Find and analyze image references in markdown content"""
    img_pattern = r"!\[(.*?)\]\((.*?)\)"
    image_matches = re.findall(img_pattern, content)
    total_images = len(image_matches)
    remote_images = sum(
        1
        for _, url in image_matches
        if url.startswith(("http://", "https://", "ftp://"))
    )

    print(f"Found {total_images} image references ({remote_images} remote)")
    return img_pattern, image_matches, remote_images


def handle_existing_image(
    local_path, base_filename, file_extension, alt_text, output_dir_name
):
    """Handle case when image file already exists"""
    print(f"File already exists: {os.path.basename(local_path)}")
    try:
        img = Image.open(local_path)
        width, height = img.size
        new_filename = f"{base_filename}_{width}x{height}{file_extension}"
        renamed_path = os.path.join(output_dir_name, new_filename)

        if local_path != renamed_path and not os.path.exists(renamed_path):
            os.rename(local_path, renamed_path)

        return f"![{alt_text}]({output_dir_name}/{new_filename})"
    except Exception:
        # If we can't open the file, just use it as is
        return f"![{alt_text}]({os.path.basename(local_path)})"


import uuid
import os


def get_max_path_length():
    """Get maximum path length for the current OS"""
    try:
        # For Windows
        if os.name == "nt":
            return 260  # Windows MAX_PATH limit
        # For macOS and Linux
        else:
            import pathconf

            return os.pathconf("/", "PC_PATH_MAX")
    except:
        # If we can't determine, use a safe default
        return 255  # A reasonable default for most systems


def get_safe_filename(base_path, base_filename, file_extension):
    """Generate a filename that does not exceed max path length"""
    # Get max path length for current OS
    max_path = get_max_path_length()

    # Calculate full path length
    full_path = os.path.join(base_path, f"{base_filename}{file_extension}")

    # If path is too long, use UUID instead
    if len(full_path) >= max_path:
        # Generate a UUID and use that instead
        uuid_name = str(uuid.uuid4())
        print(f"Original filename too long, using UUID instead: {uuid_name}")
        return uuid_name

    return base_filename


# Then update the process_single_image function to use this:
def process_single_image(
    match, output_dir_name, session, timeout, delay, processed_count, remote_images
):
    """Process a single image reference and download if needed"""
    alt_text = match.group(1)
    image_url = match.group(2).strip()

    # If not a remote URL, return unmodified
    if not (
        image_url.startswith("http://")
        or image_url.startswith("https://")
        or image_url.startswith("ftp://")
    ):
        return match.group(0), None

    processed_count += 1
    print(
        f"Processing image {processed_count}/{remote_images}: {alt_text or 'No alt text'}"
    )

    # Extract file extension from URL
    parsed_url = urlparse(image_url)
    path = parsed_url.path
    file_extension = os.path.splitext(path)[1]
    if not file_extension:
        file_extension = ".jpg"  # Default extension

    # Create a filename from alt text or URL
    if alt_text:
        base_filename = sanitize_filename(alt_text)
    else:
        # Use the last part of the URL path as the filename
        base_filename = sanitize_filename(os.path.basename(parsed_url.path))
        if not base_filename or base_filename == file_extension:
            base_filename = f"image_{hash(image_url) % 10000}"

    # Check if filename would be too long and get a safe filename
    base_filename = get_safe_filename(output_dir_name, base_filename, file_extension)

    # Download the image
    new_filename = f"{base_filename}{file_extension}"
    local_path = os.path.join(output_dir_name, new_filename)

    # Check if we already have this file
    if os.path.exists(local_path):
        return (
            handle_existing_image(
                local_path, base_filename, file_extension, alt_text, output_dir_name
            ),
            None,
        )

    try:
        success, (width, height) = download_image(
            image_url, local_path, session, timeout
        )

        # Respect the delay setting
        time.sleep(delay)

        if success:
            # Add dimensions to filename if we got them
            if width > 0 and height > 0:
                new_filename_with_dims = (
                    f"{base_filename}_{width}x{height}{file_extension}"
                )
                renamed_path = os.path.join(output_dir_name, new_filename_with_dims)

                # Check if the new path with dimensions would be too long
                if len(renamed_path) >= get_max_path_length():
                    # Keep the original filename without dimensions
                    print(
                        f"Path with dimensions too long, keeping original filename: {new_filename}"
                    )
                    return f"![{alt_text}]({output_dir_name}/{new_filename})", None

                os.rename(local_path, renamed_path)
                print(
                    f"Downloaded and saved: {new_filename_with_dims} ({width}x{height})"
                )
                return (
                    f"![{alt_text}]({output_dir_name}/{new_filename_with_dims})",
                    None,
                )
            else:
                print(f"Downloaded and saved: {new_filename}")
                return f"![{alt_text}]({output_dir_name}/{new_filename})", None
        else:
            # Return the original if download failed
            print(f"Failed to download: {image_url}")
            return match.group(0), (alt_text, image_url)
    except KeyboardInterrupt:
        print("\nDownload interrupted by user. Saving progress...")
        # Remove partial download if it exists
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
            except:
                pass
        raise


def process_markdown_file(file_path, timeout=10, delay=0.5):
    """Process markdown file to download remote images and update references"""
    output_dir_name = setup_output_directory(file_path)

    # Read markdown content
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find and analyze all image references
    img_pattern, image_matches, remote_images = analyze_markdown_images(content)

    # Create a single session to use for all downloads
    session = create_session_with_retries()

    processed_count = 0
    failed_downloads = []

    def replace_image(match):
        nonlocal processed_count
        result, failure = process_single_image(
            match,
            output_dir_name,
            session,
            timeout,
            delay,
            processed_count,
            remote_images,
        )

        if failure:
            failed_downloads.append(failure)

        processed_count += 1
        return result

    # Replace all image references
    print("Updating image references...")
    try:
        updated_content = re.sub(img_pattern, replace_image, content)
    except KeyboardInterrupt:
        # Handle keyboard interrupt more gracefully
        print("\nProcess interrupted by user. Saving partial progress...")
        # We'll still continue with the save
        updated_content = content

    # Save the modified markdown
    save_output_file(file_path, updated_content, failed_downloads)

    return output_dir_name


def save_output_file(file_path, updated_content, failed_downloads):
    """Save the updated markdown content to a new file"""
    output_file_path = os.path.splitext(file_path)[0] + "-localimg.md"
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

    # Display summary
    print(f"\nProcessed file saved to: {output_file_path}")

    if failed_downloads:
        print(f"\n{len(failed_downloads)} images failed to download:")
        for alt_text, url in failed_downloads:
            print(f"- {alt_text or 'No alt text'}: {url}")


def main():
    parser = argparse.ArgumentParser(
        description="Download remote images in Markdown files and update references."
    )
    parser.add_argument("file", help="Path to the Markdown file to process")
    parser.add_argument(
        "--timeout", type=int, default=30, help="Timeout for image downloads in seconds"
    )
    parser.add_argument(
        "--delay", type=float, default=1.0, help="Delay between downloads in seconds"
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Skip downloading images, just update references to existing files",
    )
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found.")
        sys.exit(1)

    try:
        process_markdown_file(args.file, timeout=args.timeout, delay=args.delay)
        print("Process completed successfully.")
    except KeyboardInterrupt:
        print("\nProcess terminated by user.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
