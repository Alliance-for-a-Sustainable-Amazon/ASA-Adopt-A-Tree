from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw

class Command(BaseCommand):
    help = "Test Pillow rounded corner rendering"

    def handle(self, *args, **kwargs):
        WIDTH = 667
        HEIGHT = 1000

        for radius in [10, 50, 100, 200, 300]:
            image = Image.new("RGBA", (WIDTH, HEIGHT), "green")

            mask = Image.new("L", image.size, 0)
            draw = ImageDraw.Draw(mask)

            draw.rounded_rectangle(
                [(0, 0), (WIDTH, HEIGHT)],
                radius=radius,
                fill=255
            )

            image.putalpha(mask)

            filename = f"rounded_{radius}.png"
            image.save(filename)

            self.stdout.write(f"Saved {filename}")

        self.stdout.write(self.style.SUCCESS("Done"))