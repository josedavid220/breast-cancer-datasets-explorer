import gradio as gr
import os
from PIL import Image, ImageDraw, ImageFont
import tifffile
import tempfile
import pandas as pd

# Paths
BASE_DIR = "data/DMID"
TIFF_DIR = os.path.join(BASE_DIR, "tiff-images")
ANNOT_DIR = os.path.join(BASE_DIR, "pixel-level-annotations")
ROI_DIR = os.path.join(BASE_DIR, "roi-masks")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
METADATA_PATH = os.path.join(BASE_DIR, "metadata.txt")

# Get image numbers
def get_image_numbers():
    files = [f for f in os.listdir(TIFF_DIR) if f.startswith("IMG") and f.endswith(".tif")]
    numbers = sorted([int(f[3:6]) for f in files])
    return numbers

IMAGE_NUMBERS = get_image_numbers()
TOTAL_IMAGES = len(IMAGE_NUMBERS)

# Parse Info.txt for metadata
def parse_info_txt():
    df = pd.read_csv(METADATA_PATH, sep=",", header=0, index_col=0)
    return df

METADATA = parse_info_txt()

# Load report
def load_report(image_number):
    report_path = os.path.join(REPORTS_DIR, f"Img{image_number:03d}.txt")
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            return f.read()
    return "No report available."

# Load metadata
def load_metadata(image_number):
    img_name = f"IMG{image_number:03d}"
    result = METADATA.loc[img_name]
    if isinstance(result, pd.Series):
        return result.to_frame().T
    else:
        return result
    
def convert_tiff_to_jpeg(tiff_path):
    try:
        img_array = tifffile.imread(tiff_path)
        temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        # Handle different array shapes (grayscale, RGB, etc.)
        if img_array.ndim == 2: # Grayscale
            img = Image.fromarray(img_array).convert("L") # Convert to 8-bit grayscale
        elif img_array.ndim == 3: # Color image
            if img_array.shape[2] == 3: # RGB
                img = Image.fromarray(img_array).convert("RGB")
            elif img_array.shape[2] == 4: # RGBA
                img = Image.fromarray(img_array).convert("RGBA")
                # If you want to save RGBA as JPG, you'll need to flatten it to RGB
                # JPG doesn't support alpha channel. You might lose transparency.
                img = img.convert("RGB")
            else:
                return f"Unsupported number of channels in TIFF: {img_array.shape[2]}"
        else:
            return f"Unsupported TIFF image dimensions: {img_array.ndim}"

        img.save(temp_file.name, "JPEG")
        return temp_file.name
    
    except (OSError, IOError) as e:
        print(f"Warning: Could not convert {tiff_path} to JPEG: {e}")
        return None

def create_placeholder_image(text="No image available", size=(256, 256)):
    img = Image.new("RGB", size, color=(200, 200, 200))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    text_width, text_height = 128, 128
    position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
    draw.text(position, text, fill=(50, 50, 50), font=font)
    temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    img.save(temp_file.name, "JPEG")
    return temp_file.name

def load_images(image_number):
    img_name = f"IMG{image_number:03d}.tif"
    tiff_path = os.path.join(TIFF_DIR, img_name)
    annot_path = os.path.join(ANNOT_DIR, img_name)
    roi_path = os.path.join(ROI_DIR, img_name)
    # Convert TIFF to JPEG for Gradio, or use placeholder if missing
    if os.path.exists(tiff_path):
        tiff_jpeg_path = convert_tiff_to_jpeg(tiff_path)
    else:
        tiff_jpeg_path = create_placeholder_image()
        
    if os.path.exists(annot_path):
        annot_jpeg_path = convert_tiff_to_jpeg(annot_path)
    else:
        annot_jpeg_path = create_placeholder_image()
        
    if os.path.exists(roi_path):
        roi_jpeg_path = convert_tiff_to_jpeg(roi_path)
    else:
        roi_jpeg_path = create_placeholder_image()
    print(f"Loaded images for {img_name}: TIFF={tiff_jpeg_path}, Annotation={annot_jpeg_path}, ROI={roi_jpeg_path}")
    return tiff_jpeg_path, annot_jpeg_path, roi_jpeg_path

def format_metadata(metadata):
    return metadata

# Main update function
def update_display(idx):
    image_number = IMAGE_NUMBERS[idx]
    tiff_path, annot_path, roi_path = load_images(image_number)
    metadata = load_metadata(image_number)
    report = load_report(image_number)
    return (
        gr.update(value=tiff_path),
        gr.update(value=annot_path),
        gr.update(value=roi_path),
        gr.update(value=format_metadata(metadata)),
        gr.update(value=report),
        gr.update(value=idx)
    )

with gr.Blocks() as demo:
    gr.Markdown("# Digital Mammography Dataset (DMID) Explorer")

    idx_state = gr.Number(value=0, label="Image Index", visible=False)
    
    with gr.Row():
        prev_btn = gr.Button("⬅️")
        next_btn = gr.Button("➡️")
        
    with gr.Row():
        metadata_box = gr.DataFrame(
            label="Metadata",
            wrap=True,
            show_row_numbers=True,
        )
            
    with gr.Row():
        with gr.Column():
            tiff_img = gr.Image(label="TIFF Image", show_label=True, interactive=False, type="filepath")
        with gr.Column():
            annot_img = gr.Image(label="Pixel-level Annotation", show_label=True, interactive=False, type="filepath")
        with gr.Column():
            roi_img = gr.Image(label="ROI Mask", show_label=True, interactive=False, type="filepath")
            
    with gr.Row():
        with gr.Column():
            report_box = gr.Textbox(label="Report", autoscroll=False, lines=15, interactive=True)

    # Loading indicators
    loading = gr.Textbox(value="", visible=False)
    
    def on_next(idx):
        new_idx = min(TOTAL_IMAGES - 1, idx + 1)
        return update_display(new_idx)
    
    def on_prev(idx):
        new_idx = max(0, idx - 1)
        return update_display(new_idx)

    prev_btn.click(on_prev, inputs=[idx_state], outputs=[tiff_img, annot_img, roi_img, metadata_box, report_box, idx_state])
    next_btn.click(on_next, inputs=[idx_state], outputs=[tiff_img, annot_img, roi_img, metadata_box, report_box, idx_state])

    # Initial load
    demo.load(lambda: update_display(0), [], [tiff_img, annot_img, roi_img, metadata_box, report_box, idx_state])

if __name__ == "__main__":
    demo.launch()