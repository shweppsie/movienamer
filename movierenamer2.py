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
		return res
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
	sys.stdout.write(WHITE)
	opt_extensions = ['avi','mp4','mkv','m4v','mpg','mpeg','.iso']

	"""Return the guessed name of a movie file"""

	if not os.path.exists(f):
		print 'Error: File does not exist: "%s"' %f 
		return
	elif not os.path.isfile(f):
		print 'Warning: Not a File: "%s", ignoring' % f
		return

	extensions = []

	f = f.decode('utf-8')

	directory = os.path.dirname(f)
	basename = os.path.basename(f)

	print "Processing %s..." % basename.encode("UTF-8")

	old_name, extension = os.path.splitext(basename)

	found = False
	for i in opt_extensions:
		if extension.lower() == '.'+i.replace('.','').lower():
			found = True
			break
	if not found:
		print 'Warning: Unknown extension: "%s", ignoring' %f
		return

	extensions.append(extension)
	
	if os.path.exists(os.path.join(directory,old_name+'.idx')):
		print "Found extra files to rename: '%s.idx'" % (old_name)
		extensions.append('.idx')
	if os.path.exists(os.path.join(directory,old_name+'.sub')):
		print "Found extra files to rename: '%s.sub'" % (old_name)
		extensions.append('.sub')
	if os.path.exists(os.path.join(directory,old_name+'.srt')):
		print "Found extra files to rename: '%s.srt'" % (old_name)
		extensions.append('.srt')

	clean_name = gen_clean_name(old_name)
	if options.search_year:
		date = options.search_year
		print "Using specified date: %s" % date
	else:
		date = get_date(old_name)
	if date != None:
		date_name = "%s %s" % (clean_name, date)

	resA = []
	resB = []
	results = []
	
	# fetch results
	resA = search(clean_name)
	if date_name != None:
		resB = search(date_name)

	# join the results list together removing dups
	results.extend(resA)
	for b in resB:
		fail=False
		for res in results:
			if b['id'] == res['id']:
				fail=True
		if not fail:
			results.append(b)

	# bail if we have no results
	if len(results) < 1:
		print "%sNo Results for %s!%s" % (RED,old_name,WHITE)
		return

	# finish if the original name matches a result perfectly
	for res in results:
		if build_name(res) == old_name:
			return

	suggestions = []
	for res in results:
		if 'released' in res and res['released'] != None:
			if res['released'][:4] == date:
				suggestions.append(res)

	if len(suggestions) < 1:
		suggestions = results
	if len(suggestions) == 1:
		name = suggestions[0]
		rename(directory,old_name,build_name(suggestions[0]),extensions)
		return

	for i in xrange(len(results)):
		res = results[i]
		if 'released' in res and res['released'] != None:
			print "%d - %s (%s) http://www.themoviedb.org/movie/%s" % (i, res['name'], res['released'][:4], res['id'])
		else:
			print "%d - %s http://www.themoviedb.org/movie/%s" % (i, res['name'], res['id'])
	answer = raw_input("Result? [0-9]*:")
	if re.match('[0-9]*',answer):
		res = results[int(answer)]
		rename(directory,old_name,build_name(res),extensions)


def build_name(result):
	newname = result['name']
	if 'released' in result and result['released'] != None:
		year = result['released'][0:4]
		name = "%s (%s)" % (newname, year)
	else:
		name = "%s" % (newname)

	return name

def rename(directory,old_name, newname, extensions):
	newname = re.sub(':',',',newname)

	if old_name == newname:
		return

	for i in extensions:
		print "%sRenaming '%s%s' -> '%s%s'" % (GREEN,old_name,i,newname,i.lower())

	answer = raw_input("Rename? [Y/y]:")
	if answer.lower() == "y":
		for i in extensions:
			os.rename(os.path.join(directory,old_name+i),os.path.join(directory,newname+i.lower()))
			sys.stdout.write(RESET)
		return True
	print "Skipping renaming"
	sys.stdout.write(RESET)
	return False

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
