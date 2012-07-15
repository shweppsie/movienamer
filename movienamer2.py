#!/usr/bin/env python

import os,sys,time
import re,pickle

import tmdb


searches = {}

def p(text, colour=None):
	colours = {
		'green':'32',
		'red':'33',
		'white':'37',
	}
	if colour != None:
		sys.stdout.write('\033[1;%sm' % (colours[colour]))
		sys.stdout.write(text)
		sys.stdout.write('\033[1;m')
	else:
		sys.stdout.write('\033[1;m')
		sys.stdout.write(text)
	sys.stdout.write('\n')

def search(movie, year=None):
	global searches
	attempts = 3
	backoff = 5

	if movie in searches:
		res = searches[movie]
		return res
	else:
		for i in xrange(attempts):
			try:
				res = tmdb.search(movie,year)
				searches[movie] = res
				return res
			except Exception, e:
				raise

def gen_clean_name(name):
	name = name.lower()

	blacklist = ['720p','bluray','x264','dvdrip']
	for i in blacklist:
		if i.lower() in name:
			name = name.partition(i)[0]

	# remove stuff after the first square bracket
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

	dates = []
	if len(date) == 1:
		return date[0][0]
	elif len(date) > 1:
		for i in date:
			dates.append[0]
		print dates
		return dates
	else:
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
	opt_extensions = ['avi','mp4','mkv','m4v','mpg','mpeg','.iso']

	"""Return the guessed name of a movie file"""

	if not os.path.exists(f):
		print '\nError: File does not exist: "%s"' %f
		return
	elif not os.path.isfile(f):
		print '\nWarning: Not a File: "%s", ignoring' % f
		return

	f = f.decode('utf-8')

	directory = os.path.dirname(f)
	basename = os.path.basename(f)

	print "\nProcessing %s..." % basename.encode("UTF-8")

	old_name, extension = os.path.splitext(basename)

	ext = extension[1:]
	if ext.lower() not in opt_extensions:
		print 'Warning: Unknown extension: "%s", ignoring' %f
		return

	extensions = []
	extensions.append(extension)
	for i in os.listdir(directory):
		(name, ext) = os.path.splitext(i)
		if name == old_name and ext != extension:
			if(os.path.isfile(os.path.join(directory, i))):
				print "Found extra file to rename: '%s'" % (i)
				extensions.append(extension)

	clean_name = gen_clean_name(old_name)
	if options.search_year:
		year = options.search_year
		print "Using specified date: %s" % year
	else:
		year = get_date(old_name)
		if type(year) == []:
			print "Found multiple dates in filename! Use --search-year to provide the correct one"
			return
	if year == None:
		print "Can't find release date in filename! Use --search-year to provide it"

	# fetch results
	results = search(clean_name,year)

	# bail if we have no results
	if len(results) < 1:
		p("No Results for %s!" % (old_name), 'red')
		return

	if old_name == build_name(results[0]['title'],results[0]['release_date'][:4]):
		p('First result matches current name, skipping renaming','green')
		return

	for i in xrange(len(results)):
		res = results[i]
		if 'release_date' in res and res['release_date'] != None:
			print "\t%d - %s (%s) http://www.themoviedb.org/movie/%s" % (i+1, res['title'], res['release_date'][:4], res['id'])
		else:
			print "\t%d - %s http://www.themoviedb.org/movie/%s" % (i+1, res['title'], res['id'])
	answer = raw_input("Result?: ")
	if re.match('[1-9][0-9]*',answer):
		res = results[int(answer)-1]
		if not ('release_date' in res):
			p('No release year for %s' % res['name'],'red')
			return
		rename(directory,old_name,build_name(res['title'],res['release_date'][:4]),extensions)

def build_name(name, year):
	# remove chars windows can't handle
	name = name.replace(':',',')
	name = name.replace('?','')

	name = "%s (%s)" % (name, year)

	return name

def rename(directory,old_name, newname, extensions):

	if old_name == newname:
		p('New and old names match. No renaming required','green')
		return

	for i in extensions:
		p("Renaming '%s%s' -> '%s%s'" % (old_name,i,newname,i.lower()), 'green')

	while True:
		answer = raw_input("Rename? [y/n]: ")
		if answer == 'y' or answer == 'n':
			break

	if answer == "y":
		for i in extensions:
			os.rename(os.path.join(directory,old_name+i),os.path.join(directory,newname+i.lower()))
		return True
	p('Renaming Cancelled!', 'green')
	return False

def main():
	global searches

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
	pickle.dump(searches, open(os.path.expanduser('~/.movierenamer.cache'),'w'))

if __name__ == "__main__":
	main()

# vim: set sw=8 tabstop=8 softtabstop=8 noexpandtab :
