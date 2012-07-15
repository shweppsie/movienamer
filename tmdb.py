from urllib import urlencode
from urllib2 import Request, urlopen
import json

key = '3e7807c4a01f18298f64662b257d7059'
useragent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.41 Safari/537.1'

def search(movie, year=None, max=None):
	data = [ ( 'api_key' , key ), ('query' , movie ) ]
	if year != None:
		data.append( ( 'year' , year ) )
	
	data = urlencode(data)
	url = 'http://api.themoviedb.org/3/search/movie?%s' % data

	r = Request(url)
	r.add_header('Accept','application/json')
	r.add_header('User-Agent',useragent)

	res = json.load( urlopen(r) )
	
	if max != None:
		res = res[:5]

	return res['results']
