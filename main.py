from selenium import webdriver
import bs4
from twilio.rest import Client
import _datetime
import re
import time


def navigate_to_calendar(license_num, booking, browser):
    """Navigates to the correct page then returns the HTML for that page."""

    url = 'https://driverpracticaltest.direct.gov.uk/login'

    browser.get(url)
    license_number = browser.find_element_by_id('driving-licence-number')
    license_number.send_keys(license_num)

    booking_number = browser.find_element_by_id('application-reference-number')
    booking_number.send_keys(booking)
    booking_number.submit()

    date_change_btn = browser.find_element_by_id('date-time-change')
    date_change_btn.click()

    earliest_date_radio = browser.find_element_by_id('test-choice-earliest')
    earliest_date_radio.click()

    date_submit_btn = browser.find_element_by_id('driving-licence-submit')
    date_submit_btn.click()

    return bs4.BeautifulSoup(browser.page_source, features='html.parser')


def get_dates_and_times_in_range(low_bound, up_bound, dates_times):
    pref_dates_and_times = []
    for date in dates_times:
        if low_bound <= _datetime.date.fromisoformat(date[0]) <= up_bound:
            """This doesnt get returned, only dates_n_times does,
            either make another function or add an if statement ouside the for
            checking if low_bound and up_bound are null and returning dependent
            on those values."""
            pref_dates_and_times += [date]
    return pref_dates_and_times


def get_all_dates_and_times(soup_object):
    calendar = soup_object.select('.BookingCalendar-date--bookable .BookingCalendar-content a')
    available_dates = [tag['data-date'] for tag in calendar]

    all_dates_and_times = []
    for date in available_dates:
        available_times = soup_object.select('#date-' + date + ' label strong')
        available_times = [tag.get_text() for tag in available_times]
        all_dates_and_times += [[date] + available_times]
    return all_dates_and_times


def get_most_recent_message(twil_client, to_num):
    """Returns the most recent message sent to 'to_num'"""
    messages = twil_client.messages.list(to=to_num)
    return messages[0].body


def redact_most_recent_message(twil_client, to_num):
    """Deletes the most recent message sent to 'to_num'"""
    twil_client.messages(get_most_recent_messages_sid(twil_client, to_num)).update(body='')


def get_most_recent_messages_sid(twil_client, to_num):
    """Returns the SID of the most recent message sent to 'to_num'"""
    messages = twil_client.messages.list(to=to_num)
    return messages[0].sid


def send_message(twil_client, from_num, to_num, msg_body):
    """Sends the message 'message_body' from 'from_num' to 'to_num'"""
    twil_client.messages.create(body=msg_body, from_=from_num, to=to_num)


if __name__ == '__main__':
    # first 3 are provided from twilio, last one is the phone number to send the messages to.
    ACCOUNT_SID = ***
    AUTH_TOKEN = ***
    TWILIO_NUMBER = ***
    MY_NUMBER = ***

    twilio_client = Client(ACCOUNT_SID, AUTH_TOKEN)

    # send this sms to the user
    FIRST_MSG = 'Reply \'ASAP\' for the soonest date or \'YYYY-MM-DD:YYYY-MM-DD\''
    send_message(twilio_client, TWILIO_NUMBER, MY_NUMBER, FIRST_MSG)

    # adding this in case the most recent reply fits the criteria of the while loop
    redact_most_recent_message(twilio_client, TWILIO_NUMBER)
    # get a reply from the user and save its SID
    reply = get_most_recent_message(twilio_client, TWILIO_NUMBER)
    temp_sid = get_most_recent_messages_sid(twilio_client, TWILIO_NUMBER)

    # regex to make sure the dates are valid
    date_checker = re.compile(r'(\d{4}-\d{2}-\d{2}:\d{4}-\d{2}-\d{2})')

    # loop to ensure that the reply from the user is in the right format
    """DATE ISNT MATCHING WHEN REPLY IS 'RECENT' SO I NEED TO FIX THIS"""
    while reply.strip() != 'ASAP' and date_checker.match(reply.strip()) is None:
        reply = get_most_recent_message(twilio_client, TWILIO_NUMBER)
        reply_sid = get_most_recent_messages_sid(twilio_client, TWILIO_NUMBER)
        # if the SID has changed it means the user replied.
        # we must remind them to send it in the correct format.
        if temp_sid != reply_sid and (reply.strip() != 'ASAP' and date_checker.match(reply) is None):
            send_message(twilio_client, TWILIO_NUMBER, MY_NUMBER, FIRST_MSG)
            temp_sid = reply_sid

    # navigate to the calendar page and get soup data
    chrome_browser = webdriver.Chrome()
    soup = navigate_to_calendar(***, ***, chrome_browser)

    # get the dates and times dependent on the users reply and create a message from them
    if reply == 'ASAP':
        dates_and_times = get_all_dates_and_times(soup)[0]
        message_body = "-\n\nDate: " + dates_and_times[0] + "\nTimes: " + " ".join(dates_and_times[1:])
    else:
        lower_bound = _datetime.date.fromisoformat(reply[:10])
        upper_bound = _datetime.date.fromisoformat(reply[11:])
        dates_and_times = get_dates_and_times_in_range(lower_bound, upper_bound, get_all_dates_and_times(soup))[:3]
        message_body = ''
        for date_time in dates_and_times:
            message_body += "\n\nDate: " + date_time[0] + "\nTimes: " + " ".join(date_time[1:])

    # sends the above message to the user
    send_message(twilio_client, TWILIO_NUMBER, MY_NUMBER, message_body)

    # automatically selects the soonest date
    print(dates_and_times)
    click_date = chrome_browser.find_element_by_xpath("//a[@data-date='" + dates_and_times[0] + "']")
    click_date.click()

    # automatically select the earliest time
    xpath = "//li[@id='date-"+dates_and_times[0]+"']//label[1]"
    click_time = chrome_browser.find_element_by_xpath(xpath)
    click_time.click()

    # automatically click continue
    lock_in_date_time = chrome_browser.find_element_by_id('slot-chosen-submit')
    lock_in_date_time.click()
    time.sleep(40)

    # need to send these dates/times to the user in a good format  x
    # the user needs to select a date/time: x
    # * if theres only one date/time it automatically gets selected,
    #   before proceeding any further though we need the user to reply (e.g. "YES"),
    # * if theres multiple dates/times we send them the first 3 nicely formatted,
    #   they should them reply with the date and time (example format: "YYYY-MM-DD(1:25pm)"
    #   once they reply the system should automatically select it (to prevent it being taken),
    # * need to make sure its a valid response from user before proceeding any further
    # * we should get them to double check the date/time before finalizing
