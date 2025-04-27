import rawpy
import imageio
import os

input_folder = r'P:\Film\Film Scanning\Raw' #change to your path
output_folder = r'P:\Film\Film Scanning\JPEG' #change to your path
os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if filename.lower().endswith('.nef'):
        input_path = os.path.join(input_folder, filename)
        with rawpy.imread(input_path) as raw:
            rgb = raw.postprocess()
        # Replace the .nef extension with .jpg
        output_filename = os.path.splitext(filename)[0] + '.jpg'
        output_path = os.path.join(output_folder, output_filename)
        imageio.imwrite(output_path, rgb)
        print(f"Converted {filename} to JPEG")
