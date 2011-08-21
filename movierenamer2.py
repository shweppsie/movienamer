#!/usr/bin/env python

#import tmdb
import re
import os

def processFile(f,options):
	"""Return the guessed name of a movie file"""

	for i in xrange(len(extensions)):
		if f.endswith(extensions[i]):
			break
		elif i == len(extensions):
			return None
	
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

	# grab the date incase we fail to look it up later
	date = re.findall(r'((20|19)[0-9]{2})',filename)
	if len(date) > 1:
		print "Found %d possible dates" % len(date)

	# remove rubbish from the filename
	#for i in blacklist:
	#	filename = filename.replace(i,' ')
	filename = filename.strip()
	filename = re.sub(' +',' ',filename)

	filename = filename.title()



	#print tmdb.search(filename)

	return True

def configurator():
	import ConfigParser
	config = ConfigParser.RawConfigParser()

	config.add_section('movierenamer2')

	"""
	a comma separated list of data to be included in the name
	items that are lists will be appended repeatedly for every
	item in the list.
	"""
	config.set("naming_scheme","%(name)s (%(year)s)")
	
	"""
	stuff to store if found in the original filename
	these should be in match/append pairs (i.e. dvdrip/DVDRip )
	the match is not case sensitive
	"""
	config.set("keeplist","")
	
	"""
	remove from filenames before analysis to make guesses more
	reliable
	"""
	config.set("blacklist","dvdscr,xvid,sample,.,-,(,),[,]")

	config.read([os.path.expanduser("~/.movierenamer2rc")])

	return config

def main():
	config = configurator()

	import argparse
	parser = argparse.ArgumentParser(description='Correctly Name Movie files')
	parser.add_argument(
			'--naming_scheme',
			default=config.get("movierenamer2","naming_scheme")
			help="Specify the output name scheme"
	parser.add_argument(
			'--naming_scheme_help',
			dest='naming_scheme_help',
			default=False
			help="Print out all the possibilities for naming_scheme"
	parser.add_argument(
			'--keeplist',
			dest='keeplist',
			default=config.get("movierenamer2","keeplist")
			help="List of strings to keep in the name"
	parser.add_argument('File',metavar='FILE',nargs='+',help="Files to rename")
	args = parser.parse_args()

	if args.naming_scheme_help:
		print "Help stuffs"

	for f in args.Files:
		process(f)

if __name__ == "__main__":
	main()

# vim: set sw=8 tabstop=8 softtabstop=8 noexpandtab :
