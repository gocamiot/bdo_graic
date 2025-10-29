import datetime
import json
from django import template
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from loader.models import decrypt_value
from apps.tables.models import DependentDropdown
from django.conf import settings
from django.urls import get_resolver
from urllib.parse import quote


register = template.Library()

map_field_names = getattr(settings, 'MAP_FIELD_NAMES')
reverse_map_field_names = {v: k for k, v in map_field_names.items()}

DATE_FIELDS = ['ImportDate', 'DeviceLastConnUtc', 'Import_date', 'Device_LastConnUtc', 'ReleaseDate', 'EndofSupportDate', 'Start_Date', 'End_Date', 'Audit_Date', 'Last_Approval_Date', 'DataAge', 'Created_in_AD', 'Last_AD_Logon', 'Last_Network_ping', 'AD_Account_Created', 'Password_Last_Set', 'Purchase_Date', 'Warranty_Exiry_Date', 'Start_time', 'End_time', 'Last_Scan', 'Last_Successful_Scan', 'Last_Boot_Time', 'Last_Patched_Time', 'Last_Contact_Time', 'Last_Contacted_Time_with_DS', 'Last_Success_or_Warning', 'Last_Startup', 'Last_Shutdown', 'Agent_Installation', 'Agent_Upgrade', 'Hotfix', 'Last_Firewall_Count_Sent', 'Last_Virus_Scan_Manual', 'Last_Virus_Detection_Real_time', 'Last_Virus_Scan_Scheduled', 'Last_Virus_Scan_Scan_Now', 'Last_Spyware_Scan_Manual', 'Last_Spyware_Detection_Real_time', 'Last_Spyware_Scan_Scheduled', 'Last_Spyware_Scan_Scan_Now', 'Deployed_Date', 'Agent_Responded_Time', 'Created_Time_Ticket', 'Customer_Responded_Time', 'Modified_Time_Ticket', 'Ticket_Closed_Time', 'Software_Detected_Time', 'Software_Installed_Date', 'Last_Successful_Asset_Scan', 'Last_Contact_Time', 'Shipping_Date', 'Warranty_Expiry_Date', 'Last_Asset_Scan_Time', 'Last_Boot_Time', 'Agent_Installed_Date', 'OS_Installed_Date', 'Date_of_birth', 'Date_engaged', 'start_date', 'end_date', 'opened_at', 'sys_updated_on', 'Date_Joined_Group', 'Termination_Date', 'Device_Last_Seen', 'Date_Joined_Group', 'Termination_Date', 'lastLogon', 'pwdLastSet', 'lastLogonTimestamp', 'Last_Logon', 'whenCreated', 'Warranty_Exp_Date', 'Ship_Date', 'Last_dirsync_time', 'Last_password_change_time_stamp', 'Soft_deletion_time_stamp', 'When_created', 'Sensor_last_connected', 'Agent_last_connected', 'Last_scanned', 'Component_update_change', 'AD_LastLogonTimeStamp', 'SCCM_LastSoftwareScan', 'ITSM_ModifiedDate', '_1e_LastSeen', '_1e_LastBootUtc', 'Date', 'DATE', 'VPN_Last_Used', 'Servicenow_Last_Used', 'SAP_Last_Used', 'Financial_system_Last_Used', 'SPLUNK_Last_Used', 'HR_Last_Used', 'Payroll_Last_Used', 'Start_time', 'Last_Password_Change_For_Policy', 'Modified_Date', 'Submit_Date', 'Last_Resolved_Date', 'Target_Date', 'Start_date_', 'Renewal_date_', 'Create_Date', 'Time_Of_Release', 'Time', 'Completed_Time', 'Created_Time', 'DueBy_Time', 'Last_Update_Time', 'Resolved_Time', 'Responded_Date', 'User_Updated', 'Date_Engaged', 'Date_Joined', 'Termination_Date', 'Target_Date', 'Actual_End_Date', 'Actual_Start_Date', 'Completed_Date', 'Earliest_Start_Date', 'End_Time', 'Last_Modified_Date', 'Requested_End_Date', 'Requested_Start_Date', 'Scheduled_End_Date', 'Scheduled_Start_Date', 'Submit_Date', 'Start_date', 'Renewal_date', 'osinstalldate', 'scantime', 'install_date', 'Used', 'AccountExpirationDate', 'accountExpires', 'AccountLockoutTime', 'Created', 'createTimeStamp', 'LastBadPasswordAttempt', 'LastLogonDate', 'Modified', 'modifyTimeStamp', 'PasswordLastSet', 'whenChanged', 'Next_Review_Schedule', 'Scheduled_End', 'Scheduled_Start_Time', 'Time_Spent_End_Date', 'Time_Spent_Start_Date', 'LastlogonDate', 'Last_Start_time', 'Last_Created_Time', 'Termination_Date_X', 'LastFullScanDateTime', 'LastQuickScanDateTime', 'LastReportedDateTime', 'Valid_From', 'Valid_To', 'Modification_date', 'Date', 'Start_Date', 'Leaving', 'Modification_date', 'Creation_Date', 'FROM_DAT', 'TO_DAT_EXCLU', 'DECHANGE_DATCHANGE_T', 'Start_date_of_Transfer_Promotion', 'Last_Login', 'Date_Engaged_Converted', 'Contract_End_Date_Converted', 'Date_UTC', 'd_Date_Engaged_Converted', 'd_Contract_End_Date_Converted', 'd_d_Contract_End_Date_Converted', 'd_d_Date_Engaged_Converted', 'Date_Created', 'Close_date', 'Created_on', 'Last_Updated_on', 'd_Date_Created', 'PspdpuLastModifiedTimeUtc', 'Last_checkin', 'First_Seen', 'Last_device_update', 'Enrollment_date', 'Last_EAS_sync_time', 'Compliance_grace_period_expiration', 'Management_certificate_expiration_date', 'Last_modified', 'Quick_scan_time', 'Full_scan_time', 'Last_seen', 'Data_refresh_timestamp', 'Engine_update_time', 'Signature_update_time', 'Platform_update_time', 'Security_intel_publish_time', 'Signature_refresh_time', 'WhenCreated', 'd_LastLogonDate', 'd_PasswordLastSet', 'd_WhenCreated', 'd_Created_on', 'd_Close_date', 'd_Last_Updated_on', 'd_Termination_Date', 'd_PspdpuLastModifiedTimeUtc', 'd_First_Seen', 'd_Last_device_update', 'd_Compliance_grace_period_expiration', 'd_Management_certificate_expiration_date', 'd_Last_EAS_sync_time', 'd_Signature_update_time', 'd_Platform_update_time', 'd_Last_seen', 'd_Quick_scan_time', 'd_Data_refresh_timestamp', 'd_Engine_update_time', 'd_Security_intel_publish_time', 'd_Signature_refresh_time', 'd_Full_scan_time', 'Termination_date', 'Group_Join_Date', 'Employment_Date', 'next_target_date', 'Reported_Date', 'Responed_Date', 'Closed_Date', 'Date_added', 'd_Termination_date', 'd_Start_Date', 'd_Employment_Date', 'd_Group_Join_Date', 'Termination_Date_no_text', 'Converted_pwdLastSet', 'lockoutTime', 'ConvertedlockoutTime', 'LastLogonTimeStamp', 'ConvertedLastLogonTimeStamp', 'd_Created', 'd_Converted_pwdLastSet', 'd_pwdLastSet', 'd_lockoutTime', 'd_ConvertedlockoutTime', 'd_Last_checkin', 'd_Submit_Date', 'd_Target_Date', 'Join_Date', 'Modified_By_Ticket']

