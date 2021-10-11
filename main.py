import itertools
import xml.sax


class Pass1(xml.sax.ContentHandler):
    def __init__(self, threshold):
        self.author = ""
        self.authors = []

        self.threshold = threshold
        self.bucketSize = 10000

        self.authorCount = {}
        self.buckets = [0] * self.bucketSize

    # Call when an element starts
    def startElement(self, tag, attributes):
        self.CurrentData = tag
        if tag == "article":
            self.authors = []

    # Call when an elements ends
    def endElement(self, tag):
        if self.CurrentData == "author":
            self.authors.append(self.author)
            if self.author in self.authorCount:
                self.authorCount[self.author] += 1
            else:
                self.authorCount[self.author] = 1
        if tag == "article":
            self.fillBucket(2)
        self.CurrentData = ""

    # Call when a character is read
    def characters(self, content):
        if self.CurrentData == "author":
            self.author = content

    def fillBucket(self,  k):
        tupleArray = list(itertools.combinations(self.authors, k))
        for tuple in tupleArray:
            index = self.hash(tuple)
            self.buckets[index] += 1

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

    def hash(self, tuple):
        string = ""
        for name in tuple:
            string += name

        string = string.encode('utf-8')
        return int.from_bytes(string, 'little') % self.bucketSize


    def filterFrequentAuthors(self):
        frequentAuthors = {}
        for author in self.authorCount:
            if self.authorCount[author] >= self.threshold:
                frequentAuthors[author] = self.authorCount[author]
        self.authorCount = frequentAuthors



class PassN(xml.sax.ContentHandler):
    def __init__(self, passCount, threshold, bitvector, frequentAuthors):
        self.passCount = passCount
        self.frequentAuthors = frequentAuthors

        self.author = ""
        self.key = ""

        self.authorTuples = {}
        self.threshold = threshold

        self.bitvector = bitvector

        self.bucketSize = 10000
        self.buckets = [0] * self.bucketSize

    # Call when an element starts
    def startElement(self, tag, attributes):
        self.CurrentData = tag
        if tag == "article":
            self.authors = []

    # Call when an elements ends
    def endElement(self, tag):
        if self.CurrentData == "author":
            self.authors.append(self.author)

        if tag == "article":
            AuthourCombinationArray = list(itertools.combinations(self.authors, self.passCount))
            for combination in AuthourCombinationArray:
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
                    if not combination in self.authorTuples:
                        self.authorTuples[combination] = 1
                    else:
                        self.authorTuples[combination] += 1
        self.CurrentData = ""

    # Call when a character is read
    def characters(self, content):
        if self.CurrentData == "author":
            self.author = content


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

    print(handler.authorCount['Dennis Shasha'])
    handler.filterFrequentAuthors()
    nhandler = PassN(2, 10, handler.getBucketAsBitvector(), handler.authorCount)
    parser.setContentHandler(nhandler)
    parser.parse(source)

    print(nhandler.authorTuples)
