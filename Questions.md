# Questions #

### INSTALL/UNINSTALL ON WINDOWS ###

OK, there is no real install/uninstall program. You simply extract the files to a desired directory and then run the binary file in there. It's basically just a .zip file that runs by itself. When you want to uninstall you simply delete this directory. I've heard that some retardation (Vista?) causes the files to be unzipped directly to your desktop by default if you don't specify another directory. Don't do this. Add another directory at the end so you'll get a folder instead. Or if you have no idea what I'm talking about here, just type in c:\amphetype\ in the 'installation' box, and then click Start -> Run and type in the same there. You should get a window showing you the installed files.

### How do I type an entire book? ###

  1. First you might like to go to [Project Gutenberg](http://www.gutenberg.org/wiki/Main_Page) and find a good book to type. Short books with little dialogue are probably the most convenient. Open it up in an editor and remove the Gutenberg legalese at the start and end. Save it as a UTF-8 file.
  1. Now goto the **Sources** tab in Amphetype,
  1. import it,
  1. put _In Order_ as your text selection method,
  1. expand the your text in the list and double-click the first text.
  1. Once you've typed the first text it will continue to select new texts in order from the book. If you do some lessons or other texts in between you can get back by double-clicking the text where you were last.

### What's the deal with regular expessions on the Source tab? ###

The regular expressions here give you a lot of power and flexibility
with weeding out undesirable text. Let's say you imported a novel, but would like
to practice only on the "clean" fragments without dialogue or weird characters, etc.
Then you can select the source, and enter `[^a-zA-Z0-9,.:;'\s-]`.

This will disable any text which has a character in it which isn't alphanumerical,
whitespace, or any of the common punctuation. Another useful expression is `[A-Z][A-Z]`
which will match any text which contain two capital letters in a row, which would probably
be all-caps chapter headings or such.

### What is viscosity? ###

This is an experimental measurement that's supposed to be the opposite of fluidity, though perhaps not very aptly named. That a word or text has high viscosity does not mean it was typed slowly, but rather that there are uncharacteristic stops and starts in your typing of it. The more "pauses," the higher viscosity. If you type a text striking each key following the exact same pace it will have 0.0 viscosity -- a near impossible feat.

### What's WPM? ###

A "word" is taken to be 5 typed characters. This is a [standard measure](http://en.wikipedia.org/wiki/Words_per_minute). So this measure is really characters per second divided by five.

### The averages do not behave as I expect, what's wrong? ###

An [average](http://en.wikipedia.org/wiki/Average) can be many things,
though most people probably think about [arithmetic mean](http://en.wikipedia.org/wiki/Arithmetic_mean).
Amphetype however uses the [median](http://en.wikipedia.org/wiki/Median) value
for all averages. This is because the distribution of speed, accuracy, and fluidity
is skewed (it has a hard limit on one side and the theoretical infinity on the other),
so the median better represents the central tendency than the mean. Once in a while
you're going to have some real fuck-ups and if the mean was used, those outliers
would affect the average a lot more than most of your other results which is unfair.

### Uhm, concatenate, commingle, what? ###

OK, the lesson generator can be a little opaque, but play with the controls and check out the results and I'm sure you'll figure it out.

Basically, let's say you have words you want to practice: A B C D E F ..

Concatenate 2-word sublists would produce a lesson like: A B A B A B .. C D C D C D .. E F E F .. where the number of repetitions of each 2-word sequence equals the number of copies you chose.

Commingle 4-word sublists w/ 2 copies would produce a lesson like (random mix of A A B B C C D D) (random mix of E E F F G G H H) etc...

### Import is buggered ###

I told you! Make sure you use UTF-8 text format. It **will** choke otherwise. Try opening the files in Notepad (for example) and save them again in UTF-8.

### Is there any functionality to access the raw data? ###

The database file (ends with ".db") is a SQLite3 file, so you can download the SQLite client or any other tool that supports SQLite files, and use it just like any other SQL database, export, import, whatever.

### Separate profiles ###

You can use the Database tab in the latest version (?) to switch between different profiles, even if it is a bit cumbersome. I was planning on an easier interface to this, but see below.

### Hey dude, what's up? (Read: when are you gonna fix everything?) ###

New projects, lost love, depression -- in other words: life. I don't use the program myself anymore, and it is unlikely that I will take up development again unless someone promises to shower me with cocaine and strippers or something like that. The source is there and Python is easy to learn though! Anyone could do it.