def format_timestamp(timestamp, is_edit=False):
    if timestamp < 0:
        custom_epoch = datetime.datetime(1970, 1, 1)
        date_object = custom_epoch + datetime.timedelta(seconds=timestamp)
    else:
        date_object = datetime.datetime.fromtimestamp(timestamp)
    
    if is_edit:
        return date_object.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return date_object.strftime('%b %d %Y %H:%M%p')

@register.filter(name="map_fields")
def map_fields(field):
    return reverse_map_field_names[field]

@register.filter(name="getattribute")
def getattribute(value, arg):
    if arg in reverse_map_field_names:
        arg = reverse_map_field_names[arg]

    if not hasattr(value, 'dynamic_fields') and arg == "similarity":
        return None

    if isinstance(value, dict):
        val = value[arg]
    elif hasattr(value, 'dynamic_fields') and arg in value.dynamic_fields:
        if arg == 'similarity':
            val = (1 - float(value.dynamic_fields[arg]))
            val = f"{round(val * 100, 1)}%"
        else:
            val = value.dynamic_fields[arg]
    else:
        val = getattr(value, arg)

    if arg in DATE_FIELDS and isinstance(val, int): 
        val = format_timestamp(val)

    return val


@register.filter(name="get_raw_value")
def get_raw_value(value, arg):
    if arg in reverse_map_field_names:
        arg = reverse_map_field_names[arg]
    
    if isinstance(value, dict):
        val = value[arg]
    else:
        val = getattr(value, arg)
        
    if isinstance(val, str):
        val = quote(val, safe='') 

    return val

@register.filter
def getrichtextattribute(value, arg):
    attribute = getattr(value, arg, None)
    if attribute and hasattr(attribute, 'html'):
        return attribute.html
    return ""

@register.filter
def getdropdownattribute(value, arg):
    if arg in reverse_map_field_names:
        arg = reverse_map_field_names[arg]

    attribute = getattr(value, arg, None)
    try:
        value = int(attribute)
        dropdown = DependentDropdown.objects.filter(pk=value).first()
        if dropdown:
            return dropdown.title
    except:
        pass
    return attribute

