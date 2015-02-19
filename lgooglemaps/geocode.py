#!/usr/bin/env python
import re
import db
from geopy import geocoders

API_KEY = 'ABQIAAAAzOcWoN9VrUNYDoUB9nDCQBQqqpmRkF6QEoqaptmWZ6CFb03F4xT0lqZk0bixJjAWk-pzp4_4G2SpEg'
DEMO = """"
{u'Point': {u'coordinates': [-2.0308790999999999, 51.918103799999997, 0]}, 
 u'ExtendedData': {u'LatLonBox': {u'west': -2.0322281000000002, u'east': -2.0295301000000001, u'north': 51.919452800000002, u'south': 51.9167548}}, 
 u'AddressDetails': {u'Country': {u'CountryName': u'UK', 
                                  u'Locality': {u'LocalityName': u'Cheltenham', u'DependentLocality': {u'PostalCode': {u'PostalCodeNumber': u'GL52 3NG'}, 
                                  u'Thoroughfare': {u'ThoroughfareName': u'4 Queenwood Grove'}, u'DependentLocalityName': u'Prestbury'}}, 
                                  u'CountryNameCode': u'GB'},
                     u'Accuracy': 8},
 u'id': u'p1', 
 u'address': u'4 Queenwood Grove, Prestbury, Cheltenham, Gloucestershire GL52 3NG, UK'}


{u'Point': {u'coordinates': [145.02862300000001, -37.767795, 0]}, 
 u'ExtendedData': {u'LatLonBox': {u'west': 145.02727400000001, u'east': 145.02997199999999, u'north': -37.766446000000002, u'south': -37.769143999999997}}, 
 u'AddressDetails': {u'Country': {u'CountryName': u'Australia', 
                                  u'AdministrativeArea': {u'AdministrativeAreaName': u'VIC',
                                                          u'Locality': {u'PostalCode': {u'PostalCodeNumber': u'3078'}, 
                                                          u'Thoroughfare': {u'ThoroughfareName': u'160 Fulham Rd'}, 
                                                          u'LocalityName': u'Alphington'}},
                                  u'CountryNameCode': u'AU'},
                     u'Accuracy': 8}, 
 u'id': u'p1',
 u'address': u'160 Fulham Rd, Alphington VIC 3078, Australia'}
"""

def format_search_query(search_query):
    search_query = re.sub(r'\t',' ',search_query)
    search_query = re.sub(r',',' ',search_query)
    search_query = re.sub(r'[*]',' ',search_query)
    search_query = re.sub(r'[.]',' ',search_query)
    search_query = re.sub(r'["]',' ',search_query)
    search_query = re.sub(r'\s{2,}',' ',search_query)
    return search_query.strip()
    
class GeoCode(object):
    def __init__(self, conn):
        self.g = geocoders.GoogleV3()
        self.conn = conn

    def search(self, search_query):
        #check daily limit here
        place=''
        lat = ''
        lng = ''
        search_query = format_search_query(search_query)
        results = dtconfig.DB.query("""
            select count(*) as totalcount from geocode_cache
            where last_activity::date = now()::date
        """)
        today_count = results[0].totalcount
        print today_count
        if today_count < 10000:
            results = dtconfig.DB.query("""
                select * from geocode_cache
                where search_query ~* regex_escape($search_query)
            """, vars=locals())
            if results:
                result = results[0]
                print 'found in cache %d ' % result.id
                return (result.place, result.lat, result.lng)
            try:
                place, (lat, lng) = self.g.geocode(search_query)
                lat = str(lat)
                lng = str(lng)
            except ValueError:
                pass
            finally:
                seqid = dtconfig.DB.insert('geocode_cache', search_query = search_query, place = place, lat = str(lat), lng = str(lng))
            
        return (place, lat, lng)
    
    def search1(self, search_query):
        a = self.g.geocode(search_query)
        print type(a)
        print dir(a)
        print a.address
        print a.altitude
        print a.latitude
        print a.longitude
        print a.point
        print a.raw
        
    def __del__(self):
        del self.g

if __name__ == '__main__':
    conn = db.get_connection()
    app = GeoCode(conn)
    #print app.search('"50 Ratclft Rd WA 4555"')
    #print app.search1('"50 Ratclft Rd WA 4555"')
    #print app.search('4 Queenwood Grove, Prestbury')
    #print app.search('No 9 Teng Tong Road Singapore 423499')

    import urllib, urllib2
    import json
    import pprint
    params = {'address': '51 honour avenue wyndham vale',
              'sensor': 'false'}

    url = 'https://maps.googleapis.com/maps/api/geocode/json?' + urllib.urlencode(params)
    #url = 'https://maps.googleapis.com/maps/api/geocode/json?address={0}&sensor=true_or_false&key=API_KEY'.format(urllib.urlencode(params))

    rawreply = urllib2.urlopen(url).read()
    reply = json.loads(rawreply)
    pprint.pprint(reply)
    # for result in reply['results']:
    #     print '-'*40
    #     pprint.pprint(result['address_components'])
    #     print '*'*40
    #lat = reply['results'][0]['geometry']['location']['lat']
    #lng = reply['results'][0]['geometry']['location']['lng']

    #print '[%f; %f]' % (lat, lng)
