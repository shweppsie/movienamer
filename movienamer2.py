#!/usr/bin/env python

import os,sys,time
import re,pickle

import tmdb


searches = {}

class Movienamer:
	def search(self, movie, year=None):
		global searches
		attempts = 3
		backoff = 5

		if year == None:
			index = movie
		else:
			index = movie+year
		if index in searches:
			res = searches[index]
			print 'Using cached result'
			return res
		else:
			for i in xrange(attempts):
				try:
					movie = movie.encode('utf-8')
					res = tmdb.search(movie,year)
					searches[index] = to_unicode(res)
					return res
				except Exception, e:
					raise

	def gen_clean_name(self, name):
		name = name.lower()

		blacklist = ['720p','1080p','bluray','x264','dvdrip','LiMiTED','HDRip','unrated','brrip','XviD','bdrip','eng','extended']
		for i in blacklist:
			i = i.lower()
			if i in name:
				name = name.partition(i)[0]

		# remove stuff after the first square bracket
		name = re.sub(r'\[.*','',name)
		name = splitter(name, ['(','[','{','www.'])[0]

		# remove junk characters
		name = re.sub('[\.\,;_]+',' ',name)

		# only remove a dash if there is whitespace on
		# at least one side of it
		name = re.sub('( -|- )',' ',name)

		# tidy up dulpicate spaces
		name = re.sub(' +',' ',name)
		name = name.strip()

		return name

	def get_date(self, oldname):
		date = re.findall(r'((20|19)[0-9]{2})',oldname)

		dates = []
		if len(date) == 1:
			return date[0][0]
		elif len(date) > 1:
			for i in date:
				dates.append(i)
			return dates
		else:
			return None

	""" Eventually this function will produce custom filenames """
	def build_name(self, name, year):
		name = self.prepare_name(name)

		name = "%s (%s)" % (name, year)

		return name

	""" Remove characters from names that certain OSs can't handle """
	def prepare_name(self, name):
		# Windows: / ? < > \ : * | " ^
		# MacOS: : /
		# Linux: /

		# ensure name does not begin with a dot
		name = re.sub('^\.','',name)

		# change colons to commas
		name = re.sub(' *:',',',name)

		# remove other illegal chars
		name = re.sub('[/?<>\:*"^]',' ',name)

		# tidy up extra spaces we may have added
		name = re.sub('  +',' ',name)
		name = name.strip()

		return name

	def rename(self, directory, oldname, newname, extensions):

		if oldname == newname:
			p('New and old names match. No renaming required','green')
			return

		for i in extensions:
			filename = newname+i.lower()
			if os.path.exists(os.path.join(directory, filename)):
				p('Error: Rename will overwrite file "%s"!' % filename, 'red')
				return

		for i in extensions:
			old='%s.%s' % (oldname, i)
			new='%s.%s' % (newname, i.lower())
			p("Renaming '%s' -> '%s'" % (old,new), 'green')
			os.rename(os.path.join(directory,old),os.path.join(directory,new))

	def process_file(self, f, options):
		opt_extensions = ['avi','mp4','mkv','m4v','mpg','mpeg','iso','ogm']

		"""Return the guessed name of a movie file"""

		if not os.path.exists(f):
			p('\nError: File does not exist "%s"' %f,'red')
			return
		elif not os.path.isfile(f):
			p('\nError: Not a File "%s", ignoring' % f,'red')
			return

		f = to_unicode(f)

		basename = os.path.basename(f)
		directory = os.path.dirname(f)
		if directory == '':
			directory = '.'

		p('\nProcessing %s...' % basename.encode("UTF-8"))

		oldname, ext = os.path.splitext(basename)

		# only process files known video extensions
		ext = ext[1:]
		if ext.lower() not in opt_extensions:
			p('Warning: Unknown extension "%s", ignoring' %f,'yellow')
			return

		# process any extra files
		extensions = []
		extensions.append(ext)
		for i in os.listdir(directory):
			i = to_unicode(i)
			# ensure this isn't the file we're renaming
			if basename != i:
				(name, ext) = os.path.splitext(i)
				ext = ext[1:]
				if name == oldname:
					if ext in opt_extensions:
						p('Error: multiple video files named "%s"!' % name, 'red')
						return
					else:
						p('Found extra file to rename "%s"' % (i))
						extensions.append(ext)

		# take a copy of the original name
		clean_name = oldname

		# deal with release year
		if options.search_year:
			year = options.search_year
			print "Using specified date: %s" % year
		else:
			year = self.get_date(oldname)
			if type(year) == type([]):
				p("Error: Found multiple dates in filename! Use --search-year to provide the correct one", 'red')
				return
		if year == None:
			print "Can't find release date in filename! Use --search-year to provide it"
		else:
			# remove year from name for searching purposes
			clean_name = clean_name.replace(year,'')

		clean_name = self.gen_clean_name(clean_name)

		# fetch results
		if year != None:
			print 'Searching for "%s" with year %s' % (clean_name, year)
		else:
			print 'Searching for "%s" ' % (clean_name)
		results = self.search(clean_name,year)

		if len(results) < 1:
			# no results, retry search without year
			if year != None:
				print 'Searching again without year'
				results = self.search(clean_name)
			# no results
			if len(results) < 1:
				p("No Results for %s!" % (oldname), 'red')
				return

		if self.prepare_name(oldname) == self.build_name(results[0]['title'],results[0]['release_date'][:4]):
			p('First result matches current name, skipping renaming','green')
			return

		for i, res in enumerate(results):
			title = res['title']
			date = res['release_date'][:4]
			url = "http://www.themoviedb.org/movie/%s" % res['id']
			if 'release_date' in res and res['release_date'] != None:
				release_date = res['release_date'][:4]
				print "\t%d - %s (%s) %s" % (i+1, title, release_date, url)
			else:
				print "\t%d - %s %s" % (i+1, title, url)
		answer = raw_input("Result?: ")
		if re.match('[1-9][0-9]*',answer):
			res = results[int(answer)-1]
			if not ('release_date' in res):
				p('No release year for %s' % res['name'],'yellow')
				return

			title = res['title']
			date = res['release_date'][:4]
			newname = build_name(title,date)
			rename(directory, oldname, newname, extensions)

