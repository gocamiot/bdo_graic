from django.utils import timezone
from datetime import datetime


def calculate_contract_value(request):
    annual_contract = request.POST.get('Total_Contract_Value_Annual_Excluding_VAT')
    try:
        return round(int(annual_contract) / 12, 2)
    except:
        return 0


def calculate_remaining_days(request):
    current_time = timezone.now()
    end_date_str = request.POST.get('End_Date')

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M').replace(tzinfo=timezone.get_current_timezone())
            remaining_days = (end_date - current_time).days

            if remaining_days >= 0:
                return remaining_days
            else:
                return 0 
        except ValueError:
            return 0 
    else:
        return 0 
