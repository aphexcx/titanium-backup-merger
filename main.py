import sys
import traceback
from lxml import etree

namespaces = {'t': 'http://www.titaniumtrack.com/ns/titanium-backup/messages'}

THREADS_ELEMENT = None


def merge(xmlfiles):
    global THREADS_ELEMENT
    threadsets = {}
    for xmlfile in xmlfiles:
        with open(xmlfile, 'r') as f:
            txt = f.read()
        root = etree.fromstring(txt)
        threads = root.xpath('t:thread', namespaces=namespaces)
        print "Loading %s threads from %s ..." % (len(threads), xmlfile)
        for thread in threads:
            address = thread.attrib['address']
            if address not in threadsets:
                threadsets[address] = set()
            for msg in thread:
                # drop sms/mms tags into sets organized by address
                # with the desirable side effect of ignoring EXACT duplicates
                # (messages that share the same text, date, time, everything)
                threadsets[address].add(etree.tostring(msg))

        # save the 'threads' parent element
        if THREADS_ELEMENT is None:
            for child in root.getchildren():
                root.remove(child)
            THREADS_ELEMENT = root

    return threadsets


def dump(threadsets):
    global THREADS_ELEMENT
    root = THREADS_ELEMENT
    if root is None:
        print "Couldn't load the parent 'threads' element, wrong xml format?"
        return 1
    root.attrib['count'] = str(len(threadsets))
    try:
        for address, threadset in threadsets.iteritems():
            # build up a thread element
            thread_elem = etree.Element('thread')
            thread_elem.attrib['address'] = address
            for msg in threadset:
                # dump all messages into each thread
                thread_elem.append(etree.fromstring(msg))
            root.append(thread_elem)
    except Exception as e:
        print "Error writing merged XML: "
        print traceback.format_exc()
        print e
        return 1

    with open('merged.xml', 'w') as outfile:
        outfile.write(etree.tostring(root, encoding='UTF-8',
                                     xml_declaration=True,
                                     standalone=True))

    print "Done, %s threads saved to merged.xml" % len(threadsets)
    return 0


def main(argv):
    if len(argv) < 2:
        print "usage: %s xml_file1 xml_file2 ..." % sys.argv[0]
        return 1
    return dump(merge(argv[1:]))


if __name__ == '__main__':
    sys.exit(main(sys.argv))