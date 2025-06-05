# Markdown Local Images

<img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg">
<img alt="Python 3.7+" src="https://img.shields.io/badge/python-3.7+-blue.svg">

A Python utility that downloads remote images from Markdown files and replaces URLs with local references for offline viewing and improved portability.

## Features

* ✅ Processes Markdown files to find all image references (!alt text)
* ✅ Downloads remote images (http, https, ftp) to a local directory
* ✅ Preserves image file extensions from source URLs
* ✅ Intelligently names files based on alt text or URL structure
* ✅ Includes image dimensions in filenames
* ✅ Creates a new Markdown file with updated local image references
* ✅ Preserves local image references without modification

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

```bash
python download_md_images.py /path/to/your/markdown_file.md
```

Example

```bash
python download_md_images.py ./blog-post.md
```

This will:

1. Create a directory blog-post-images/ (based on the first 15 characters of the input filename)
2. Download all remote images referenced in the Markdown
3. Create a new file blog-post-localimg.md with updated image references

## How It Works

The script processes Markdown files using the following workflow:

* Parses the Markdown content looking for image tags (!alt text)
* For each image with a remote URL:
  * Downloads the image
  * Determines its dimensions using Pillow
  * Creates a filename based on alt text (if available) or URL
  * Saves the file to the local image directory
  * Updates the image reference in the document
* Saves a new Markdown file with updated references

## Example Transformation

Before:

```markdown
# My Travel Blog

Check out this amazing sunset!
![Beautiful Sunset](https://example.com/images/sunset.jpg)
```

After:

```markdown
# My Travel Blog

Check out this amazing sunset!
![Beautiful Sunset](my-travel-blog-images/Beautiful_Sunset_1200x800.jpg)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

https://substackcdn.com/image/fetch/w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https://substack-post-media.s3.amazonaws.com/public/images/8f4ebf74-d192-49f2-8abb-d067dabf6fa0_1022x883.png
https://substackcdn.com/image/fetch/w_424,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F8f4ebf74-d192-49f2-8abb-d067dabf6fa0_1022x883.png