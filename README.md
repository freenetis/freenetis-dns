freenetis-dns
=============

FreenetIS DNS synchronization tool.

Requirements
------------
 - Python 2.6
 - BIND 9
 - named-checkconf


Installation
------------
 - Copy [freenetis-dns.conf](freenetis-dns.conf) to /etc/freenetis/
 - Copy [freenetis-dns-sync.py](freenetis-dns-sync.py) to /root
 - Copy [freenetis](freenetis) to /etc/cron.d/
 - Configure CRON interval in /etc/cron.d/freenetis

Changelog
---------
Changelog in debian format is available [here](changelog).
