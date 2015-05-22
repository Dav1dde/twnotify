import argparse
import tempfile
import traceback
import datetime
from gi.repository import Notify, GLib
import requests
import time
import sys


MIME_TYPE = 'application/vnd.twitchtv.v3+json'
FOLLOWS_ENDPOINT = 'https://api.twitch.tv/kraken/users/{0}/follows/channels'
STREAM_ENDPOINT = 'https://api.twitch.tv/kraken/streams/{0}'


def get_follows(username):
    def make_request(offset=0):
        response = requests.get(
            FOLLOWS_ENDPOINT.format(username),
            params=dict(limit=100, offset=offset),
            headers=dict(accept=MIME_TYPE)
        )
        response.raise_for_status()
        return response.json()

    follows = list()
    offset = 0
    page = make_request(offset)
    while True:
        follows.extend(page['follows'])

        if len(follows) <= page['_total']:
            break

        offset += len(page['follows'])
        page = make_request(offset)

    return follows


def get_stream(username):
    response = requests.get(
        STREAM_ENDPOINT.format(username),
        headers=dict(accept=MIME_TYPE)
    )
    response.raise_for_status()
    j = response.json()

    return j['stream']


def download(url, fd):
    response = requests.get(url, stream=True)
    if response.ok:
        for chunk in response.iter_content(1204):
            if not chunk:
                break
            fd.write(chunk)
    fd.flush()


def notify_stream(stream):
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as icon:
        if stream['channel']['logo']:
            download(stream['channel']['logo'], icon)

        n = Notify.Notification.new(
            '{0} just went live!'.format(stream['channel']['display_name']),
            '{0} is playing {1}:\n{2}\n{3}'.format(
                stream['channel']['display_name'], stream['game'],
                stream['channel']['status'], stream['channel']['url']

            ),
            icon.name
        )
        n.set_category('presence.online')

        try:
            n.show()
        except GLib.Error:
            # sometimes this happens
            # g-dbus-error-quark: GDBus.Error:org.freedesktop.DBus.Error.ServiceUnknown
            Notify.uninit()
            Notify.init('twnotify')
            n.show()


def mainloop(username, interval=120):
    follows = get_follows(username)
    for follow in follows:
        follow['__offline'] = False

    while True:
        for follow in follows:
            stream = get_stream(follow['channel']['name'])
            if stream is None:
                follow['__offline'] = True
                continue

            if follow.get('__offline', True):
                notify_stream(stream)
            follow['__offline'] = False
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser('twnotify')

    parser.add_argument(
        '-u', '--username', dest='username',
        help='Twitch username', required=True
    )

    parser.add_argument(
        '--interval', dest='interval', type=int, default=120,
        help='The interval to check for new online streams'
    )

    parser.add_argument(
        '--logfile', dest='logfile', default=None
    )

    ns = parser.parse_args()

    if ns.logfile:
        with open(ns.logfile, 'a') as f:
            pass

    Notify.init('twnotify')
    while True:
        try:
            mainloop(ns.username, interval=ns.interval)
        except KeyboardInterrupt:
            break
        except Exception:
            if ns.logfile:
                with open(ns.logfile, 'a') as f:
                    f.write(datetime.datetime.now().isoformat(sep=' '))
                    traceback.print_exc(file=f)

            traceback.print_exc(file=sys.stderr)

    Notify.uninit()


if __name__ == '__main__':
    main()