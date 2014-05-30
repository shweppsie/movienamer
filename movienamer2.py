#!/usr/bin/env python

import os,sys,time
import re,pickle

import tmdb

class Filename:
    def __init__(self, path, name=None, ext=None):
        if ext and not name:
            raise Exception("Cannot use ext without name")
        if ext and name:
            name = "%s.%s" % (name, ext)
        if name:
            self.set_path(os.path.join(path, name))
        else:
            self.set_path(path)

    def __str__(self):
        return self._name

    def set_path(self, path):
        path = to_unicode(path)

        self.set_dir(os.path.dirname(path))
        self.set_name(os.path.basename(path))

    def set_dir(self, directory):
        directory = to_unicode(directory)
        if directory == "":
            directory = "."
        self._dir = directory

        fulldir = self._dir
        fulldir = os.path.expanduser(fulldir)
        fulldir = os.path.abspath(fulldir)
        self._fulldir = fulldir

    def set_name(self, name):
        name = to_unicode(name)
        self._name_name, ext = os.path.splitext(name)
        self._name_ext = ext.lower()
        self._name = "%s%s" % (self._name_name, self._name_ext)

    def get_dir(self):
        return self._dir

    def get_path(self):
        return os.path.join(self._dir, self._name)

    def get_full_path(self):
        return os.path.join(self._fulldir, self._name)

    def get_full_dir(self):
        return self._fulldir

    def get_name(self):
        return self._name

    def get_name_name(self):
        return self._name_name

    def get_name_ext(self, with_dot=True):
        if not with_dot:
            return self._name_ext[1:]
        else:
            return self._name_ext

    def get_human_size(self):
        num = os.path.getsize(self.get_full_path())
        for x in ['bytes','KB','MB','GB']:
            if num < 1024.0 and num > -1024.0:
                return "%3.1f%s" % (num, x)
            num /= 1024.0
        return "%3.1f%s" % (num, 'TB')

class Movienamer:
    def __init__(self, config=None):
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

    def rename(self, oldfile, newfile, extensions):
        if oldfile.get_full_path() == newfile.get_full_path():
            p('New and old names match. No renaming required','green')
            return

        # don't overwrite existing files
        for i in extensions:
            f = Filename("%s.%s" % (newname.get_name_name(),i))
            if os.path.exists(f.get_full_path()):
                p('Error: Rename will overwrite file "%s"!','red')
                p('Remove original to continue' % filename, 'red')
                return

        # check for duplicate video files
        f = []
        for i in os.listdir(newfile.get_full_dir()):
            i = Filename(newfile.get_full_dir(), i)
            # check names match (excl extension) and file type is video
            if i.get_name_name() == newfile.get_name_name() \
                    and i.get_name_ext(False) in self.filetypes:
                f.append(i)
        if len(f) > 0:
            p('Error: Rename will add duplicate file', 'red')
            p('File: %s (%s)' % (oldfile.get_path(), oldfile.get_human_size()))
            p('Duplicates', 'red')
            for i in f:
                p("%s (%s)" % (i.get_name(),i.get_human_size()))
            p('Remove duplicates to continue', 'red')
            return

        # rename files
        extensions.append(newfile.get_name_ext())
        for i in extensions:
            newname = Filename( \
                    newfile.get_full_dir(), \
                    newfile.get_name_name(), \
                    i \
            )
            p("Renaming '%s' -> '%s'" % (oldfile,newname), 'green')
            os.rename(oldfile.get_full_path(),newfile.get_full_path())

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

        filename = Filename(f)

        p('\nProcessing "%s"...' % filename)

        # only process files known video extensions
        ext = filename.get_name_ext(False)
        if ext.lower() not in self.filetypes:
            p('Warning: Unknown extension "%s", ignoring' % f,'yellow')
            return

        # process any extra files
        extensions = []
        for i in os.listdir(filename.get_full_dir()):
            i = to_unicode(i)
            # ensure this isn't the file we're renaming
            if filename.get_name() != i:
                new = Filename(i)
                if new.get_name_name() == filename.get_name_name():
                    if new.get_name_ext(False) in self.filetypes:
                        p('Error: multiple video files named "%s"!' % name,
                                'red')
                        return
                    if new.get_name_ext() in self.othertypes:
                        p('Found extra file to rename "%s"' % (i))
                        extensions.append(new.get_name_ext())

        # take a copy of the original name
        clean_name = filename.get_name_name()

        # deal with release year
        if search_year:
            year = search_year
            print "Using specified date: %s" % year
        else:
            year = self.get_date(filename.get_name_name())
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
            newname = "%s%s" % \
                (self.build_name(title,date), filename.get_name_ext())
            if newdir != None:
                newfile = Filename(os.path.join(newdir, newname))
            elif self.newdir != None:
                newfile = Filename(os.path.join(self.newdir, newname))
            else:
                newfile = Filename(os.path.join(filename.get_path(), newname))
            self.rename(filename, newfile, extensions)

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
    import yaml
    config_path = os.path.expanduser('~/.movienamer/config.yaml')
    if os.path.exists(config_path):
        config = yaml.safe_load(open(config_path))
    else:
        print "No config file found"
        config = None

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
