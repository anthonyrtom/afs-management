import csv
from django.http import HttpResponse
from datetime import datetime


def construct_client_dict(final_dict=None, client_fy_obj=None):
    """
    a function to help construct a dictionary, it receives an antry type which
    can be accounting, secretarial, taxation or invoicing
    final_dict is the dictionary that will be returned after adding the dictionary
    to be constructed in this procedure
    client_fy_obj is an instance of ClientFinancialYear module
    """
    if not client_fy_obj:
        raise TypeError("client_fy_obj can not be None")
    if not isinstance(final_dict, dict):
        raise TypeError("Wrong object passed, final_dict must be a dictionary")

    fin_finished = tax_finished = sec_finished = invoicing_finished = "Incomplete"
    fin_days = tax_days = sec_days = invoicing_days = 0
    data_dict = {}
    today = datetime.now().date()
    data_dict["fy"] = client_fy_obj.financial_year.the_year
    data_dict["name"] = client_fy_obj.client.get_client_full_name()
    data_dict["client_id"] = client_fy_obj.client.id

    if client_fy_obj.schedule_date and client_fy_obj.finish_date:
        fin_finished = "Completed"
        fin_days = (client_fy_obj.finish_date -
                    client_fy_obj.schedule_date).days
    elif client_fy_obj.schedule_date and not client_fy_obj.finish_date:
        fin_days = (today - client_fy_obj.schedule_date).days

    if client_fy_obj.secretarial_start_date and client_fy_obj.secretarial_finish_date:
        sec_finished = "Completed"
        sec_days = (client_fy_obj.secretarial_finish_date -
                    client_fy_obj.secretarial_start_date).days
    elif client_fy_obj.secretarial_start_date and not client_fy_obj.secretarial_finish_date:
        sec_days = (today - client_fy_obj.secretarial_start_date).days
    elif client_fy_obj.finish_date and not client_fy_obj.secretarial_finish_date:
        sec_days = (today - client_fy_obj.finish_date).days

    if client_fy_obj.itr14_start_date and client_fy_obj.itr14_date:
        tax_finished = "Completed"
        tax_days = (client_fy_obj.itr14_date -
                    client_fy_obj.itr14_start_date).days
    elif client_fy_obj.itr14_start_date and not client_fy_obj.itr14_date:
        tax_days = (today - client_fy_obj.itr14_start_date).days
    elif client_fy_obj.secretarial_finish_date and not client_fy_obj.itr14_date:
        tax_days = (today - client_fy_obj.secretarial_finish_date).days
    # invoicing below
    if client_fy_obj.invoice_date and client_fy_obj.itr14_date:
        invoicing_finished = "Completed"
        invoicing_days = (client_fy_obj.invoice_date -
                          client_fy_obj.itr14_date).days
    elif client_fy_obj.itr14_date and not client_fy_obj.invoice_date:
        invoicing_days = (today - client_fy_obj.itr14_date).days

    data_dict["fin_days"] = fin_days
    data_dict["fin_finished"] = fin_finished
    data_dict["sec_days"] = sec_days
    data_dict["sec_finished"] = sec_finished
    data_dict["tax_days"] = tax_days
    data_dict["tax_finished"] = tax_finished
    data_dict["invoicing_days"] = invoicing_days
    data_dict["invoicing_finished"] = invoicing_finished
    final_dict[client_fy_obj.id] = data_dict
    return final_dict


def calculate_unique_days_from_dict(key_type, client_fy_dict):
    """
    Returns a list of unique day values for the specified key_type from the dictionary.

    Args:
        key_type (str): The day field to extract ("fin_days", "sec_days", etc.)
        client_fy_dict (dict): Dictionary from construct_client_dict

    Returns:
        list: Unique day values
    """
    if not isinstance(key_type, str):
        raise TypeError("key_type must be a string")
    if not client_fy_dict:
        raise TypeError("client_fy_dict cannot be None")
    if not isinstance(client_fy_dict, dict):
        raise TypeError("client_fy_dict should be a dict")

    valid_keys = {"fin_days", "sec_days", "tax_days",
                  "invoicing_days"}  # Add all valid keys
    if key_type not in valid_keys:
        raise ValueError(f"key_type must be one of {valid_keys}")

    unique_days = set()

    for client_data in client_fy_dict.values():  # We only need the nested dicts
        if key_type in client_data:
            unique_days.add(client_data[key_type])
    sorted_days = sorted(unique_days, reverse=True)
    return sorted_days


def calculate_max_days_from_dict(client_fy_dict):
    """
    Returns a max of day values for the specified key_type from the dictionary.

    Args:
        key_type (str): The day field to extract ("fin_days", "sec_days", etc.)
        client_fy_dict (dict): Dictionary from construct_client_dict

    Returns:
        list: an int
    """
    if not client_fy_dict:
        raise TypeError("client_fy_dict cannot be None")
    if not isinstance(client_fy_dict, dict):
        raise TypeError("client_fy_dict should be a dict")

    valid_keys = {"fin_days", "sec_days", "tax_days", "invoicing_days"}
    final_dict = {}

    for key_type in valid_keys:
        all_values = [client_data[key_type]
                      for client_data in client_fy_dict.values()]
        final_dict[key_type] = max(all_values) if all_values else 0

    return final_dict


def get_client_model_fields():
    """
    Helper function to get the field list of the Client model in a list
    Args:
    None
    Returns:
        A list of all the fields except ManyToMany fields
    """
    all_list = ["name", "surname", "email", "cell_number", "contact_person", "contact_person_cell", "month_end", "is_active", "is_sa_resident", "last_day", "income_tax_number", "paye_reg_number",
                "first_month_for_paye_sub", "uif_reg_number", "entity_reg_number", "birthday_of_entity", "vat_reg_number", "first_month_for_vat_sub", "vat_category", "registered_address", "coida_reg_number", "first_month_for_coida_sub", "internal_id_number", "uif_dept_reg_number", "accountant", "first_financial_year", "client_type"]

    return all_list


def export_to_csv(filename, headers, rows):
    """
    Exports data to a CSV file.

    :param filename: The CSV file name (string)
    :param headers: A list of column names
    :param rows: A list of lists/tuples containing row data
    :return: HttpResponse with CSV content
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(headers)

    for row in rows:
        writer.writerow(row)

    return response
