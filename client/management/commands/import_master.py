import csv
from django.core.management.base import BaseCommand
from client.models import Client, ClientType, Month, VatCategory, FinancialYear, CustomUser


class Command(BaseCommand):
    help = 'Import clients from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file']

        try:
            with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                # manual_file = open("check.txt", "w", newline="\n")
                for row in reader:
                    try:
                        vat_number = row.get('vat_reg_number')
                        vat_number = vat_number if vat_number else None
                        income_tax_number = row.get('income_tax_number')
                        income_tax_number = income_tax_number if income_tax_number else None
                        paye_reg_number = row.get('paye_reg_number')
                        paye_reg_number = paye_reg_number if paye_reg_number else None

                        client_data = {
                            'name': row['name'],  # Name is compulsory
                            'surname': row.get('surname'),
                            'email': row.get('email'),
                            'cell_number': row.get('cell_number'),
                            'contact_person': row.get('contact_person'),
                            'contact_person_cell': row.get('contact_person_cell'),
                            'month_end': row.get('month_end', 2),
                            'last_day': row.get('last_day', 28),
                            'income_tax_number': income_tax_number,
                            'paye_reg_number': paye_reg_number,
                            'uif_reg_number': row.get('uif_reg_number', None),
                            'entity_reg_number': row.get('entity_reg_number', None),
                            'vat_reg_number': vat_number,
                            'registered_address': row.get('registered_address', None),
                            'coida_reg_number': row.get('coida_reg_number', None),
                            'internal_id_number': row.get('internal_id_number', None),
                            'uif_dept_reg_number': row.get('uif_dept_reg_number', None),
                            'is_active': row.get('is_active', False),
                            'is_sa_resident': row.get('is_sa_resident', True),
                            'first_financial_year': row.get('first_financial_year', None),
                        }

                        # Handle foreign keys only if the value exists
                        if row.get('client_type'):
                            client_data['client_type'] = ClientType.objects.filter(
                                name=row['client_type']).first()
                        if row.get('first_month_for_paye_sub'):
                            client_data['first_month_for_paye_sub'] = Month.objects.filter(
                                name=row['first_month_for_paye_sub']).first()
                        if row.get('first_month_for_vat_sub'):
                            client_data['first_month_for_vat_sub'] = Month.objects.filter(
                                name=row['first_month_for_vat_sub']).first()
                        if row.get('vat_category'):
                            client_data['vat_category'] = VatCategory.objects.filter(
                                vat_category=row['vat_category']).first()
                        if row.get('first_financial_year'):
                            year_value = row['first_financial_year'].strip()
                            try:
                                year_value = int(year_value)
                                if year_value:
                                    financial_year, _ = FinancialYear.objects.get_or_create(
                                        the_year=year_value)
                                client_data['first_financial_year'] = financial_year
                            except:
                                client_data['first_financial_year'] = None
                        else:
                            client_data['first_financial_year'] = None
                        if row.get('accountant'):
                            client_data['accountant'] = CustomUser.objects.filter(
                                username=row['accountant']).first()

                        client, created = Client.objects.update_or_create(
                            name=row['name'],
                            defaults=client_data
                        )

                        status = 'created' if created else 'updated'
                        self.stdout.write(self.style.SUCCESS(
                            f'Client {client.name} {status} successfully!'))
                        # manual_file.write(client.name)
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f'Error importing client {row.get("name")}: {e}'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                f'File not found: {csv_file_path}'))
