import json
names=["Human-Faced Crow","Killer Clown","Floating Spirit","Hanako's Grave","Maze Street","Construction Site","Cat Gathering","Secret Thing","Forest Treasure","Staircase Ghost","Black Dog","Underpass Ghost","Soy Sauce Granny","Shin-Oji Line Curse","Burnt Ruins","Double Suicide","Riverbank Ghost","Mizuko","Walking Old Man","Redevelopment","Park Triplets","Peeping Old Man","Closed Pachinko Parlor","White Will","Yellow Umbrella","Rasen-sama","Fox Spirit","Corpse","Parasite","Sakaue Jizo","Narusawa Estate","Cat Sacrifice","Wishing Camphor Tree","Lizard Hand","Snake Spot","Cursed Antiques","Park Friend","Portrait Artist","Secret Trick","Words of Death","Kurumi's Lost Item","Will-o'-the-Wisp","Courage Test","Hirumi 7 Gods"]
assert len(names)==44
u={}
H=lambda t,**k: dict(t=t,style='hand',**k)
C=lambda t: dict(t=t,style='cap')
P=lambda t: dict(t=t,style='help')
u[28]=H("Crow's Curse"); u[29]=H("Others"); u[30]=H("Where?"); u[31]=H("Go home?"); u[32]=H("Settings")
for k,n in enumerate(names):
    u[33+k]=H(n); u[159+k]=C(n)
u[65]=dict(t=names[32],style='inv')
u[203]=C("Crow's Curse"); u[204]=C("Other Rumors")
hand={97:"Settings",98:"Controls",99:"Basic/Right/Left",100:"Search Sign",101:"Sound / Mark",102:"Text Speed",103:"Fast/Normal/Slow",104:"Vibration",106:"Sound",107:"Mono / Stereo",108:"Volume",109:"Save Icon",110:"Back to Notebook"}
for k,t in hand.items(): u[k]=H(t)
u[99]=H("Basic/Right/Left",segs=[["Basic",2],["/",1],["Right",2],["/",1],["Left",2]])
u[101]=H("Sound/Mark",segs=[["Sound",2],["/",1],["Mark",3]])
u[103]=H("Fast/Normal/Slow",segs=[["Fast",3],["/",1],["Normal",3],["/",1],["Slow",3]])
u[107]=H("Mono/Stereo",segs=[["Mono",4],["/",1],["Stereo",4]])
u[97]=H("Settings",keep_left=12)
helpt={129:"< Normal >",130:"< Left Hand >",131:"< Right Hand >",136:"Move (tap twice: dash / big action)",137:"Look far",138:"Look down",143:"Search / Talk / OK",144:"Cancel",145:"Open notebook",146:"Dash / Big action",149:"Pause",154:"Open map",155:"Zoom map out",156:"Zoom map in",157:"Move right (tap twice: dash / big action)",158:"Move left (tap twice: dash / big action)",
205:"Controller setup",206:"Basic",207:"Right-hand",208:"Left-hand",209:"How search points are signaled",210:"Signal by sound",211:"Signal by mark",212:"Change the message speed",213:"Fast speed",214:"Normal speed",215:"Slow speed",216:"Turn vibration on or off",217:"Vibration on",218:"Vibration off",219:"Choose mono or stereo sound output",220:"Mono output",221:"Stereo output",222:"Adjust the volume",223:"Sound effect volume",224:"Music volume",225:"Choose the save data icon",256:"OK",257:"Cancel"}
for k,t in helpt.items(): u[k]=P(t)
j=json.load(open('translation/ui/eas_text.json'))
j['d002/f542']={str(k):v for k,v in sorted(u.items())}
open('translation/ui/eas_text.json','w').write(json.dumps(j,ensure_ascii=False,indent=1))

# ---- shared buttons, found by pixel hash in every EAS leaf (2026-11-17) ----
import sys, hashlib, mmap
sys.path.insert(0, 'tools'); import eas
P = lambda t: dict(t=t, style='help')
def hsh(d, im): return hashlib.md5(d[im['off']:im['off']+im['size']]).hexdigest()
d3, _ = eas.leaf('d002/f543'); i3 = eas.images(d3)
d2, _ = eas.leaf('d002/f542'); i2 = eas.images(d2)
d1, _ = eas.leaf('d002/f541'); i1 = eas.images(d1)
d6, _ = eas.leaf('d006/f008'); i6 = eas.images(d6)
ref = {hsh(d3, i3[9]): P("Map"), hsh(d3, i3[10]): P("OK"), hsh(d2, i2[257]): P("Cancel"), hsh(d2, i2[256]): P("OK"),
       hsh(d1, i1[120]): P("Switch view"), hsh(d1, i1[121]): P("Larger"), hsh(d1, i1[122]): P("Smaller")}
