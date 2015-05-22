twnotify
========

Get notified if one of your favorite streamers go online

## Requirements ##

* Python 3
* [requests](https://pypi.python.org/pypi/requests/)
* [pygobject](https://pypi.python.org/pypi/PyGObject/)


## Usage ##

Drop `twnotify.py` somewhere and adjust the `twnotify.dekstop` file accordingly, afterwards copy it to
`~/.local/share/applications/` and/or to `~/.config/autostart`. 

Don't forget to pass your username via commandline:

    Exec=twnotify --username foobar
    
Alternatively create a shell script which launches *twnotify* for you with the correct username.