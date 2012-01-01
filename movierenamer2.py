#!/usr/bin/env python

import os,sys,time
import re,pickle

import tmdb

GREEN='\033[1;32m'
RED='\033[1;33m'
WHITE='\033[1;37m'
RESET='\033[1;m'

searches = {}

def search(term):
	global searches
	attempts = 3
	backoff = 5

	if term in searches:
		res = searches[term]
	else:
		for i in xrange(attempts):
			try:
				res = tmdb.search(term)
				searches[term] = res
				return res
			except tmdb.TmdXmlError, e:
				print "Error, retrying in %d seconds..." % backoff
				time.sleep(backoff)

def gen_clean_name(name):
	opt_blacklist = ['dvdrip']

	# remove rubbish from the filename
	#TODO: find lowercase and uppercase copies of
	#      items in the blacklist
	for i in opt_blacklist:
		name = name.replace(i,' ')

	#FIXME: temporary hack
	name = re.sub(r'\[.*','',name)
	name = splitter(name, ['(','[','www.'])[0]

	# remove junk characters
	name = re.sub('[\.\,]+',' ',name)
	# only remove a dash if there is whitespace on
	# at least one side of it
	name = re.sub('( -|- )',' ',name)
	# tidy up dulpicate spaces
	name = re.sub(' +',' ',name)
	name = name.strip()

	return name

def get_date(old_name):
	date = re.findall(r'((20|19)[0-9]{2})',old_name)

	# found more than one date
	if len(date) > 1:
		print "Found %d possible dates: %s" % (len(date), ' '.join([i[0] for i in date]))
		print "Using %s with search. Use --search-year to override." % date[len(date)-1][0]

	if len(date) > 0:
		date = date[len(date)-1][0]
		return date
	else:
		print "Can't find release date in filename! Use --search-year to provide it"
		return None

def splitter(word, separators):
	word = [word]
	for s in separators:
		res = []
		for i in range(len(word)):
			res.extend(word[i].split(s))
		word = res
	return word

def processFile(f,options):
	"""Return the guessed name of a movie file"""

	if not os.path.exists(f):
		print 'Error: File does not exist: "%s"' %f 
		return
	elif not os.path.isfile(f):
		print 'Warning: Not a File: "%s", ignoring' % f
		return

	extensions = ['avi']
	found = False
	for i in extensions:
		if f.endswith(i):
			found = True
			break
	if not found:
		print 'Warning: Unknown extension: "%s", ignoring' %f
		return
	
	extensions = []

	directory = os.path.dirname(f)
	basename = os.path.basename(f)

	basename = basename.lower()

	filename, extension = basename.rsplit('.',1)

	#TODO: rename files with the same name
	#extensions.append(extension)
	#
	#if os.path.exists(filename+'.idx'):
	#	extensions.append('idx')
	#if os.path.exists(filename+'.sub'):
	#	extensions.append('sub')
	#if os.path.exists(filename+'.srt'):
	#	extensions.append('srt')
	#
	#if len(extensions) > 1:
	#	"Found extra files to rename (subtitles)"
	
	print "Processing %s" % f

	clean_name = gen_clean_name(old_name)
	if options.search_year:
		date = options.search_year
		print "Using specified date: %s" % date
	else:
		date = get_date(old_name)
	if date != None:
		date_name = "%s %s" % (clean_name, date)


	# remove rubbish from the filename
	#for i in blacklist:
	#	filename = filename.replace(i,' ')
	filename = filename.strip()
	filename = re.sub(' +',' ',filename)

	#FIXME: temporary hack
	filename = re.sub(r'\[.*','',filename)

	filename = filename.title()

	else:
		print 'mv "%s" "/stuff/shared/videos/movies/other/%s (%s).%s"' % (f, filename, date[0][0], extension)

	#print tmdb.search(filename)

	return True





def main():
	global searches

	tmdb.configure('3e7807c4a01f18298f64662b257d7059')

	import argparse
	parser = argparse.ArgumentParser(description='Correctly Name Movie files')
	parser.add_argument(
			'-r','--recursive',
			help="Search for files recursively",
			action='store_true',
			)
	parser.add_argument(
			'--search-year',
			dest='search_year',
			action='store',
			help="Year to use when searching for result",
			)
	parser.add_argument(
			'Files',
			metavar='FILE',
			nargs='+',
			help="Files to rename",
			)
	args = parser.parse_args()

	if args.recursive and args.year:
		print "Do not use --year and --recursive"
		exit(2)

	if os.path.exists(os.path.expanduser('~/.movierenamer.cache')):
		searches = pickle.load(open(os.path.expanduser('~/.movierenamer.cache'),'r'))
	try:
		files = args.Files
		if args.recursive:
			for f in files:
				if os.path.isdir(f):
					for i in os.walk(f):
						for j in i[2]:
							processFile(os.path.join(i[0],j),args)
		else:
			for f in files:
				print f
				processFile(f,args)
	except KeyboardInterrupt, e:
		pickle.dump(searches, open(os.path.expanduser('~/.movierenamer.cache'),'r+'))
		raise
	except Exception, e:
		pickle.dump(searches, open(os.path.expanduser('~/.movierenamer.cache'),'r+'))
		raise
	pickle.dump(searches, open(os.path.expanduser('~/.movierenamer.cache'),'r+'))

if __name__ == "__main__":
	main()

# vim: set sw=8 tabstop=8 softtabstop=8 noexpandtab :
