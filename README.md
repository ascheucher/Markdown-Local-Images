# Markdown Local Images

<img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg">&nbsp;<img alt="Python 3.7+" src="https://img.shields.io/badge/python-3.7+-blue.svg">

A Python utility that downloads remote images from Markdown files and replaces
URLs with local references for offline viewing and improved portability.

Folder and File names are optimized to work in **Obsidian**.

## Features

* ✅ Processes Markdown files to find all image references (`![alt text](url)`)
* ✅ Downloads remote images (http, https, ftp) to a local directory
* ✅ Preserves image file extensions from source URLs
* ✅ Intelligently names files based on alt text or URL structure
* ✅ Includes image dimensions in filenames
* ✅ Creates a new Markdown file with updated local image references
* ✅ Preserves local image references without modification
* ✅ Special handling for Substack CDN URLs
* ✅ Smart fallback to UUID filenames when paths are too long
* ✅ Resilient downloading with retries and fallbacks

## Installation

Prerequisites:

* Python 3.7 or higher
* pip or uv package manager
  
Setup with traditional pip

```bash
# Clone the repository (or download the script)
git clone https://github.com/yourusername/markdown-image-downloader.git
cd markdown-image-downloader

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install requests Pillow
```

Setup with uv (faster alternative)

```bash
# Install uv if you don't have it
pip install uv

# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install dependencies
uv pip install requests Pillow
```

## Usage

Basic usage:

```bash
python download_md_images.py /path/to/your/markdown_file.md
```

Advanced options:

```bash
# Set a longer timeout for large images
python download_md_images.py ./blog-post.md --timeout 60

# Add a longer delay between downloads to avoid rate limiting
python download_md_images.py ./blog-post.md --delay 2
```

## How It Works

The script processes Markdown files using the following workflow:

1. Creates an output directory with the same name as the input file (without extension)
2. Parses the Markdown content looking for image tags (`![alt text](url)`)
3. For each image with a remote URL:
   * Downloads the image with automatic retries
   * For Substack CDN URLs, extracts and downloads from the original source
   * Determines image dimensions using Pillow
   * Creates a filename with the first 20 characters of the markdown filename as prefix
   * Adds image dimensions to filenames (e.g., `prefix_image_800x600.jpg`)
   * Uses UUIDs for filenames that would exceed system path length limits
   * Saves the file to the output directory
4. Creates a new copy of the Markdown file in the output directory with updated image references

## Example Transformation

Before:

```markdown
# My Travel Blog

Check out this amazing sunset!
![Beautiful Sunset](https://example.com/images/sunset.jpg)
```

After (in the `my-travel-blog` directory):

```markdown
# My Travel Blog

Check out this amazing sunset!
![Beautiful Sunset](my-travel-blog_Beautiful_Sunset_1200x800.jpg)
```

## File Structure

For an input file named `blog-post.md`, the script creates:

```bash
blog-post/                         # Output directory
├── blog-post.md                   # Copy of markdown with updated references
├── blog-post_image1_800x600.jpg   # Downloaded images with prefixes
└── blog-post_image2_1200x800.jpg  # and dimensions in filenames
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
