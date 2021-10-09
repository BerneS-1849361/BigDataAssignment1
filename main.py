
import xml.sax


class AuthorHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.author = ""
        self.key = ""

    # Call when an element starts
    def startElement(self, tag, attributes):
        self.CurrentData = tag
        if tag == "article":
            key = attributes["key"]

    # Call when an elements ends
    def endElement(self, tag):
        if self.CurrentData == "author":
            print("Author: ", self.author)
        self.CurrentData = ""

    # Call when a character is read
    def characters(self, content):
        if self.CurrentData == "author":
            self.author = content

if __name__ == '__main__':
    file1 = open("dblp.txt", "w")

    source = "dblp.xml"

    # create an XMLReader
    parser = xml.sax.make_parser()
    # turn off namepsaces
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)

    # override the default ContextHandler
    handler = AuthorHandler()
    parser.setContentHandler(handler)

    parser.parse(source)

    file1.close()
