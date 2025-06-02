from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
import requests
from main.models import Vehicle, Driver

class Command(BaseCommand):
    help = 'Update existing vehicles and drivers with photos'

    def download_image(self, url, filename):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return ContentFile(response.content, name=filename)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not download image from {url}: {e}'))
        return None

    def handle(self, *args, **kwargs):
        vehicle_images = [
            'https://assets.avtocod.ru/storage/images/articles/rwWVEXc11wFn0SHxJ0bgRWMYWCJVUbrh4rHhVfvg.jpg',
            'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSH8diuIxt40O5WXhspplAqhRM85gLfz-fc4w&s',
            'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQEsrC39dvLNRKluEznQoiKgWtP2XtibbX3sw&s'
        ]

        driver_images = [
            'https://topgir.com.ua/wp-content/uploads/2022/05/taxi-self-auto-1.jpg',
            'https://public.superjob.ru/images/profi_articles/image/5411_a86cdc40742c377503228e80345bea46.jpg',
            'https://cdn-trans.info/uploads/2021/06/8a6572462d17afc3c3b0b8fe7d2.jpg'
        ]

        vehicles = Vehicle.objects.all()
        for i, vehicle in enumerate(vehicles):
            image_url = vehicle_images[i % len(vehicle_images)]
            image_content = self.download_image(image_url, f'vehicle_{i+1}.jpg')
            if image_content:
                vehicle.image.save(f'vehicle_{i+1}.jpg', image_content, save=True)
                self.stdout.write(self.style.SUCCESS(f'Updated vehicle {vehicle} with image'))

        drivers = Driver.objects.all()
        for i, driver in enumerate(drivers):
            image_url = driver_images[i % len(driver_images)]
            image_content = self.download_image(image_url, f'driver_{i+1}.jpg')
            if image_content:
                driver.photo.save(f'driver_{i+1}.jpg', image_content, save=True)
                self.stdout.write(self.style.SUCCESS(f'Updated driver {driver} with photo')) 