walk = {31: "Nao's house", 32: "Kurumi's house", 33: "Torizuka gate", 34: "Hirumi Tsukazato", 35: "Hirumi Stn South",
        36: "...start the walk from", 37: "Hirumi City Hall"}
for k, t in walk.items(): ref[hsh(d6, i6[k])] = dict(t=t, style='msg')
f = open('extract/DATA/FILELINK.FLB', 'rb'); m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
for l in open('work/flb_tree.txt'):
    p = l.split()
    try: off = int(p[2], 16); n = int(p[4])
    except: continue
    if m[off:off+3] != b'EAS' or n < 100: continue
    dd = m[off:off+n]
    for im in eas.images(dd):
        if im['size'] and hsh(dd, im) in ref:
            j.setdefault(p[0], {}).setdefault(str(im['i']), ref[hsh(dd, im)])
j['d006/f008']['26'] = P('OK')
S = lambda t: dict(t=t, style='save'); B = lambda t: dict(t=t, style='btn')
j['d012/f000'] = {**j.get('d012/f000', {}), **{
 '11': dict(t='Save', style='hand', keep_left=12), '12': dict(t='/', style='hand'), '13': dict(t=' ', style='hand'),
 '14': dict(t='Day 100', style='hand', bg=14), '16': dict(t='Left', style='hand'), '17': dict(t='Back to Title', style='hand'),
 '18': dict(t='Back', style='hand', bg=14), '19': dict(t='Retry', style='hand'),
 '52': S('Checking the memory card...|Do not remove the memory card'), '53': S('No memory card inserted'),
 '54': dict(t='Insert a memory card|in slot 1 and|press the button', style='msgdark', bg=13),
 '55': S('Overwrite this save?'), '56': S('Not enough free blocks on the card.|Saving needs 2 blocks.'),
 '57': S('Saving...|Do not remove the memory card'), '58': S('Saving failed'), '59': S('Continue without saving?'),
 '60': S('The memory card is not formatted.|Format it now?'), '61': S('Formatting...|Do not remove the memory card'),
 '62': S('Already formatted'), '63': S('Formatting failed'), '64': S('Saving complete'),
 '65': S('Yes (OK) / No (Cancel)'), '66': S('(OK)'), '67': S('(OK) / (Cancel)')}}
W = lambda t, sz=14: dict(t=t, style='ramp', bg=15, ramp=(14, 14, 14), size=sz)
H5 = lambda t: dict(t=t, style='ramp', bg=15, ramp=(7, 10, 13), size=20)
j['d005/f000'] = {'10': W('Su'), '11': W('Mo'), '12': W('Tu'), '13': W('We'), '14': W('Th'), '15': W('Fr'), '16': W('Sa'),
 '17': W('/', 18), '18': W(' '), '31': H5('Left'), '32': H5('d'), '33': H5(':'), '34': H5(' '),
 '35': dict(t='Day 100', style='ramp', bg=14, ramp=(7, 4, 1), size=30)}
j['d011/f000'] = {'0': S("Save today's events?"), '1': B('Save'), '2': B("Don't save"), '4': S('Save your clear data?')}
j['d013/f000'] = {'7': S('This data is cursed.|Purify it?'), '8': B('Purify'), '9': B("Don't purify"),
 '10': S('Purifying...'), '11': S('Purification complete'), '12': S('Save the purified data?'),
 '13': B('Save'), '14': B("Don't save")}
open('translation/ui/eas_text.json', 'w').write(json.dumps(j, ensure_ascii=False, indent=1))
print(len(j), 'leaves,', sum(len(v) for v in j.values()), 'images')

# ---- town map labels, d002/f541 (2026-11-17) ----
A = lambda t, **k: dict(t=t, style='auto', **k)
maplab = {1: 'Old Narusawa', 2: 'Narusawadai', 3: 'Gas Station', 4: 'Asahi Truck Plant', 7: 'Hirumidai High',
 9: 'Hirumidai JHS', 11: 'Police Box', 12: 'Yomogi Nursery', 13: 'Koshu Kaido', 14: 'Hirumidai', 16: 'Hirumidai Estate',
 17: 'Sakanoue Shops', 19: 'Seitokuin Univ.', 20: 'New Hirumidai|Estate (planned)', 22: 'Karikiri Jizo',
 23: 'Shin-Oji Line', 24: 'Concrete Moat St.', 25: 'Hirumidaira Homes', 26: 'Hodo St.', 27: 'Kariin New Homes',
 29: 'Wasaka Shrine', 30: 'Water Bureau', 31: 'Kariin Green No.2', 32: 'Kariin', 34: 'Kariin Elementary',
 35: 'Kariin Park', 37: 'Hirumi Health Bureau', 39: 'Post Office', 41: 'Hirumi City Hall', 42: 'Bowling Alley',
 43: 'Mukaibashi Ave.', 44: 'City Hall St.', 45: 'Wildflower Garden', 46: 'Civic Hall', 47: "Women's U. St.",
 48: 'Station Shops', 49: 'Yokocho St.', 51: 'Police Box', 52: 'NR Hirumi Stn', 53: 'Bus Terminal',
 55: 'Cemetery', 56: 'Honmachi', 58: 'Fire Station', 59: 'Promenade', 61: 'Ito Maternity|Clinic',
 63: 'Eida Hospital', 64: 'Under the Bridge', 65: 'Hirumi-sama', 66: 'Embankment', 67: 'Dobugawa Lane',
 69: 'Redevelopment', 70: 'Tama River', 71: 'Tsukazato Inari', 72: 'Asakawa Canal', 73: 'Hirumi Tsukazato',
 74: 'Reservoir', 75: 'Water Office', 76: 'Tsukazato Golf Center', 78: 'Sakanoue', 79: 'Kurabone St.',
 81: 'Sky Garden', 83: 'Convent', 84: 'Overpass Park', 86: 'Six Jizo', 88: 'Sakaue Jizo',
 90: 'Kusumigahara|Sanatorium'}
