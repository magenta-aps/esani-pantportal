# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
def clean_phone_no(phone):
    cleaned_phone_no = phone.replace(" ", "")

    if cleaned_phone_no.startswith("(+299)"):
        return "(+299) " + cleaned_phone_no[6:]
    elif cleaned_phone_no.startswith("(+45)"):
        return "(+45) " + cleaned_phone_no[5:]
    elif cleaned_phone_no.startswith("+45"):
        return "(+45) " + cleaned_phone_no[3:]
    elif cleaned_phone_no.startswith("+299"):
        return "(+299) " + cleaned_phone_no[4:]
    elif len(cleaned_phone_no) == 6:
        return "(+299) " + cleaned_phone_no
    elif len(cleaned_phone_no) == 8:
        return "(+45) " + cleaned_phone_no
    elif cleaned_phone_no.startswith("299") and len(cleaned_phone_no) == 9:
        return "(+299) " + cleaned_phone_no[3:]
    elif cleaned_phone_no.startswith("45") and len(cleaned_phone_no) == 10:
        return "(+45) " + cleaned_phone_no[2:]
    elif cleaned_phone_no.startswith("00299") and len(cleaned_phone_no) == 11:
        return "(+299) " + cleaned_phone_no[5:]
    elif cleaned_phone_no.startswith("0045") and len(cleaned_phone_no) == 12:
        return "(+45) " + cleaned_phone_no[4:]
    else:
        return phone
