Amphetype is a layout-agnostic typing program aimed at people who don't need an on-screen keyboard, but would still like to improve their speed and accuracy.

Some features:

* WPM, accuracy, and viscosity (as the opposite of fluidity) statistics on texts, words, keys, and trigrams. Historical data can be grouped in several different ways (by days, averages of 10, etc.).
* You can generate text fragments to type from Project Gutenberg or any other plain text source to practice typing with your favorite novel. There's even an option that lets you type texts in order, fragment by fragment. Read a book with your fingers!
* Advanced lesson generation: auto-review slow and mistyped words after every text or generate custom lessons to practice problem words, keys, trigrams, etc.
* Graphs!

Proper install is coming. I apologize for the current
mess. It was developed on a Windows machine with few
tools and no internet during a train ride and suffered
a few rewrites so the filenames aren't very descriptive
anymore.


To run, type:

python Amphetype.py


Depends on:

python-qt4  (that is, PyQt 4.3+)

OPTIONAL: py-editdist from http://www.mindrot.org/projects/py-editdist/
 - This latter dependancy is by no means critical and you will
 probably never get to use it. (For fetching words from a wordfile
 that are "similar" to your target words in the lesson generator.)
 If you don't have the module it will just select random words
 instead