j['d002/f541'] = {**j.get('d002/f541', {}), **{str(k): A(t) for k, t in maplab.items()}}
j['d002/f541']['44'] = A('City Hall St.', angle=28)
open('translation/ui/eas_text.json', 'w').write(json.dumps(j, ensure_ascii=False, indent=1))

j['d003/f000'] = {'_disclaimer': ['This game is a work of fiction.', 'Any resemblance to real people', 'or organizations', 'is purely coincidental.']}
open('translation/ui/eas_text.json', 'w').write(json.dumps(j, ensure_ascii=False, indent=1))

# ---- street-name captions in the per-area map snippets, d002/f543-578 (2026-11-17) ----
# keyed by pixel hash of the Japanese image (work/street_keys.json lists where each occurs); names are first-pass guesses
street = {'033d5c':'Hango Hill','0701e7':'Construction Site Rd','0ccbb7':'Twilight Hill',"0d929a":"Nao's House Rd",
 '11b29a':'Ditch Back Rd','12f198':"Kurumi's House Rd",'15f7a4':'Golf Center Rd',"1d18ba":"Women's Univ. Back Rd",
 '1ee829':'Hilltop Jizo','20d7f1':'Stairs by Viaduct','22378f':'Tamagawa Shortcut','23bdc6':'Railway Hill',
 '28a829':'Wildflower Park','32ea44':'Railway Rd','3deb2a':'Health Center Rd','3e76f9':'School Back Rd',
 '4139b2':'Yazu Bridge','41e69b':'Waterworks','44ebb9':'Reservoir N.','484bbb':'Nameless Rd',
 '491db2':"Women's Univ. Rd",'4b6987':'Hirumidaira Housing','522441':'Viaduct Rd','52a4df':'Underpass / Stn West',
 '535849':'Hospital Rd','551df2':'Hirumi Stn South','5f3d0a':'Post Office Rd','606268':'Bowling Alley Rd',
 '608037':'Fire Station Rd','641f65':'Redevelopment / Stn Back Shops','680ffd':'Tsukazato Rd','6e8f39':'School Gate Rd',
 '7394c7':'Shopping St. Side Rd','7baa2c':'Hilltop Shops','7e993f':'Kariin Elem. Back Rd','7f7bdf':'X Hill',
 '880f1d':'Hirumidai Estate','8ebdee':'Tamagawa Bank Rd','900d60':'Reed Field','92ddbe':'Path to Inari',
 '9c999b':'Underpass / Stn East','a1d012':'Miyama Hill Rd','a2c32e':'Campus Rd','a6ca9c':'City Hall Rd',
 'a9ca3b':'Heights Rd','accd8e':'Wa Hill','b0a717':'Police Box Rd','c040a8':'Wa Hill Alley','c45d6c':'Crossing Rd',
 'c9ca98':'Far End Rd','caee58':'Horidome Rd','cedb48':'Kariin Housing Dev.','d2384b':'Convent Rd',
 'd906a8':'Shabby Apt Rd','e47f02':'Temple Rd','ee2465':'Hirumi Stn North','ee4b6a':'Foot of Hirumi Hill',
 'f91df0':'New Housing Area','fb2f74':'Station Shops','fbf065':'Hirumi Bridge','fd153e':'Tsukazato Woods',
 'fd832d':'Office District Rd'}
for n in range(543, 579):
    lf = 'd002/f%03d' % n; dd, _ = eas.leaf(lf); ii = eas.images(dd)
    for i in (15, 16, 17, 18):
        if i >= len(ii): continue
        rows = eas.indices(dd, ii[i]); k = hashlib.md5(bytes(v for r in rows for v in r)).hexdigest()[:6]
        if k in street: j.setdefault(lf, {})[str(i)] = A(street[k])
open('translation/ui/eas_text.json', 'w').write(json.dumps(j, ensure_ascii=False, indent=1))
print('street captions added')
