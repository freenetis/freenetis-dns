import urllib2
import sys
import traceback
import shutil
import os
import subprocess
import ConfigParser

error = False

class data:
    data = ''
    err = False
    
    def get(self,  url):
        err = ''
        data = ''
        
        try:
            # Try to download data           
            result = urllib2.urlopen(url)
            self.data = result.read()
        except Exception, e:
            self.err = traceback.format_exc(0)
            
        return
        
class zone_file:
    def create_record(self, record, global_ttl):
        r = ''
        if record['name'] == '':
            r = '	'
        else:
            r = record['name']+'	'
            
        if record['ttl'] == '':
            r += '	IN	'
        else:
            r += record['ttl']+'	IN	'
        
        r += record['type']+'	'
        
        if record['type'] == 'MX':
            r += record['param']+'	'
        
        r += record['value']
            
        return r
    
    def create_zone_file(self,  zone_data):
        try:
            file = BIND_FN_ZONES_PATH+'db.'+zone_data['zone']
            print 'Generating '+ file
            f = open(file,  "w")
            try:
                #Write $TTL directive
                if zone_data['ttl'] != '':
                    f.write('$TTL '+str(zone_data['ttl'])+' ; zone default\n')
                    
                # Write SOA record
                f.write('@	IN	SOA	'+zone_data['ns']+'.	'+zone_data['mail']+'.	(\n')
                f.write('					'+str(zone_data['sn'])+' ; serial number\n')
                f.write('					'+str(zone_data['ref'])+' ; refresh\n')
                f.write('					'+str(zone_data['ret'])+' ; retry\n')
                f.write('					'+str(zone_data['ex'])+' ; expire\n')
                f.write('					'+str(zone_data['nx'])+' ; not exist\n')
                f.write('					)\n')
                
                for record in zone_data['records']:
                    f.write(self.create_record(record, str(zone_data['ttl']))+'\n')
            finally:
                f.close()
        except IOError:
            print 'Cannot create zone file'

        return

class named:
    def create_named_file(self, master, slave):
        global error
        try:
            print 'Generating '+BIND_FN_NAMED_PATH
            f = open(BIND_FN_NAMED_PATH,  "w")
            try:
                for zone in master:
                    f.write('zone "'+zone['zone']+'." {\n')
                    f.write('	type master;\n')
                    f.write('	file "'+BIND_FN_ZONES_PATH+'db.'+zone['zone']+'";\n')
                    f.write('	allow-transfer { ')
                    if not zone.has_key('slaves') or not zone['slaves']:
                        f.write('none;')
                    else:
                        for ip in zone['slaves']:
                            f.write(zone['slaves'][ip]+'; ')
                    f.write('};\n')
                    f.write('	allow-query { any;};\n')
                    f.write('};\n\n')
                    
                for zone in slave:
                    f.write('zone "'+zone['zone']+'." {\n')
                    f.write('	type slave;\n')
                    f.write('	file "'+BIND_FN_ZONES_PATH+'sl.'+zone['zone']+'";\n')
                    f.write('	masters { '+zone['master']+';};\n')
                    f.write('	allow-query { any;};\n')
                    f.write('};\n\n')
            finally:
                f.close()
        except IOError:
            print 'Cannot create named file'

        print 'Checking configuration'
        if os.path.exists(BIND_FN_NAMED_PATH):
            code = subprocess.call(['/usr/sbin/named-checkconf', '-z', BIND_FN_NAMED_PATH])
            error = error or code != 0
        else:
            error = True

        return

def reloadServer():
    code = subprocess.call(['/usr/sbin/rndc', 'reload'])
    if code != 0:
        if code < 0:
            print 'Killed by signal', -code
        else:
            print 'Reload failed', code
        return False
    else:
        print 'Done'
    return True

FN_PATH = ''
FN_FULL_PATH = ''
BIND_PATH = ''
BIND_NAMED_PATH = ''
BIND_FN_ZONES_PATH = ''
BIND_FN_NAMED_PATH = ''
BIND_INCLUDE = ''

