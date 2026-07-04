GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'
GOOGLE_SCOPE = ' '.join([
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
])

GOOGLE_CALENDAR_LIST_URL = 'https://www.googleapis.com/calendar/v3/users/me/calendarList'
GOOGLE_EVENTS_URL = 'https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events'
