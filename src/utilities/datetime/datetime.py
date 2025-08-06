from datetime import datetime
from langchain.tools import tool

@tool
def get_datetime_info(_: str = "") -> str:
    """
    Return the current year, month, day, hour, minute, second, and day of week as a string.
    Use this tool when you need to know the current date and time.
    """
    now = datetime.now()
    year = now.year
    month = now.month
    day = now.day
    hour = now.hour
    minute = now.minute
    second = now.second
    weekday = now.strftime('%A')
    return (
        f"Year: {year}\n"
        f"Month: {month}\n"
        f"Day: {day}\n"
        f"Hour: {hour}\n"
        f"Minute: {minute}\n"
        f"Second: {second}\n"
        f"Day of week: {weekday}"
    ) 