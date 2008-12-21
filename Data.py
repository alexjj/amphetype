

from __future__ import division, with_statement


from itertools import *
import time
import bisect
import getpass
import sqlite3
import re



def trimmed_average(total, series):
        s = 0.0
        n = 0

        start = 0
        cutoff = total // 3
        while cutoff > 0:
            cutoff -= series[start][1]
            start += 1
        if cutoff < 0:
            s += -cutoff * series[start-1][0]
            n += -cutoff

        end = len(series)-1
        cutoff = total // 3
        while cutoff > 0:
            cutoff -= series[end][1]
            end -= 1
        if cutoff < 0:
            s += -cutoff * series[end+1][0]
            n += -cutoff

        while start <= end:
            s += series[start][1] * series[start][0]
            n += series[start][1]
            start += 1

        return s/n


class Statistic(list):
    def __init__(self):
        super(Statistic, self).__init__()
        self.flawed_ = 0
    
    def append(self, x, flawed=False):
        bisect.insort(self, x)
        if flawed:
            self.flawed_ += 1
    
    def __cmp__(self, other):
        return cmp(self.median(), other.median())
    
    def measurement(self):
        return trimmed_average(len(self), map(lambda x:(x, 1), self))

    def median(self):
        l = len(self)
        if l == 0:
            return None
        if l & 1:
            return self[l // 2]
        return (self[l//2] + self[l//2-1])/2.0

    def flawed(self):
        return self.flawed_





class MedianAggregate(Statistic):
    def step(self, val):
        self.append(val)
 
    def finalize(self):
        return self.median()


class AmphDatabase(sqlite3.Connection):
    def __init__(self, *args):
        super(AmphDatabase, self).__init__(*args)

        self.setRegex("")
        self.resetCounter()
        self.create_function("counter", 0, self.counter)
        self.create_function("regex_match", 1, self.match)
        self.create_aggregate("agg_median", 1, MedianAggregate)
        #self.create_aggregate("agg_trimavg", 2, TrimmedAverarge)
        self.create_function("ifelse", 3, lambda x, y, z: y if x is not None else z)

        try:
            self.fetchall("select * from result,source,statistic,text,mistake limit 1")
        except:
            self.newDB()
    
    def setRegex(self, x):
        self.regex_ = re.compile(x)
    
    def match(self, x):
        if self.regex_.search(x):
            return 1
        return 0

    def counter(self):
        self._count += 1
        return self._count
    def resetCounter(self):
        self._count = -1
    
    def newDB(self):
        self.executescript("""
create table source (name text, disabled integer, discount integer);
create table text (id text primary key, source integer, text text, disabled integer);
create table result (w real, text_id text, source integer, wpm real, accuracy real, viscosity real);
create table statistic (w real, data text, type integer, time real, count integer, mistakes integer, viscosity real);
create table mistake (w real, target text, mistake text, count integer);
create view text_source as
    select id,s.name,text,coalesce(t.disabled,s.disabled)
        from text as t left join source as s on (t.source = s.rowid);
        """)
        self.commit()

    def executemany_(self, *args):
        super(AmphDatabase, self).executemany(*args)
    def executemany(self, *args):
        super(AmphDatabase, self).executemany(*args)
        #self.commit()

    def fetchall(self, *args):
        return self.execute(*args).fetchall()
    
    def fetchone(self, sql, default, *args):
        x = self.execute(sql, *args)
        g = x.fetchone()
        if x is None:
            return default
        return g

    def getSource(self, source, lesson=False):
        v = self.fetchall('select rowid from source where name = ? limit 1', (source, ))
        if len(v) > 0:
            self.execute('update source set disabled = NULL where rowid = ?', v[0])
            self.commit()
            return v[0][0]
        self.execute('insert into source (name,discount) values (?,?)', (source, 1 if lesson else None))
        return self.getSource(source)

dbname = getpass.getuser() or "typer"
if '.' not in dbname:
    dbname += '.db'

# Global entries
DB = sqlite3.connect(dbname,5,0,"DEFERRED",False,AmphDatabase)


#Item = ItemStatistics()


