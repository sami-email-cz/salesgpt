from token365 import get_token

from ms_graph import MSGraph

from msgraph.generated.models.event import Event
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.date_time_time_zone import DateTimeTimeZone
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.attendee import Attendee

from msgraph.generated.me.calendar.calendar_request_builder import CalendarRequestBuilder
from msgraph.generated.me.calendar.get_schedule.get_schedule_post_request_body import GetSchedulePostRequestBody
from msgraph.generated.me.calendar.get_schedule.get_schedule_request_builder import GetScheduleRequestBuilder
from msgraph.generated.me.calendar.events.item.cancel.cancel_post_request_body import CancelPostRequestBody
from msgraph.generated.me.calendar.events.item.cancel.cancel_request_builder import CancelRequestBuilder
from msgraph.generated.me.events.events_request_builder import EventsRequestBuilder
from msgraph.generated.me.events.item.event_item_request_builder import EventItemRequestBuilder

import requests
import json

from datetime import datetime


def format_date(input_date):
  # Convert input date string to datetime object
  dt = datetime.strptime(input_date, '%d-%m-%Y %H:%M')

  # Format datetime to JavaScript-compatible format
  return dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')


async def get_calendar():
  ms_graph = MSGraph()
  client = ms_graph.client

  headers = {
    'Authorization': 'Bearer ' + await ms_graph.get_token(),
    'Content-Type': 'application/json'
  }

  request_config = CalendarRequestBuilder.CalendarRequestBuilderGetRequestConfiguration(headers=headers)
  client_calendar = await client.me.calendar.get(request_configuration=request_config)

  return client_calendar


async def event_registration(date_arrival, date_departure, name, email):
  ms_graph = MSGraph()
  client = ms_graph.client

  headers = {
    'Authorization': 'Bearer ' + await ms_graph.get_token(),
    'Content-Type': 'application/json'
  }

  request_configuration = CalendarRequestBuilder.CalendarRequestBuilderGetRequestConfiguration(headers=headers)
  client_calendar = await client.me.calendar.get(request_configuration=request_configuration)
  client_calendar_id = client_calendar.id
  
  headers = {
    'Authorization': 'Bearer ' + await ms_graph.get_token('Calendars.ReadWrite'),
    'Content-Type': 'application/json'
  }

  request_body = Event()

  request_body.subject = 'Parking'

  body = ItemBody()
  # body.content_type.Html
  body_type = BodyType()
  body.content_type = body_type.Html
  body.content = 'Parking reservation'
  request_body.body = body

  start = DateTimeTimeZone()
  start.date_time = date_arrival
  start.time_zone = 'Central Europe Standard Time'

  end = DateTimeTimeZone()
  end.date_time = date_departure
  end.time_zone = 'Central Europe Standard Time'

  request_body.start = start
  request_body.end = end

  # location = event.location.Location()
  # location.display_name = location_name
  # request_body.location = location

  attendee = Attendee()
  attendee_email = EmailAddress()
  attendee_email.address = email
  attendee_email.name = name
  attendee.email_address = attendee_email
  attendee.type = 'required'
  request_body.attendees = [attendee]

  # request_body.transaction_id = ''

  request_configuration = client.me.events.EventsRequestBuilderPostRequestConfiguration(headers=headers)
  response = await client.me.calendars.by_calendar_id(calendar_id=client_calendar_id).events.post(body=request_body, request_configuration=request_configuration)

  try:
    # Response params
    subject = response.subject
    start_time = response.start.date_time
    end_time = response.end.date_time
    # location = response.location.display_name

    # Attendees
    attendees = response.attendees
    attendees_info = ''
    for attendee in attendees:
      attendees_info += attendee["emailAddress"]["name"] + " (" + attendee["emailAddress"]["address"] + "), "
    # Del white-space and comma
    attendees_info = attendees_info[:-2]

    # Output formatting for event registration
    summary = f"Event: {subject}\nArrival Date: {start_time}\nDeparture Date: {end_time}\nAttendees: {attendees_info}"
    return summary
  except Exception as e:
    return(f"Error while making reservation.\n{e}")


