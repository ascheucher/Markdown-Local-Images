#!/usr/bin/env python3
# filepath: download_md_images.py

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


def download_image(url, save_path):
    """Download image from URL and return its dimensions"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Save the image
        with open(save_path, "wb") as f:
            f.write(response.content)

        # Get dimensions
        width, height = get_image_dimensions(response.content)

        return True, (width, height)
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False, (0, 0)


def process_markdown_file(file_path):
    """Process markdown file to download remote images and update references"""
    # Create output directory name based on first 15 chars of input file
    base_name = os.path.basename(file_path)
    file_name_without_ext = os.path.splitext(base_name)[0]
    output_dir_name = f"{file_name_without_ext[:15]}-images"

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir_name):
        os.makedirs(output_dir_name)
        print(f"Created directory: {output_dir_name}")

    # Read markdown content
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all image references using regex
    img_pattern = r"!\[(.*?)\]\((.*?)\)"

    def replace_image(match):
        alt_text = match.group(1)
        image_url = match.group(2).strip()

        # If not a remote URL, return unmodified
        if not (
            image_url.startswith("http://")
            or image_url.startswith("https://")
            or image_url.startswith("ftp://")
        ):
            return match.group(0)

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

        # Download the image
        new_filename = f"{base_filename}{file_extension}"
        local_path = os.path.join(output_dir_name, new_filename)

        success, (width, height) = download_image(image_url, local_path)

        if success:
            # Add dimensions to filename if we got them
            if width > 0 and height > 0:
                new_filename = f"{base_filename}_{width}x{height}{file_extension}"
                renamed_path = os.path.join(output_dir_name, new_filename)
                os.rename(local_path, renamed_path)
                print(f"Downloaded and saved: {new_filename} ({width}x{height})")
                return f"![{alt_text}]({output_dir_name}/{new_filename})"
            else:
                print(f"Downloaded and saved: {new_filename}")
                return f"![{alt_text}]({output_dir_name}/{new_filename})"
        else:
            # Return the original if download failed
            print(f"Failed to download: {image_url}")
            return match.group(0)

    # Replace all image references
    updated_content = re.sub(img_pattern, replace_image, content)

    # Save the modified markdown
    output_file_path = os.path.splitext(file_path)[0] + "-localimg.md"
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"Processed file saved to: {output_file_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Download remote images in Markdown files and update references."
    )
    parser.add_argument("file", help="Path to the Markdown file to process")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found.")
        sys.exit(1)

    process_markdown_file(args.file)


if __name__ == "__main__":
    main()
