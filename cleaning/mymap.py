#!/usr/bin/python

import urllib
import urlparse

def geocode(address):
    """Geocode the given address, updating the standardized address, latitude,
    and longitude."""
    qs = dict(q=address['address_string'], key=GMAPS_API_KEY, sensor='true',
              output='csv')
    qs = urllib.urlencode(qs)
    url = urlparse.urlunsplit(('http', 'maps.google.com', '/maps/geo', qs, ''))
    f = urllib.urlopen(url)
    result = list(csv.DictReader(f, ('status', 'accurary', 'latitude', 'longitude')))[0]
    if int(result['status']) != 200:
        raise RuntimeError, 'could not geocode address %s (%s)' % \
                            (address, result['status'])
    address['latitude'] = result['latitude']
    address['longitude'] = result['longitude']
    
    
if __name__ == '__main__':
    print geocode('160 fulham road fairfield 3078')