# def event_registration(date_arrival,date_departure, name, email):
#   # URL pro vytvoření nové události
#   url = "https://graph.microsoft.com/v1.0/me/events"

#   # Váš token
#   headers = {
#       'Authorization': 'Bearer ' + get_token(),
#       'Content-Type': 'application/json'
#   }

#   # Detaily události
#   payload = json.dumps({
#     "subject": "Parkování",
#     "body": {
#       "contentType": "HTML",
#       "content": "Rezervace parkování"
#     },
#     "start": {
#         "dateTime": f"{date_arrival}",
#         "timeZone": "Central Europe Standard Time"
#     },
#     "end": {
#         "dateTime": f"{date_departure}",
#         "timeZone": "Central Europe Standard Time"
#     },
#     # "location":{
#     #     "displayName":f"{location}"
#     # },
#     "attendees": [
#       {
#         "emailAddress": {
#           "address": f"{email}",
#           "name": f"{name}"
#         },
#         "type": "required"
#       }
#     ]
#   })

#   response = requests.request("POST", url, headers=headers, data=payload)

#   #print(response.text)

#   data = response.json()#json.loads(response.text)

#   try:
#       # Získání potřebných údajů
#       subject = data["subject"]
#       start_time = data["start"]["dateTime"]
#       end_time = data["end"]["dateTime"]
#       # location = data["location"]["displayName"]

#       # Získání účastníků
#       attendees = data["attendees"]
#       attendees_info = ""
#       for attendee in attendees:
#           attendees_info += attendee["emailAddress"]["name"] + " (" + attendee["emailAddress"]["address"] + "), "

#       # Odebrání posledního znaku čárky a mezery
#       attendees_info = attendees_info[:-2]

#       # Vytvoření a tisk souhrnu rezervace
#       summary = f"Název události: {subject}\nZačátek: {start_time}\nKonec: {end_time}\nÚčastníci: {attendees_info}"
#       #print(summary)
#       return(summary)

#   except KeyError:
#       #print("Při rezervaci došlo k chybě.")
#       return("Při rezervaci došlo k chybě.")


async def cancel_event_registration(id, subject, start, end, attendee):
  ms_graph = MSGraph()
  client = ms_graph.client

  attendee_info = "" + attendee["emailAddress"]["name"] + " (" + attendee["emailAddress"]["address"] + ")"

  try:
    # Event cancelation
    headers = {
      'Authorization': 'Bearer ' + await ms_graph.get_token('Calendars.ReadWrite'),
      'Content-Type': 'application/json'
    }

    request_body = CancelPostRequestBody()
    request_body.comment = f'Cancelling event {subject}\nAt time: {start} - {end}\nWith: {attendee_info}'

    request_configuration = CancelRequestBuilder.CancelRequestBuilderPostRequestConfiguration(headers=headers)
    await client.me.events.by_event_id(id).cancel.post(body=request_body, request_configuration=request_configuration)

    # Event deletation
    del_headers = {
      'Authorization': 'Bearer ' + await ms_graph.get_token('Calendars.ReadWrite')
    }

    del_request_configuration = EventItemRequestBuilder.EventItemRequestBuilderDeleteRequestConfiguration(headers=del_headers)
    await client.me.events.by_event_id(id).delete(request_configuration=del_request_configuration)

    return f'Event {subject}\nAt time {start} - {end}\nWith {attendee_info}\nhas been canceled and deleted'
  except Exception as e:
    return f"Error while cancelling reservation.\n{e}"


