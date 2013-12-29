#!/usr/bin/env python

import os,sys,time
import re,pickle

import tmdb
import yaml

class Movienamer:
    def __init__(self, config):
        self.config = config

        newdir = self.c('movienamer/move-to')
        if newdir:
            self.newdir = newdir
            print "Moving renamed files to %s" % newdir
        else:
            self.newdir = None

        blacklist = self.c('movienamer/blacklist')
        if blacklist:
            self.blacklist = blacklist
            print "Loaded blacklist: %s" % ",".join(blacklist)
        else:
            self.blacklist = []

        filetypes = self.c('movienamer/filetypes')
        if filetypes:
            self.filetypes = filetypes
        else:
            self.filetypes = ['avi','mp4','mkv','m4v','mpg','mpeg','iso','ogm']

        othertypes = self.c('movienamer/othertypes')
        if othertypes:
            self.othertypes = othertypes
        else:
            self.othertypes = ['srt']

        if self.c('tmdb/cachefile'):
            self.tmdb_cachefile = self.c('tmdb/cachefile')
        else:
            path = '~/.movienamer/searches.cache'
            self.tmdb_cachefile = os.path.expanduser(path)

        if os.path.exists(self.tmdb_cachefile):
            self.tmdb_cache = pickle.load(open(self.tmdb_cachefile))
            print "Loaded cache file: %s" % self.tmdb_cachefile
        else:
            self.tmdb_cache = {}

    def c(self, key):
        if not self.config:
            return None

        config = self.config
        key = key.split('/')
        try:
            for i in key:
                config = config[i]
            return config
        except:
            return None

    def save_cache(self):
        folder = os.path.dirname(self.tmdb_cachefile)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        pickle.dump(self.tmdb_cache, open(self.tmdb_cachefile,'w'))

    def search(self, movie, year=None):
        attempts = 3
        backoff = 5

        if year == None:
            index = movie
        else:
            index = movie+year
        if index in self.tmdb_cache:
            res = self.tmdb_cache[index]
            print 'Using cached result'
            return res
        else:
            for i in xrange(attempts):
                try:
                    movie = movie.encode('utf-8')
                    res = tmdb.search(movie,year)
                    self.tmdb_cache[index] = to_unicode(res)
                    self.save_cache()
                    return res
                except Exception, e:
                    raise

    def gen_clean_name(self, name):
        name = name.lower()

        # remove stuff after the first square bracket
        name = re.sub(r'\[.*','',name)
        name = splitter(name, ['(','[','{','www.'])[0]

        # remove junk characters
        name = re.sub('[\.\,;_]+',' ',name)

        # only remove a dash if there is whitespace on
        # at least one side of it
        name = re.sub('( -|- )',' ',name)

        # remove blaclisted words
        for i in self.blacklist:
            # the space ensures the term is not part of a word
            i = " %s" % i.lower()
            if i in name:
                name = name.partition(i)[0]

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
    def build_name(self, name, year=None):
        name = self.prepare_name(name)

        if year != None:
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

    def rename(self, olddir, oldname, newname, extensions, newdir=""):
        if newdir == "":
            newdir = olddir

        if oldname == newname and olddir == newdir:
            p('New and old names match. No renaming required','green')
            return

        for i in extensions:
            filename = newname+i.lower()
            if os.path.exists(os.path.join(newdir, filename)):
                p('Error: Rename will overwrite file "%s"!' % filename, 'red')
                return

        for i in extensions:
            old='%s.%s' % (oldname, i)
            new='%s.%s' % (newname, i.lower())
            p("Renaming '%s' -> '%s'" % (old,new), 'green')
            os.rename(os.path.join(olddir,old),os.path.join(newdir,new))

    def process_file(self, f, newdir=None, search_year=None):
        """Return the guessed name of a movie file"""

        if newdir:
            print "Moving renamed files to %s" % newdir

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
        if ext.lower() not in self.filetypes:
            p('Warning: Unknown extension "%s", ignoring' % f,'yellow')
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
                    if ext in self.filetypes:
                        p('Error: multiple video files named "%s"!' % name,
                                'red')
                        return
                    if ext in self.othertypes:
                        p('Found extra file to rename "%s"' % (i))
                        extensions.append(ext)

        # take a copy of the original name
        clean_name = oldname

        # deal with release year
        if search_year:
            year = search_year
            print "Using specified date: %s" % year
        else:
            year = self.get_date(oldname)
            if type(year) == type([]):
                p('Error: Found multiple dates in filename! ' \
                        'Use --search-year to provide the correct one',
                        'red')
                return
        if year == None:
            print 'Can\'t find release date in filename! ' \
                    'Use --search-year to provide it'
        else:
            # remove year from name for searching purposes
            clean_name = clean_name.replace(year,'')

        clean_name = self.gen_clean_name(clean_name)

        # fetch results
        if year != None:
            print 'Searching for "%s" with year %s' % (clean_name, year)
        else:
            print 'Searching for "%s"' % (clean_name)
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

        if self.newdir == None \
                and newdir == None \
                and self.prepare_name(oldname) == self.build_name( \
                results[0]['title'],results[0]['release_date'][:4]):
            p('First result matches current name, skipping renaming','green')
            return

        for i, res in enumerate(results):
            title = res['title']
            url = "http://www.themoviedb.org/movie/%s" % res['id']
            if 'release_date' in res and res['release_date'] != None:
                release_date = res['release_date'][:4]
                print "\t%d - %s (%s): %s" % (i+1, title, release_date, url)
            else:
                print "\t%d - %s: %s" % (i+1, title, url)
        answer = raw_input("Result?: ")
        if re.match('[1-9][0-9]*',answer):
            res = results[int(answer)-1]
            if not ('release_date' in res):
                p('No release year for %s' % res['name'],'yellow')
                return

            title = res['title']
            if 'release_date' in res:
                date = res['release_date'][:4]
            else:
                date = None
            newname = self.build_name(title,date)
            if newdir != None:
                self.rename(directory, oldname, newname, \
                        extensions, newdir)
            elif self.newdir != None:
                self.rename(directory, oldname, newname, \
                        extensions, self.newdir)
            else:
                self.rename(directory, oldname, newname, extensions)

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
            '--move-to',
            dest='move_to',
            action='store',
            help="Directory to move renamed files to",
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

    config_path = os.path.expanduser('~/.movienamer/config.yaml')
    if os.path.exists(config_path):
        config = yaml.safe_load(open(config_path))
    else:
        print "No config file found"
        config = None

    try:

        if args.recursive:
            file_args = args.Files
            files = []
            for f in file_args:
                if not os.path.isdir(f):
                    continue
                for i in os.walk(f):
                    for j in sorted(i[2]):
                        p = os.path.join(i[0],j)
                        files.append(p)
        else:
            files = args.Files

        movienamer = Movienamer(config)
        for f in files:
            movienamer.process_file(f,args.move_to,args.search_year)
    except KeyboardInterrupt, e:
        pass

if __name__ == "__main__":
    main()

# vim: set sw=4 tabstop=4 softtabstop=4 expandtab :
