# coding=utf-8
import sys
import traceback

from lxml import etree

namespaces = {'t': 'http://www.titaniumtrack.com/ns/titanium-backup/messages'}

THREADS_ELEMENT = None


class Message(object):
    def __hash__(self):
        return hash((frozenset(self.filteredAttribs.items()), self.element.text))

    def __init__(self, element):
        self.element = element
        self.filteredAttribs = {k: v for k, v in self.element.attrib.iteritems() if k != "serviceCenter"}
        self.string = etree.tostring(self.element)

    def __str__(self):
        return self.string

    def __eq__(self, other):
        return self.filteredAttribs == other.filteredAttribs and self.element.text == other.element.text

    def __ne__(self, other):
        return not self.__eq__(other)


def merge(xmlfiles):
    global THREADS_ELEMENT
    threadsets = {}
    for xmlfile in xmlfiles:
        with open(xmlfile, 'r') as f:
            txt = f.read()
        root = etree.fromstring(txt)
        threads = root.xpath('t:thread', namespaces=namespaces)
        print "Loading %s threads from %s ..." % (len(threads), xmlfile)
        message_count = 0
        added_count = 0
        service_centers = 0
        for thread in threads:
            address = thread.attrib['address']
            if address not in threadsets:
                threadsets[address] = set()
            for sms in thread:
                # drop sms/mms tags into sets organized by address
                # with the desirable side effect of ignoring EXACT duplicates
                # (messages that share the same text, date, time, everything)

                # some messages have a 'serviceCenter' and this can affect de-duplication.
                # if message has a serviceCenter:
                # if message[-serviceCenter] exists in threadset
                # remove it.

                cur = Message(sms)
                message_count += 1

                if 'serviceCenter' not in cur.element.attrib:
                    # if message doesn't have a serviceCenter,
                    # and message[+serviceCenter] exists in threadset
                    if cur in threadsets[address]:
                        # don't add it.
                        print "Skipping adding this message because this same message with a 'serviceCenter' " \
                              "attribute already exists: "
                        print cur.string
                        # print "See?"
                        # print threadsets[address]
                        continue
                else:
                    # if message has a serviceCenter:
                    service_centers += 1
                    if cur in threadsets[address]:
                        # if it exists remove it from the set
                        threadsets[address].remove(cur)
                        added_count -= 1
                        # thus only the message with the serviceCenter attribute will remain in the end
                        print "Removed duplicate message (missing a 'serviceCenter' attribute) and keeping the same " \
                              "message with the attribute: "
                        print cur.string

                added_count += 1
                threadsets[address].add(Message(sms))

        # save the 'threads' parent element
        if THREADS_ELEMENT is None:
            for child in root.getchildren():
                root.remove(child)
            THREADS_ELEMENT = root

        print "%s messages found, %s uniques added (%s with serviceCenters)" % (
        message_count, added_count, service_centers)
    return threadsets


def dump(threadsets):
    global THREADS_ELEMENT
    root = THREADS_ELEMENT
    if root is None:
        print "Couldn't load the parent 'threads' element, wrong xml format?"
        return 1
    root.attrib['count'] = str(len(threadsets))
    message_count = 0
    try:
        for address, threadset in threadsets.iteritems():
            # build up a thread element
            thread_elem = etree.Element('thread')
            thread_elem.attrib['address'] = address
            for Msg in threadset:
                # dump all messages into each thread
                thread_elem.append(Msg.element)
                message_count += 1
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

    print "Done, %s messages in %s threads saved to merged.xml" % (message_count, len(threadsets))
    return 0


def main(argv):
    if len(argv) < 2:
        print "usage: %s xml_file1 xml_file2 ..." % sys.argv[0]
        return 1
    return dump(merge(argv[1:]))


if __name__ == '__main__':
    sys.exit(main(sys.argv))
