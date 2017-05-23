import os
import os.path
import re
import sqlite3 as sql

units = {
    'kB': 1024,
    'mB': 1024**2,
    'gB': 1024**3,
}


def readtext(*path):
    with open(os.path.join(*path)) as f:
        return f.readline().strip()


def readint(*path):
    with open(os.path.join(*path)) as f:
        return int(f.readline())


def readlines(*path):
    with open(os.path.join(*path)) as f:
        for line in f:
            yield line.rstrip()


def readfields(sep, *path):
    with open(os.path.join(*path)) as f:
        for line in f:
            yield re.split(sep, line)


def loadavg():
    fields = readtext('/proc/loadavg').split()
    var1 = float(fields[0])
    var2 = float(fields[1])
    var3 = float(fields[2])
    
    res =  '{ "loadavg1": '  + str(float(fields[0])) + ', "loadavg10": ' +  str(float(fields[1])) + ', "loadavg5": ' + str(float(fields[2])) + ' }'
    
    with sql.connect("test.db") as con:
        cur = con.cursor()
        cur.execute('''INSERT INTO observations(date_time,type,data)
                        VALUES ((datetime('now','localtime')), "loadavg", ?)''',(res,))
        
        con.commit()
        msg = "Record successfully added"
        print (msg)
    
    return {
        'loadavg1' : float(fields[0]),
        'loadavg5' : float(fields[1]),
        'loadavg10': float(fields[2]),
    }

    con.close()

def cpustats():
    stats = {}

    for fields in readfields('\s+', '/proc/stat'):
        if fields[0].startswith('cpu'):
            stats[fields[0]] = {
                'user'   : int(fields[1]),
                'nice'   : int(fields[2]),
                'system' : int(fields[3]),
                'idle'   : int(fields[4]),
                'iowait' : int(fields[5]),
                'softirq': int(fields[6]),
            }
            
    res = str(stats)
    with sql.connect("test.db") as con:
            cur = con.cursor()
            cur.execute('''INSERT INTO observations(date_time,type,data) 
                            VALUES ((datetime('now','localtime')), "cpustats", ?)''',(res,))
            con.commit()
            msg = "Record successfully added"
            print (msg)

    return stats
    con.close()


def meminfo():
    stats = {}

    for fields in readfields('\s*:\s*', '/proc/meminfo'):
        key = fields[0].strip()
        rhs = fields[1].split()

        if len(rhs) == 1:
            value = int(rhs[0])
        elif len(rhs) == 2:
            value = int(rhs[0]) * units[rhs[1]]

        stats[key] = value

    res = str(stats)
    with sql.connect("test.db") as con:
            cur = con.cursor()
            cur.execute('''INSERT INTO observations (date_time,type,data) 
                            VALUES ((datetime('now','localtime')), "meminfo", ?)''',(res,))
            con.commit()
            msg = "Record successfully added"
            print (msg)

    return stats
    con.close()


def mounts():
    results = {}

    for line in readlines('/proc/mounts'):
        fields = line.split()

        results[fields[1]] = {
            'dev' : fields[0],
            'type': fields[2],
            'attr': fields[3],
        }

    res = str(results)
    with sql.connect("test.db") as con:
            cur = con.cursor()
            cur.execute('''INSERT INTO observations (date_time,type,data) 
                            VALUES ((datetime('now','localtime')), "mounts", ?)''',(res,))
            con.commit()
            msg = "Record successfully added"
            print (msg)

    return results
    con.close()


def uptime():
    fields = readtext('/proc/uptime').split()
    var1 = float(fields[0])
    var2 = float(fields[1])
    
    res =  '{ "idle": '  + str(float(fields[0])) + ', "uptime": ' +  str(float(fields[1])) + ' }'
    
    with sql.connect("test.db") as con:
        cur = con.cursor()
        cur.execute('''INSERT INTO observations(date_time,type,data)
                        VALUES ((datetime('now','localtime')), "uptime", ?)''',(res,))
        
        con.commit()
        msg = "Record successfully added"
        print (msg)

    return {
        'uptime': float(fields[0]),
        'idle': float(fields[1]),
    }


def listblocks():
    return os.listdir('/sys/block')


def blockinfo(block):
    blockpath = os.path.join('/sys/block', block)

    if not os.path.exists(blockpath):
        raise FileNotFoundError()

    blockinfo = {}

    sector_size = readint(blockpath, 'queue/hw_sector_size')
    blockinfo['size'] = readint(blockpath, 'size') * sector_size
    blockinfo['type'] = readtext(blockpath, 'device/type')

    blockinfo['partitions'] = []

    for part in [part for part in os.listdir(blockpath) if part.startswith(block)]:
        partpath = os.path.join(blockpath, part)

        partinfo = {}

        partinfo['start'] = readint(partpath, 'start') * sector_size
        partinfo['size'] = readint(partpath, 'size') * sector_size
        partinfo['ratio'] = partinfo['size'] / blockinfo['size']
        partinfo['partition'] = readint(partpath, 'partition')

        blockinfo['partitions'].append(partinfo)

    blockinfo['partitions'].sort(key=lambda p: p['partition'])

    return blockinfo


def devices():
    devices = []

    for device in os.listdir('/sys/bus/usb/devices'):
        path = os.path.join('/sys/bus/usb/devices', device)

        try:
            devices.append({
                'manufacturer': readtext(path, 'manufacturer'),
                'product'     : readtext(path, 'product'),
                'version'     : readtext(path, 'version'),
                'idProduct'   : readtext(path, 'idProduct'),
                'idVendor'    : readtext(path, 'idVendor'),
            })
        except FileNotFoundError:
            continue

    return devices


def version():
    return readtext('/proc/version')


def hex_to_ipv4(s):
    x = int(s, 16)
    return tuple((x >> (8*i)) & 0xff for i in range(4))


def ipv4_to_str(ip):
    return '.'.join(map(str, ip))


def ip_route():
    results = []

    with open('/proc/net/route') as f:
        # skip header
        header = f.readline().split()
        column = dict((name, i) for i, name in enumerate(header))

        for line in f:
            result = {}

            fields = line.split()

            iface = fields[column['Iface']]
            dest = fields[column['Destination']]
            gateway = fields[column['Gateway']]
            mask = fields[column['Mask']]

            result['iface'] = iface
            result['dest'] = ipv4_to_str(hex_to_ipv4(dest))
            result['gateway'] = ipv4_to_str(hex_to_ipv4(gateway))
            result['mask'] = ipv4_to_str(hex_to_ipv4(mask))

            results.append(result)

    return results
