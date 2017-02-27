from xml.etree import ElementTree as et
import re
import sys


def remove_null(xml_file):
    with open(xml_file, 'r') as f:
        xml_str = f.read()

    # Removes all null-byte characters from xml file #
    xml =  [char for char in xml_str if char != '\x00']
    return ''.join(xml) 


def get_gateway_path(clean_xml):
    root = et.fromstring(clean_xml)
    paths = []
    for elem in root.iter():
        if elem.tag == 'path':
            paths.append(elem.text)
    return paths


def build_abs_path(path):
    print(path.split('@')[1]) 

    if path.split('@')[1] == 'CLIP':
        pass 
    else:     
        abs_path = '/'.join(path.split('/')[:-1])
        filename = path.split('/')[-1].split('@')[0]    
        frame_range = re.findall('\[(\d+)-(\d+)', filename)
        start_frame, end_frame = frame_range[0]
        current_frame = int(start_frame)

        while current_frame != int(end_frame):
            old_path = re.sub('\[\d+-\d+\]', str(current_frame), filename)
            new_path = abs_path, old_path
            #print(''.join(str(new_path)))
            print('/'.join(new_path))
            current_frame += 1

    #print(filename, start_frame, end_frame)
    # Output example -> sq1200_s9.[000101-000119].exr@CLIP #

def main():
    #print('Inside main()')
    xml = remove_null(sys.argv[1])
    #print('printing var "xml" -> {} '.format(xml))
    path = get_gateway_path(xml)
    #print('printing var "path" -> {} '.format(path))
    build_abs_path(path)


if __name__ == '__main__':
    # Makes sure user addes mio file #
    if len(sys.argv) != 2:
        print('Usage: %script xml-file')
        sys.exit(1)
    main()




