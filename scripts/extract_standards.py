"""exports a json file summarising WINDOWS std files to PATH_DATA"""

import os, glob
from glass_explore import PATH_STANDARDS,PATH_DATA

import simplejson
my_data = []

files = glob.glob(os.path.join(PATH_STANDARDS,'*.std'))

for file in files:
    d = {}
    with open(file) as f:
        d['filename'] = f.name.split(os.path.sep)[-1]
        while True:
            line = f.readline().strip()
            if line.lower().startswith('standard description'):
                i = line.find(':')
                s = line[i+1:].strip().lower()
                s= s.replace('window','WINDOW')
                s= s.replace('en ','EN ')
                s= s.replace('iso ','ISO ')
                s= s.replace('astm', 'ASTM')
                s= s.replace('smarts', 'SMARTS')
                s= s.replace('nfrc', 'NFRC')
                s= s.replace('radiance', 'Radiance')
                s= s.replace('color', 'colour')
                s =s.replace('consistent with ', '')
                d['description'] = s[0].upper() + s[1:]
                break
        d['notes'] = ''
        d['interesting'] = True
        my_data.append(d)        

json = simplejson.dumps(my_data, indent=4, sort_keys=True)

p= os.path.join(PATH_DATA, "standards.json")
# now write output to a file
dataFile = open(p, "w")
# magic happens here to make it pretty-printed
dataFile.write(json)
dataFile.close()

