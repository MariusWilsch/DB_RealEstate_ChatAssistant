# @traceable(name="getCalendly")
# def get_calendly():

#     AIRTABLE_API_KEY = 'patPHyS8sFfq0mXFo.13852f42f1266bf24a910185004b7132328f508d8d7f675cdc53d6331c97f037'
#     AIRTABLE_BASE_ID = 'appgufMUru0W64cNO'  # Example Base ID
#     TABLE_NAME_USERINFO = 'Lead'  # Example Table Name
#     TABLE_NAME_FILTER = 'Filter'
#     TABLE_NAME_THREAD = 'Thread'
#     # Calendly API URLs and Headers
#     url = "https://api.calendly.com/users/me"
#     url_events = "https://api.calendly.com/scheduled_events"

#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": "Bearer eyJraWQiOiIxY2UxZTEzNjE3ZGNmNzY2YjNjZWJjY2Y4ZGM1YmFmYThhNjVlNjg0MDIzZjdjMzJiZTgzNDliMjM4MDEzNWI0IiwidHlwIjoiUEFUIiwiYWxnIjoiRVMyNTYifQ.eyJpc3MiOiJodHRwczovL2F1dGguY2FsZW5kbHkuY29tIiwiaWF0IjoxNzE2MzA3MTYxLCJqdGkiOiJlOGY5NDYyNi03NmJlLTRhNmQtYjJiMC1mNTcyMDY4ZmZlNmUiLCJ1c2VyX3V1aWQiOiIxMmMyY2MxOS1jNTkyLTQwMzItYWIzNy01YTYzMzdmZWUwMmQifQ.X61hQ4skDatjGUGqL1M94Fme_FtFyBxBPXaNsN5ZNNggheo9ByhvEAWQNnlHdfSZckP39tyv62mH4_dbHNwoMA"
#     }

#     # Get User
#     response_user = requests.get(url, headers=headers)

#     if response_user.status_code == 200:
#         response_user_data = response_user.json()
#         uri = response_user_data["resource"]["uri"]
#         print("***********************")
#         print(uri)
#         print("***********************")
#     else:
#         print("***********************")
#         print("Failed to retrieve data:", response_user.status_code)
#         print("***********************")

#     # List Events
#     querystring_events = {"user":uri, "sort":"start_time:desc"}

#     response_events = requests.request("GET", url_events, headers=headers, params=querystring_events)
#     collections = response_events.json().get("collection", [])
#     uri_events = [event.get("uri") for event in collections]

#     # uri_event = response.json()["collection"][0]["uri"]

#     # print(response.text)
#     print("***********************")
#     print(len(uri_events))
#     print(uri_events)
#     print("***********************")

#     # Get Event Invitees
#     #Pre-process the uri_events to uuid_events
#     uuid_events = [url.split('/')[-1] for url in uri_events]

#     events_invitees = []

#     for uuid in uuid_events:
#         url = f"https://api.calendly.com/scheduled_events/{uuid}/invitees"
#         response = requests.get(url, headers=headers)
#         if response.status_code == 200:
#             invitees_data = response.json().get("collection", [])
#             for invitee in invitees_data:
#                 event_invitee = {
#                     "url": url,
#                     "created_at": invitee.get("created_at", ""),
#                     "tracking": {
#                         "utm_campaign": invitee.get("tracking", {}).get("utm_campaign", ""),
#                         "utm_medium": invitee.get("tracking", {}).get("utm_medium", ""),
#                         "utm_term": invitee.get("tracking", {}).get("utm_term", "")
#                     }
#                 }
#                 events_invitees.append(event_invitee)
#         else:
#             print(f"Failed to retrieve invitees for event {uuid}: {response.status_code}")

#     print("***********************")
#     print("RESULT:", events_invitees[0], "\n", events_invitees[1])
#     print("***********************")

#     results = []

#     # Logging the initial events list
#     logging.debug(f"Initial events_invitees: {events_invitees}")

#     events_invitees_chatbot = [event for event in events_invitees if event.get('utm_medium') == 'chatbot']

#     # Logging the filtered events list
#     logging.debug(f"Filtered events_invitees_chatbot: {events_invitees_chatbot}")

#     for event in events_invitees_chatbot:
#         utm_campaign = event.get('utm_campaign')
#         utm_term = event.get('utm_term')

#         # Logging the current event being processed
#         logging.debug(f"Processing event: {event}")

#         if not utm_campaign or not utm_term:
#             skip_message = f"Skipping event with missing utm_campaign or utm_term: {event}"
#             logging.warning(skip_message)
#             results.append(skip_message)
#             continue

#         data_payload = {
#             "performUpsert": {
#                 "fieldsToMergeOn": [
#                     "ThreadID"
#                 ]
#             },
#             "records": [{
#                 "fields": {
#                     "ThreadID": utm_campaign,
#                     "Meeting Booked": "Booked",
#                     "Meeting Booked at": utm_term
#                 }
#             }]
#         }

#         url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME_THREAD}"
#         headers = {
#             "Authorization": f"Bearer {AIRTABLE_API_KEY}",
#             "Content-Type": "application/json"
#         }

#         # Logging the payload and request details
#         logging.debug(f"Payload: {data_payload}")
#         logging.debug(f"URL: {url}")
#         logging.debug(f"Headers: {headers}")

#         response = requests.post(url, json=data_payload, headers=headers)

#         # Logging the response
#         logging.debug(f"Response Status Code: {response.status_code}")
#         logging.debug(f"Response Text: {response.text}")

#         if response.status_code == 200:
#             success_message = f"Record for ThreadID {utm_campaign} updated successfully."
#             logging.info(success_message)
#             results.append(success_message)
#         else:
#             error_message = f"Failed to update record for ThreadID {utm_campaign}. Response: {response.text}"
#             logging.error(error_message)
#             results.append(error_message)

#     return results