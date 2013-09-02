import sys
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
        for thread in threads:
            address = thread.attrib['address']
            if address not in threadsets:
                threadsets[address] = set()
            for msg in thread:
                # drop sms/mms tags into sets organized by address
                # with the desirable side effect of removing EXACT duplicates
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
    root.attrib['count'] = str(len(threadsets))
    try:
        for address, threadset in threadsets.iteritems():
            for msg in threadset:
                root.append(etree.fromstring(msg))
    except:
        return 1

    with open('merged.xml', 'w') as outfile:
        outfile.write(etree.tostring(root, encoding='UTF-8',
                                     xml_declaration=True,
                                     standalone=True))
    return 0


def main(argv):
    if len(argv) < 2:
        print "usage: %s xml_file1 xml_file2 ..." % sys.argv[0]
    return dump(merge(argv[1:]))


if __name__ == '__main__':
    sys.exit(main(sys.argv))