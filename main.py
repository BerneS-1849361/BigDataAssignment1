import itertools
import xml.sax


class Pass1(xml.sax.ContentHandler):
    def __init__(self, threshold):
        self.author = ""
        self.authors = []

        self.threshold = threshold
        self.bucketSize = 1000000  # todo make dynamic with memory

        self.authorCount = {}
        self.buckets = [0] * self.bucketSize

    # Call when an element starts
    def startElement(self, tag, attributes):
        self.CurrentData = tag
        if tag == "article":
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
        if tag == "article":
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
        string = ""
        for name in tuple:
            string += name

        string = string.encode('utf-8')
        return int.from_bytes(string, 'little') % self.bucketSize

    # removes all non frequent authors from the authorCount array
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
    def __init__(self, passNr, threshold, bitvector, frequentTuples):
        self.passNr = passNr
        self.frequentTuples = frequentTuples

        self.author = ""

        self.authorTuples = {}
        self.threshold = threshold

        self.bitvector = bitvector

        self.bucketSize = int(10000 / (self.passNr - 1))  # todo make dynamic
        self.buckets = [0] * self.bucketSize

    # Call when an element starts
    def startElement(self, tag, attributes):
        self.CurrentData = tag
        # at the start of an article make the list of authors empty
        if tag == "article":
            self.authors = []

    # Call when an elements ends
    def endElement(self, tag):

        # add author to the list of authors of the article
        if self.CurrentData == "author":
            self.authors.append(self.author)

        # at the start of an article
        if tag == "article":
            if len(self.authors) > 2:
                print("suckit")
            # for each combination of length passNr
            for tuple in list(itertools.combinations(self.authors, self.passNr)):
                string = ""
                frequent = True

                # check if each name is frequent and get the hash of the tuple
                for name in tuple:
                    if name not in self.frequentTuples:
                        frequent = False
                    string += name

                # check if every combination of the tuple is frequent
                for tupleLen in range(1, len(tuple)):
                    for tup in list(itertools.combinations(tuple, tupleLen)):
                        if tup not in self.frequentTuples:
                            frequent = False

                # break if not everything was frequent
                if not frequent:
                    break
                # get index of tuple
                string = string.encode('utf-8')
                index = int.from_bytes(string, 'little') % self.bucketSize

                # check if tuple itself is in a frequent bucket
                if self.bitvector & (1 << index):
                    # if it was in a frequent bucket add it to the tuple count
                    if tuple not in self.authorTuples:
                        self.authorTuples[tuple] = 1
                    else:
                        self.authorTuples[tuple] += 1

        self.CurrentData = ""

    # Call when a character is read
    def characters(self, content):
        if self.CurrentData == "author":
            self.author = content

    # adds 1 to the bucket array where the combinations of length k of the current authors
    # in the author array are hashed to
    def fillBucket(self, k):
        tupleArray = list(itertools.combinations(self.authors, k))
        for tuple in tupleArray:
            index = self.hash(tuple)
            self.buckets[index] += 1

    # hashes the given tuple to a set index
    def hash(self, tuple):
        string = ""
        for name in tuple:
            string += name

        string = string.encode('utf-8')
        return int.from_bytes(string, 'little') % self.bucketSize

    # returns the tuple(s) of authors that wrote the most articles together
    # returns a tuple of a number and an array of tuples of strings
    def getMaxAuthor(self):
        print(self.authorTuples)
        max = (0, [])
        for tuple in self.authorTuples:
            if self.authorTuples[tuple] > max[0]:
                max = (self.authorCount[tuple], [tuple])
            elif self.authorCount[tuple] == max[0]:
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

    # parse file with the first pass
    parser.parse(source)

    handler.filterFrequentAuthors()
    print(handler.getMaxAuthor())

    nhandler = PassN(2, 1, handler.getBucketAsBitvector(), handler.authorCount)
    parser.setContentHandler(nhandler)
    parser.parse(source)

    nhandler.getMaxAuthor()
