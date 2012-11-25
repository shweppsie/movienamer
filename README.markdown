# MovieNamer2 #

(c) 2010-current GNU GPL v3

Author: Nathan Overall

Movienamer does exactly as it's name infers. Given the name of any movie file,
movienamer will try to find the most likely movie and rename the file.

# Operation #
At this point the program is very much interactive. Below is an example of the
program running.

```
Loaded blacklist: 720p,1080p,bluray,x264,dvdrip,LiMiTED,HDRip,unrated,brrip,XviD,bdrip,eng,extended
Loaded cache file: /home/nathan/.movienamer/searches.cache

Processing The.Raid.Redemption.2011.BDRip.XviD-MeRCuRY.avi...
Searching for "the raid redemption" with year 2011
Using cached result
	1 - The Raid: Redemption (2011) http://www.themoviedb.org/movie/94329
	Result?: 1
	Renaming 'The.Raid.Redemption.2011.BDRip.XviD-MeRCuRY.avi' -> 'The Raid, Redemption (2011).avi'
```

# Installation #
MovieNamer2 requires Python and themoviedb to run.
Install themoviedb from [here](https://github.com/doganaydin/themoviedb).
Then run

	./movienamer2 --help

