import os
from PIL import Image, ImageFile, ImageOps
ImageFile.LOAD_TRUNCATED_IMAGES = True


class PdfCreator:
    def create(self, input_dir: str, output_dir: str, params: dict = {}) -> str:
        default_params = {
            'name': 'output.pdf',
            'resize': True,
            'width': 1080,
        }
        params = {**default_params, **params}

        # Get list of images
        try:
            images = (Image.open(f'{input_dir}/{name}')
                      for name in os.listdir(input_dir))
        except:
            return False

        # Sort images in alphabetical order
        images = list(sorted(images, key=lambda img: img.filename))

        # Rotate images to correct orientation
        images = list(map(ImageOps.exif_transpose, images))

        # Resize images
        if params['resize']:
            images = list(map(lambda img: self.resize_by_width(
                img, params['width']), images))

        # Create and save pdf
        save_path = os.path.join(output_dir, params['name'])
        images[0].save(
            save_path, "PDF" ,resolution=100.0, 
            save_all=True, append_images=images[1:]
        )

        return save_path

    def resize_by_width(self, image: Image, new_width: int) -> Image:
        """Proportionally resize the photo for a given width"""

        width, height = image.size
        new_height = int(new_width * height / width)
        return image.resize((new_width, new_height))
