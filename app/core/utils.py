def convert_to_timestamp(date_str):
    return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())