@register.filter(name="getformattribute")
def getformattribute(value, arg):
    
    #print( ' > ' + str( type( value ) ) + ' -> ' + str( arg ) )
    
    if isinstance(value, dict):
        val = value[arg]
    else:
        val = getattr(value, arg)

    # dateFields = ['ImportDate', 'DeviceLastConnUtc', 'Import_date', 'Device_LastConnUtc', 'ReleaseDate', 'EndofSupportDate','Start_Date','End_Date','Audit_Date','Last_Approval_Date', 'DataAge','Created_in_AD','Last_AD_Logon','Last_Network_ping','AD_Account_Created','Password_Last_Set','Purchase_Date','Warranty_Exiry_Date','Start_time','End_time','Last_Scan','Last_Successful_Scan','Last_Boot_Time','Last_Patched_Time','Last_Contact_Time','Last_Contacted_Time_with_DS','Last_Success_or_Warning','Last_Startup','Last_Shutdown','Agent_Installation','Agent_Upgrade','Hotfix','Last_Firewall_Count_Sent','Last_Virus_Scan_Manual','Last_Virus_Detection_Real_time','Last_Virus_Scan_Scheduled','Last_Virus_Scan_Scan_Now','Last_Spyware_Scan_Manual','Last_Spyware_Detection_Real_time','Last_Spyware_Scan_Scheduled','Last_Spyware_Scan_Scan_Now','Deployed_Date','Agent_Responded_Time','Created_Time_Ticket','Customer_Responded_Time','Modified_Time_Ticket','Ticket_Closed_Time','Software_Detected_Time','Software_Installed_Date','Last_Successful_Asset_Scan','Last_Contact_Time','Shipping_Date','Warranty_Expiry_Date','Last_Asset_Scan_Time','Last_Boot_Time','Agent_Installed_Date','OS_Installed_Date','Date_of_birth','Date_engaged','start_date','end_date','opened_at','sys_updated_on','Date_Joined_Group','Termination_Date','Device_Last_Seen','Date_Joined_Group','Termination_Date','lastLogon','pwdLastSet','lastLogonTimestamp','Last_Logon','whenCreated','Warranty_Exp_Date','Ship_Date','Last_dirsync_time','Last_password_change_time_stamp','Soft_deletion_time_stamp','When_created','Sensor_last_connected','Agent_last_connected','Last_scanned','Component_update_change','AD_LastLogonTimeStamp','SCCM_LastSoftwareScan','ITSM_ModifiedDate','_1e_LastSeen','_1e_LastBootUtc','Date','DATE','VPN_Last_Used','Servicenow_Last_Used','SAP_Last_Used','Financial_system_Last_Used','SPLUNK_Last_Used','HR_Last_Used','Payroll_Last_Used', 'Start_time', 'Last_Password_Change_For_Policy', 'Modified_Date','Submit_Date', 'Last_Resolved_Date','Target_Date', 'Start_date_', 'Renewal_date_', 'Create_Date','Time_Of_Release', 'Time', 'Completed_Time', 'Created_Time', 'DueBy_Time', 'Last_Update_Time', 'Resolved_Time', 'Responded_Date', 'User_Updated', 'Date_Engaged', 'Date_Joined', 'Termination_Date','Target_Date', 'Actual_End_Date', 'Actual_Start_Date', 'Completed_Date', 'Earliest_Start_Date', 'End_Time', 'Last_Modified_Date', 'Requested_End_Date', 'Requested_Start_Date', 'Scheduled_End_Date', 'Scheduled_Start_Date', 'Submit_Date','Start_date', 'Renewal_date',]

    # Process TimeStamp -> Date
    if arg in DATE_FIELDS and isinstance(val, int): 
        val = format_timestamp(val, is_edit=True)

    return val


@register.filter(name="get_one_list")
def get_one_list(combos):
    one_side = combos['one_side']
    if one_side:
        content_type = ContentType.objects.get(model=one_side[0].lower())
        model_class = content_type.model_class()

        return model_class.objects.values_list(one_side[1], flat=True).order_by(one_side[1]).distinct()

    return []


@register.filter(name="getdynamicattribute")
def getdynamicattribute(value_list, index):
    return value_list[index]

@register.filter(name="set_article")
def set_article(field):
    vowels = "aeiou"
    if field.lower().startswith(tuple(vowels)):
        return "an"
    else:
        return "a"

@register.filter(name="split_media_path")
def split_media_path(path):
    file_name = path.split('/')[-1]
    return file_name


@register.filter(name="iso8601_datetime")
def iso8601_datetime(datetime_obj):
    iso_datetime = timezone.localtime(datetime_obj).isoformat()
    return iso_datetime


@register.filter(name="decrypt_value")
def get_decrypted_value(value):
    return decrypt_value(value)

@register.filter
def strip_space(value):
    return value.strip()


@register.filter
def url_has_pattern(view_name):
    """Check if the given view_name exists as a named URL pattern in Django."""
    try:
        url_patterns = get_resolver().reverse_dict.keys()
        return view_name in url_patterns
    except Exception:
        return False


@register.filter
def percentage(value, decimals=1):
    try:
        return f"{round(float(value) * 100, decimals)}%"
    except (ValueError, TypeError):
        return ""