print '--------------------------------------------------------------------------------'
try:
    config = ConfigParser.ConfigParser()
    config.read("/etc/freenetis/freenetis-dns.conf")
    FN_PATH = config.get('Configuration', 'FN_PATH')
    FN_FULL_PATH = FN_PATH + config.get('Configuration', 'FN_WEBINTERFACE')
    BIND_PATH = config.get('Configuration', 'BIND_PATH')
    BIND_NAMED_PATH = BIND_PATH + config.get('Configuration', 'BIND_NAMED')
    BIND_FN_ZONES_PATH = BIND_PATH + config.get('Configuration', 'BIND_FN_ZONES')
    BIND_FN_NAMED_PATH = BIND_PATH + config.get('Configuration', 'BIND_FN_NAMED')
    BIND_INLCUDE = 'include "' + BIND_FN_NAMED_PATH + '";'
    BIND_FN_ZONES_PATH_BK = BIND_PATH + 'bk.' + config.get('Configuration', 'BIND_FN_ZONES')
    BIND_FN_NAMED_PATH_BK = BIND_PATH + 'bk.' + config.get('Configuration', 'BIND_FN_NAMED')

except:
    print 'Cannot open config file'
    sys.exit()
        
# download config from FreenetIS
print 'Downloading from '+FN_FULL_PATH
downloader = data()
downloader.get(FN_FULL_PATH)

if downloader.err != False:
    print downloader.err
    sys.exit()



config_data = eval(downloader.data)

zf = zone_file()

# back up config
if os.path.exists(BIND_FN_NAMED_PATH):
    print 'Backing up '+BIND_FN_NAMED_PATH+' to ' +BIND_FN_NAMED_PATH_BK
    shutil.move(BIND_FN_NAMED_PATH, BIND_FN_NAMED_PATH_BK)
    
if os.path.exists(BIND_FN_ZONES_PATH):
    print 'Backing up '+BIND_FN_ZONES_PATH+' to '+BIND_FN_ZONES_PATH_BK
    shutil.move(BIND_FN_ZONES_PATH, BIND_FN_ZONES_PATH_BK)
    
os.mkdir(BIND_FN_ZONES_PATH)

if not hasattr(config_data, 'has_key'):
    print 'No data'
    sys.exit()

# create master records
if config_data.has_key('master'):
    master = config_data['master']
    for zone in config_data['master']:
        #create zone file from received data
        zf.create_zone_file(zone)
else:
    master = []
        
# create slave records
if config_data.has_key('slave'):
    slave = config_data['slave']
else:
    slave = []

# set named.conf file
nd = named()
nd.create_named_file(master, slave)

if not BIND_INCLUDE in open(BIND_NAMED_PATH).read():
    try:
        print 'Adding to '+BIND_NAMED_PATH
        f = open(BIND_NAMED_PATH,  "a")
        try:
            f.write(BIND_INCLUDE+'\n')
        finally:
            f.close()
    except IOError:
        print 'Cannot add configuration to NAMED file'

if error:
    print 'Error in configuration - Reverting to previous configuration'
    os.remove(BIND_FN_NAMED_PATH)
    shutil.rmtree(BIND_FN_ZONES_PATH)
    if os.path.exists(BIND_FN_NAMED_PATH_BK):
        shutil.move(BIND_FN_NAMED_PATH_BK, BIND_FN_NAMED_PATH)
    if os.path.exists(BIND_FN_ZONES_PATH_BK):
        shutil.move(BIND_FN_ZONES_PATH_BK, BIND_FN_ZONES_PATH)

reloadServer()

if os.path.exists(BIND_FN_NAMED_PATH_BK):
    os.remove(BIND_FN_NAMED_PATH_BK)
if os.path.exists(BIND_FN_ZONES_PATH_BK):
    shutil.rmtree(BIND_FN_ZONES_PATH_BK)