async def event_check_existence(date_arrival, date_departure, name, email):
  date_arrival = format_date(date_arrival)
  date_departure = format_date(date_departure)
  
  ms_graph = MSGraph()
  client = ms_graph.client

  headers = {
    'Authorization': 'Bearer ' + await ms_graph.get_token('Calendars.Read'),
    'Prefer': "outlook.timezone=\"Central Europe Standard Time\""
  }

  # query_params = EventsRequestBuilder.EventsRequestBuilderGetQueryParameters(
  #   select=['subject', 'body', 'start', 'end', 'attendees'],
  #   filter=f"start/dateTime eq '{date_arrival}' and end/dateTime eq '{date_departure}'"
  #   )
  
  query_params = EventsRequestBuilder.EventsRequestBuilderGetQueryParameters(select=['subject', 'body', 'start', 'end', 'attendees'])

  request_configuration = EventsRequestBuilder.EventsRequestBuilderGetRequestConfiguration(headers=headers, query_parameters=query_params)
  response = await client.me.events.get(request_configuration=request_configuration)

  event2cancel = {}
  request_response = False
  for event in response.value:
    attendee = event.attendees[0]
    if event.start.date_time == date_arrival and event.end.date_time == date_departure and attendee.email_address.address == email and attendee.email_address.name == name:
      event2cancel['id'] = event.id
      event2cancel['subject'] = event.subject
      event2cancel['start'] = event.start.date_time
      event2cancel['end'] = event.end.date_time
      event2cancel['attendee'] = attendee
      request_response = True
      break
  
  if request_response:
    return cancel_event_registration(**event2cancel)
  else:
    return 'There is not such event'


async def event_check_collision(date_arrival, date_departure, name, email):
  date_arrival = format_date(date_arrival)
  date_departure = format_date(date_departure)
  
  ms_graph = MSGraph()
  client = ms_graph.client

  headers = {
    'Authorization': 'Bearer ' + await ms_graph.get_token('.default'),
    'Content-Type': 'application/json',
    'Prefer' : "outlook.timezone=\"Central Europe Standard Time\""
  }

  request_body = GetSchedulePostRequestBody()
  request_body.schedules = ["esterai@multima.cz"]

  start = DateTimeTimeZone()
  start.date_time = date_arrival
  start.time_zone = 'Central Europe Standard Time'

  end = DateTimeTimeZone()
  end.date_time = date_departure
  end.time_zone = 'Central Europe Standard Time'

  request_body.availability_view_interval = 15

  request_configuration = GetScheduleRequestBuilder.GetScheduleRequestBuilderPostRequestConfiguration(headers=headers)
  response = await ms_graph.client.me.calendar.get_schedule.post(body=request_body, request_configuration=request_configuration)
  # response = await client.me.calendar.get_schedule.post(body=request_body)

  # if len(response.value) == 0:
  #   # return await event_registration(date_arrival, date_departure, name, email)
  #   return 'There is free time-frame'
  # else:
  #   return 'There are other events in this time-frame'
  return response


# def event_check(date_arrival, date_departure, name, email):
#   date_arrival = format_date(date_arrival)
#   date_departure = format_date(date_departure)
  
#   # URL pro vytvoření nové události
#   url = "https://graph.microsoft.com/v1.0/me/calendar/getschedule"

#   # Váš token
#   headers = {
#     'Authorization': 'Bearer ' + get_token(),
#     'Content-Type': 'application/json'
#   }

#   # Detaily události
#   payload = json.dumps({
#     "Schedules": ["esterai@multima.cz"],
#     "StartTime": {
#       "dateTime": f"{date_arrival}",
#       "timeZone": "Central Europe Standard Time"
#     },
#     "EndTime": {
#       "dateTime": f"{date_departure}",
#       "timeZone": "Central Europe Standard Time"
#     },
#     "availabilityViewInterval": "15"
#   })

#   response = requests.request("POST", url, headers=headers, data=payload)

#   data = json.loads(response.text)
#   availability_view = data['value'][0]['availabilityView']

#   # proměnná is_free je True pokud všechny bloky v availability_view jsou "0", jinak False
#   is_free = all(slot == '0' for slot in availability_view)

#   if is_free:
#     return event_registration(date_arrival, date_departure, name, email)
#   else:
#     #print("Není volno.")
#     return("V tomto čase není volno")


"""from events import event_check

date_arrival = "2023-07-06T12:30:00"
date_departure = "2023-07-06T12:45:00"
location = "Praha"
email = "stoklasa.michal666@gmail.com"


resetvation_result = event_check(date_arrival,date_departure, location, email)
print(resetvation_result)"""