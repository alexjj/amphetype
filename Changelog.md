## 0.17: (sources version) ##

  * ADD: new "sitting" grouping method in performance tab
  * ADD: ability to tune running average used to smooth out graph
  * ADD: ability to set group-by value used for avg-of-last-# and "group by" in performance tab
  * CHANGE: unified "text/lesson" and source selector in performance tab
  * CHANGE: rearranged some items on preferences tab, added links to Settings wiki page
  * FIX: reviews now start out as disabled (considered this a bug)
  * FIX: typer wasn't getting notified properly when you changed the font

## 0.16: 2009-01-01 ##

  * ADD: review lessons auto-generated after every text you type (defaults to off)
  * ADD: ability to set different repeat requirements for texts and lessons
  * ADD: option to **not** record data from lesson into analysis
  * ADD: ability to change database file
  * ADD: database statistics and a way to clean up old/stale data
  * CHANGE: proper about
  * CHANGE: removed all the 's-words from the word lists
  * FIX: some minor/obscure bugs in lesson generation

## 0.15: 2008-12-27 ##

  * OTHER: version hit reddit so I suppose this was my "official" first release
  * ADD: time-scaled / dampened graphs

## 0.14: 2008-12-24 ##

  * CHANGE: ditched the bloated matplotlib dependency just for graph support
  * ADD: tentative graphs drawn in Qt