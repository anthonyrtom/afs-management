import csv
from django.core.management.base import BaseCommand
from client.models import Client


class Command(BaseCommand):
    help = 'Export all clients to a CSV file with name and client code'

    def handle(self, *args, **kwargs):
        csv_file_path = 'clients_export.csv'

        try:
            with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'internal_id_number']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()

                clients = Client.objects.all()
                for client in clients:
                    writer.writerow({
                        'name': client.name,
                        'internal_id_number': client.internal_id_number or ''
                    })

                self.stdout.write(self.style.SUCCESS(
                    f'Clients exported successfully to {csv_file_path}!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Error exporting clients: {e}'))