def to_unicode(string):
	if isinstance(string, basestring):
		if not isinstance(string, unicode):
			string = unicode(string, 'utf-8')
	return string

def p(text, colour=None):
	colours = {
		'red':'31',
		'aqua':'36',
		'pink':'35',
		'blue':'34',
		'green':'32',
		'yellow':'33',
		'white':'37',
	}
	if colour != None:
		sys.stdout.write('\033[1;%sm' % (colours[colour]))
		sys.stdout.write(text.encode('utf-8'))
		sys.stdout.write('\033[1;m')
	else:
		sys.stdout.write('\033[1;m')
		sys.stdout.write(text.encode('utf-8'))
	sys.stdout.write('\n')

def splitter(word, separators):
	word = [word]
	for s in separators:
		res = []
		for i in range(len(word)):
			res.extend(word[i].split(s))
		word = res
	return word

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

	if args.recursive and args.search_year:
		print "Do not use --year and --recursive"
		exit(2)

	movienamer = Movienamer()

	if os.path.exists(os.path.expanduser('~/.movienamer.cache')):
		searches = pickle.load(open(os.path.expanduser('~/.movienamer.cache'),'r'))
	try:
		files = args.Files
		if args.recursive:
			for f in files:
				if os.path.isdir(f):
					for i in os.walk(f):
						for j in sorted(i[2]):
							movienamer.process_file(os.path.join(i[0],j),args)
		else:
			for f in files:
				movienamer.process_file(f,args)
	except KeyboardInterrupt, e:
		pass
	except Exception, e:
		pickle.dump(searches, open(os.path.expanduser('~/.movienamer.cache'),'w'))
		raise
	pickle.dump(searches, open(os.path.expanduser('~/.movienamer.cache'),'w'))

if __name__ == "__main__":
	main()

# vim: set sw=8 tabstop=8 softtabstop=8 noexpandtab :
