import itertools
import xml.sax


class AuthorHandler(xml.sax.ContentHandler):
    def __init__(self, threshold):
        self.author = ""
        self.key = ""

        self.authorCount = {}
        self.pairs = []
        self.threshold = threshold

    # Call when an element starts
    def startElement(self, tag, attributes):
        self.CurrentData = tag
        if tag == "article":
            key = attributes["key"]

    # Call when an elements ends
    def endElement(self, tag):
        if self.CurrentData == "author":
            if self.author in self.authorCount:
                self.authorCount[self.author] += 1
            else:
                self.authorCount[self.author] = 1
        self.CurrentData = ""

    # Call when a character is read
    def characters(self, content):
        if self.CurrentData == "author":
            self.author = content

    def generatePairs(self):
        frequentItems = {}
        for key in self.authorCount:
            if self.authorCount[key] >= self.threshold:
                frequentItems[key] = self.authorCount[key]
        self.pairs = itertools.combinations(frequentItems.items(), 2)
        print(len(list(self.pairs)))



if __name__ == '__main__':
    file1 = open("dblp.txt", "w")

    source = "dblp50000.xml"

    # create an XMLReader
    parser = xml.sax.make_parser()
    # turn off namepsaces
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)

    # override the default ContextHandler
    handler = AuthorHandler(10)
    parser.setContentHandler(handler)

    parser.parse(source)
    handler.generatePairs()

    file1.close()
