# GLB -> glTF-JSON mit eingebettetem Puffer (damit auch Hosts ohne .glb-Unterstützung die Datei ausliefern)
import sys, json, base64, struct
src, dst = sys.argv[1], sys.argv[2]
d = open(src, 'rb').read(); magic, ver, length = struct.unpack('<III', d[:12]); off = 12; j = None; binchunk = None
while off < length:
    clen, ctype = struct.unpack('<II', d[off:off+8]); body = d[off+8:off+8+clen]; off += 8 + clen
    if ctype == 0x4E4F534A: j = json.loads(body.decode('utf-8'))
    elif ctype == 0x004E4942: binchunk = body
j['buffers'][0]['uri'] = 'data:application/octet-stream;base64,' + base64.b64encode(binchunk).decode()
open(dst, 'w').write(json.dumps(j)); print(dst, len(json.dumps(j)) // 1024, 'KB')
