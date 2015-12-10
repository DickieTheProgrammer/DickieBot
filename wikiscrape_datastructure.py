#!/usr/bin/python
# -*- coding: utf-8 -*-
#  wikiscrape.py

# I've tried reading both raw wiki markup or html and they're both inconsistent.
# This is hard.

from StringIO import StringIO
import pycurl
import requests
import re

# Returns a shortened url from rldn.net
def makeTiny(addr):
        rldnapi = "http://rldn.net/api/"

        buff = StringIO()
        curl = pycurl.Curl()
        curl.setopt(curl.URL,rldnapi+addr)
        curl.setopt(curl.WRITEFUNCTION,buff.write)
        curl.setopt(curl.USERAGENT, 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:8.0) Gecko/20100101 Firefox/8.0')
        curl.perform()

        status,url = buff.getvalue().split()

        if status == '200':
                return url.strip()

        return "status %s - tell mog."

default_search_url = '%sSpecial:Random' # % (baseURL)
wiki_list = [
        (['wiki'],'http://en.wikipedia.org/wiki/','%sSpecial:Search/%s'),
        (['wookie','holocron'],'http://starwars.wikia.com/wiki/','%sSpecial:Search?search=%s'),
        (['mcwiki'],'http://minecraft.wikia.com/wiki/','%sSpecial:Search?search=%s'),
        (['trek'],'http://en.memory-alpha.org/wiki/','%sSpecial:Search?search=%s'),
        (['ooo'],'http://adventuretime.wikia.com/wiki/','%sSpecial:Search?search=%s'),
        (['simple'],'http://simple.wikipedia.org/wiki/','%sSpecial:Search/%s'),
        ]

def wikiScrape(wiki,searchTerm,charLimit=None):
        # this part by shapr
        # uncomfortable use of list comprehension as table lookup
        # also doesn't handle failed lookup well
        urls = [(w[1],w[2]) for w in wiki_list if wiki in w[0]]
        baseURL,search = urls[0] # tuple unpack
        if searchTerm:
                searchURL = search % (baseURL,searchTerm)
        else:
                searchURL = default_search_url % baseURL
        
        # SHOUT OUT TO MY PEEP BRIMSTONE
        searchURL = searchURL.replace(' ','%20')
        r = requests.get(searchURL)
        redirectURL = r.url

        if redirectURL == searchURL:
                return 'Sorry, no article found. Try searching here: {0!s}'.format(makeTiny(redirectURL))

        title = '[' + redirectURL.replace(baseURL,'').replace('_',' ').strip() + '] '

        buff = StringIO()
        curl = pycurl.Curl()
        curl.setopt(curl.URL,redirectURL+'?action=raw')
        curl.setopt(curl.WRITEFUNCTION,buff.write)
        curl.setopt(curl.USERAGENT, 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:8.0) Gecko/20100101 Firefox/8.0')
        curl.perform()

        body = buff.getvalue()

        if re.match('^\#REDIRECT',body):
                return wikiScrape(wiki,body.split('[[')[1].split(']]')[0],charLimit)

        while re.search('\s*\{\{[^\{\}]*\}\}',body)!=None:
                body = re.sub('\s*\{\{[^\{\}]*\}\}','',body) # anything in and including curly brackets - these can be nested
        body = re.sub('\s*\<[^\<]*\>','',body) # html tags
        body = re.sub('\&.*\;',' ',body) # html entities
        body = re.sub("'''?","",body) # ''' or '', sorry for being inconsistent with quotes
        body = re.sub('===?.*=?==','',body) # section headings surrounded by === or ==
        body = re.sub('\[\[(Category|File).*\]\]','',body,flags=re.IGNORECASE) # category tags
        body = re.sub('\[[^\]]*\|','',body) # removes the wiki links section if aliased "[ <stuff here> |"
        body = re.sub('\]|\[','',body) # removes remaining brackets from wiki links
        body = re.sub('\n+\*','; ',body) # Convert \n* delimited elements into ; delimited
        body = re.sub('\:\;',': ',body) # newline immediately preceeding the start of list causes :;

        body = re.sub('\n.*','',body.strip()) # stray newlines
        body = body.strip()

        if charLimit != None:
                tinyURL = ' ...more: {0!s}'.format((makeTiny(redirectURL)))
                charLeft = charLimit - (len(tinyURL) + len(title))

                if charLeft <= 0:
                        return 'charLimit too restrictive'

                index = min(charLeft,len(body))

                return title+body[0:index-1]+tinyURL

        return '{0!s} {1!s}'.format(title, body)