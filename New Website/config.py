import authomatic
from authomatic.providers import oauth2, oauth1

CONFIG = {
    'google': {
        'class_': oauth2.Google,
        'consumer_key': '801799207789-qj58obkub7m1coj112fje0vs57mi8ode.apps.googleusercontent.com',
        'consumer_secret': '0Jjk48bTxHGGRgt2ycYccZ-Z',
        'id': authomatic.provider_id(),
        'scope': oauth2.Google.user_info_scope + ['https://www.googleapis.com/auth/calendar',
                                                  'https://mail.google.com/mail/feed/atom',
                                                  'https://www.googleapis.com/auth/drive',
                                                  'https://gdata.youtube.com'],
        '_apis': {
            'List your calendars': ('GET', 'https://www.googleapis.com/calendar/v3/users/me/calendarList'),
            'List your YouTube playlists': ('GET', 'https://gdata.youtube.com/feeds/api/users/default/playlists?alt=json'), }, }}