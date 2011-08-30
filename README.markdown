# MovieRenamer2 #

(c) 2010 GNU GPL v3

Author: Nathan Overall

This is a rewrite of MovieRenamer after it became too unwieldy to work with 
anymore. I will slowly Migrate features from MovieRenamer into MovieRenamer2
and also include various enhancements.

# Installation #
MovieRenamer2 requires Python and themoviedb to run.
Get themoviedb from [here](https://github.com/shweppsie/themoviedb) 
then run ./movierenamer2

# Configuration #
mininuke will read a config file from 
    ~/.movierenamer2rc
of the form below. Below the defaults 
are shown.

    [movierenamer2]

    # a comma separated list of data to be included in the name
    # items that are lists will be appended repeatedly for every
    # item in the list
    naming_scheme="%name%,(%year%),[%keep%]"

    # what to separate the contents of the name with """
    separator=","

    # stuff to store if found in the original filename
    # these should be in match/append pairs (i.e. dvdrip/DVDRip )
    # the match is not case sensitive
    keeplist=""

    # remove from filenames before renaming to make renaming more reliable
    blacklist="dvdscr,xvid,sample,.,-,(,),[,]"
