import itertools
import xml.sax


class Pass1(xml.sax.ContentHandler):
    def __init__(self, threshold):
        self.author = ""
        self.authors = []

        self.threshold = threshold
        self.bucketSize = 10000 #todo make dynamic with memory

        self.authorCount = {}
        self.buckets = [0] * self.bucketSize

        self.max = (0, [])

    # Call when an element starts
    def startElement(self, tag, attributes):
        self.CurrentData = tag
        if tag == "article" or tag == "inproceedings" or tag == "proceedings" or tag == "book" or \
                tag == "incollection" or tag == "phdthesis" or tag == "mastersthesis" or tag == "www":
            self.authors = []

    # Call when an elements ends
    def endElement(self, tag):
        # if the element is an author, add the author to the author array of the article
        # and add an occurrence to the dictionary
        if self.CurrentData == "author":
            self.authors.append(self.author)
            if self.author in self.authorCount:
                self.authorCount[self.author] += 1
            else:
                self.authorCount[self.author] = 1
        # if the element is an article add the articles combinations to the bucket
        if tag == "article" or tag == "inproceedings" or tag == "proceedings" or tag == "book" or \
                tag == "incollection" or tag == "phdthesis" or tag == "mastersthesis" or tag == "www":
            self.fillBucket(2)
        self.CurrentData = ""

    # Call when a character is read
    def characters(self, content):
        if self.CurrentData == "author":
            self.author = content

    # adds 1 to the bucket array where the combinations of length k of the current authors
    # in the author array are hashed to
    def fillBucket(self,  k):
        tupleArray = list(itertools.combinations(self.authors, k))
        for tuple in tupleArray:
            index = self.hash(tuple)
            self.buckets[index] += 1

    # returns the bucketarray as a vector where a 1 is a frequent bucket
    def getBucketAsBitvector(self):
        bitVec = 0
        count = 0
        for i in self.buckets:
            if i >= self.threshold:
                bitVec |= 1 << count
            else:
                bitVec |= 0 << count
            count += 1
        return bitVec

    # hashes the given tuple
    def hash(self, tuple):
        tuple = sorted(tuple)
        string = ""
        for name in tuple:
            string += name

        string = string.encode('utf-8')
        return int.from_bytes(string, 'little') % self.bucketSize


    def filterFrequentAuthors(self):
        self.authorCount = dict(filter(lambda elem: elem[1] >= self.threshold, self.authorCount.items()))

    # returns the author(s) that wrote the most articles as a tuple of a number and an array of strings
    def getMaxAuthor(self):
        max = (0, [])
        for author in self.authorCount:
            if self.authorCount[author] > max[0]:
                max = (self.authorCount[author], [author])
            elif self.authorCount[author] == max[0]:
                max[1].append(author)
        return max



class PassN(xml.sax.ContentHandler):
    def __init__(self, passNr, threshold, bitvector, frequentAuthors):
        self.passNr = passNr
        self.frequentAuthors = frequentAuthors

        self.author = ""
        self.key = ""

        self.authorTuples = {}
        self.threshold = threshold

        self.bitvector = bitvector

        self.bucketSize = int(1000 / self.passNr)
        self.buckets = [0] * self.bucketSize

    # Call when an element starts
    def startElement(self, tag, attributes):
        self.CurrentData = tag
        if tag == "article" or tag == "inproceedings" or tag == "proceedings" or tag == "book" or \
            tag == "incollection" or tag == "phdthesis" or tag == "mastersthesis" or tag == "www":
            self.authors = []

    def hash(self, tuple):
        string = ""
        for name in tuple:
            string += name

        string = string.encode('utf-8')
        return int.from_bytes(string, 'little') % self.bucketSize

    # Call when an elements ends
    def endElement(self, tag):
        if self.CurrentData == "author":
            self.authors.append(self.author)

        if tag == "article" or tag == "inproceedings" or tag == "proceedings" or tag == "book" or \
                tag == "incollection" or tag == "phdthesis" or tag == "mastersthesis" or tag == "www":
            AuthourCombinationArray = list(itertools.combinations(self.authors, self.passNr))
            for combination in AuthourCombinationArray:
                combination = tuple(sorted(combination))
                string = ""
                frequent = True
                for name in combination:
                    if name not in self.frequentAuthors:
                        frequent = False
                    string += name

                if not frequent:
                    break
                string = string.encode('utf-8')
                index = int.from_bytes(string, 'little') % self.bucketSize
                if self.bitvector & (1 << index):
                    if combination not in self.authorTuples:
                        self.authorTuples[combination] = 1
                    else:
                        self.authorTuples[combination] += 1
                # Add triplets
                for author in self.authors:
                    # If author also wrote on article, and not yet in the tuple
                    if author in self.frequentAuthors and author not in combination:
                        newTuple = combination + tuple(author)
                        index = self.hash(newTuple)
                        self.buckets[index] += 1

        self.CurrentData = ""

    def getBucketAsBitvector(self):
        bitVec = 0
        count = 0
        for i in self.buckets:
            if i >= self.threshold:
                bitVec |= 1 << count
            else:
                bitVec |= 0 << count
            count += 1
        return bitVec

    # Call when a character is read
    def characters(self, content):
        if self.CurrentData == "author":
            self.author = content


    def fillBucket(self, k):
        tupleArray = list(itertools.combinations(self.authors, k))
        for tuple in tupleArray:
            index = self.hash(tuple)
            self.buckets[index] += 1

    def filterFrequentTuples(self):
        self.authorTuples = dict(filter(lambda elem: elem[1] >= self.threshold, self.authorTuples.items()))

    def getMaxTuple(self):
        max = (0, [])
        for tuple in self.authorTuples:
            if self.authorTuples[tuple] > max[0]:
                max = (self.authorTuples[tuple], [tuple])
            elif self.authorTuples[tuple] == max:
                max[1].append(tuple)
        return max


if __name__ == '__main__':
    source = "dblp50000.xml"

    # create an XMLReader
    parser = xml.sax.make_parser()
    # turn off namepsaces
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)

    # override the default ContextHandler
    handler = Pass1(10)
    parser.setContentHandler(handler)

    #parse file with the first pass
    parser.parse(source)
    handler.filterFrequentAuthors()

    print(handler.getMaxAuthor())
    nhandler = PassN(2, 1, handler.getBucketAsBitvector(), handler.authorCount)
    parser.setContentHandler(nhandler)
    parser.parse(source)

    nhandler.filterFrequentTuples()
    print(nhandler.getMaxTuple())
