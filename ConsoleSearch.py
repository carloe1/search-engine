#!/usr/bin/python

import os
import re
import math
import json
import operator
import sys
from nltk.stem import PorterStemmer
from collections import defaultdict
from HTMLParser import HTMLParser


## INDEX ####################################################################
index = defaultdict(dict)
currentFileName = None
documentCount = 0

class WordFrequency():
    def __init__(self):

        self.wordCount = 0
        self.wordSet= defaultdict(int)

        self.title  = defaultdict(int)
        self.header = defaultdict(int)
        self.bold   = defaultdict(int)
        self.strong = defaultdict(int)
        self.body   = defaultdict(int)

    def appendWord(self, word, tag):

        # Stem Word
        stemmer = PorterStemmer()
        word = stemmer.stem(word)

        if tag == None:
            return
        elif tag == "body":
            self.body[word] += 1
        elif tag in ["h1", "h2", "h3"]:
            self.header[word] += 500
        elif tag == "title":
            self.title[word] += 1000
        elif tag == "strong":
            self.strong[word] += 200
        elif tag == "b":
            self.bold[word] += 250

        self.wordCount += 1
        self.wordSet[word] += 1

    def calculateTF(self, word):
        return 1+self.title[word]+ self.header[word]+self.bold[word]+self.strong[word]+self.body[word]


def calculateWeight():
    global index
    for key, value in index.items():
        idf = documentCount / len(value)
        for fileName in value:
            value[fileName] = math.log(value[fileName]) * math.log(idf)


## INDEX JSON FILE ############################################################
INDEX_PATH = "/Users/carloe1/Desktop/cs121_project3/index.json"

def writeIndexFile():
    file = open(INDEX_PATH, "w")

    global index
    print "Writing index file"
    json.dump(index, file)
    print "Done writing index file!"


def readIndexFile():

    global index
    print "Loading index file..."
    json_data = open(INDEX_PATH)
    index = json.load(json_data)
    print "Done loading!"



## HTML FILE PARSING ####################################################
CURRENT_PATH = "/Users/carloe1/Desktop/cs121_project3/WEBPAGES_CLEAN"

class HTMLFileParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.words = WordFrequency()
        self.tags = list()
        self.tags.append(None)
        self.tags.append("title")

    def handle_starttag(self, tag, attrs):
        if tag == "body" and "body" not in self.tags:
            self.tags.pop()
        self.tags.append(tag)
                
    def handle_endtag(self, tag):
        if tag in self.tags:
            self.tags.pop()

    def handle_data(self, data):
        for word in re.split("[^A-Za-z0-9]+", data.rstrip().lower()):
            if word != "":
                self.words.appendWord(word, self.tags[-1])

    def getWords(self):
        return self.words


def parseFile(fileName):
    file = open(fileName, "r")
    fileName = "/".join(fileName.split("/")[-2:])
    currentFileName = fileName
    parser = HTMLFileParser()
    parser.feed(file.read())

    ## add all words from document to the index
    global index
    wordFrequency = parser.getWords()
    for word in wordFrequency.wordSet:
        index[word][currentFileName] = wordFrequency.calculateTF(word)


def parseDocuments():
    # Get the name of all files in current path
    global documentCount
    print "Parsing documents..."
    for root, dirs, files in os.walk(CURRENT_PATH, topdown=False):
        for name in files:
            if "." not in name:
                documentCount += 1
                parseFile(os.path.join(root, name))

    print "Done parsing documents!"
    print "Documents Count: " + str(documentCount)


## QUERY SEARCH #################################################################
BOOKKEEPING_PATH = "/Users/carloe1/Desktop/cs121_project3/WEBPAGES_CLEAN/bookkeeping.json"

def getQueryResults(userInput):

    global index
    stemmer = PorterStemmer()
    results = list() 

    for word in userInput:
        try:
            # Query word is in index
            result = index[stemmer.stem(word)]
        except:
            # Query word is not in index
            result = None
        finally:
            results.append(result)

    return results

def calcualteScores(results):
    fileNames = defaultdict(int)

    for result in results:
        if result != None:
            for fileName, tfidf in result.items():
                fileNames[fileName] += tfidf

    return fileNames

def getUrls(fileNames, data):

    urls = list()
    if len(fileNames) == 0:
            print "No results..."
    else:
        for fileName, tfidf in sorted(fileNames.items(), key = operator.itemgetter(1), reverse=True)[:10]:
            print data[fileName]

def searchQuery():

    global index
    json_data = open(BOOKKEEPING_PATH)
    data = json.load(json_data)
    userInput = None
    
    while True:
        # Ask for user input
        userInput = raw_input("Search: ")
        
        # Check to see if the user wants to quit the program
        if userInput == "quit":
            print "Exit search engine..."
            return

        # Get results for each query word
        results = getQueryResults(userInput.rstrip().split())

        # Calculate the tfidf for all results
        fileNames = calcualteScores(results)

        # Print Top 10 Results
        getUrls(fileNames, data)



## MAIN #################################################################
if __name__ == "__main__":
    
    # Read the index if it exists, otherwise create one
    if os.path.exists(INDEX_PATH):
        readIndexFile()
    else:
        parseDocuments()
        calculateWeight()
        writeIndexFile()
        
    searchQuery()
    



