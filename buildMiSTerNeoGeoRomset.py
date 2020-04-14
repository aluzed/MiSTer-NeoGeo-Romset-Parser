# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
#       buildMiSTerNeoGeoRomset.py
#       loloC2C - SmokeMonster discord 2019
#-------------------------------------------------------------------------------

import os
import re
import argparse
import zipfile
import xml.etree.ElementTree as ET
from xml.dom import minidom
import shutil

encrypted_roms = {
  "kof98": "kof98h", # Initial kof 98 is encrypted
  "kof98k": "kof98h", # Kof 98 korean
  "kof98a": "kof98h", # Kof 98 alt
  "kof98ka": "kof98h", # Kof 98 korean set 2
  "kof99": "kof99nd", # Kof 99 initial
  "kof99e": "kof99nd",  # Kof 99 earlier
  "kof99h": "kof99nd",  # Kof 99 set 2
  "kof99k": "kof99nd",  # Kof 99 korean
  "kof99p": "kof99nd",  # Kof 99 prototype
  "kof2000": "kof2knd", # Kof 2000 is encrypted
  "kof2000n": "kof2knd", # Kof 2000n is still encrypted
  "kof2001": "kof2k1nd", # Kof 2001 is encrypted
  "kof2001h": "kof2k1nd",  # Kof 2001 alternate
  "kof2002": "kof2k2nd", # Kof 2002 is encrypted
  "kof2002b": "kof2k2nd", # Kof 2002 bootleg
  "kf2k2pls": "kof2k2nd",  # Kof 2002 plus hack
  "kf2k2pla": "kof2k2nd",  # Kof 2002 plus alt hack
  "kf2k2mp": "kof2k2nd",  # Kof 2002 magic plus hack
  "kf2k2mp2": "kof2k2nd",  # Kof 2002 magic plus 2 hack
  "kof2003": "kof2k3nd",  # Kof 2003 initial
  "kof2003h": "kof2k3nd",  # Kof 2003 set 2
  "kf2k3bl": "kof2k3nd",  # Kof 2003 bootleg
  "kf2k3pcb": "kof2k3nd",  # Kof 2003 Jamma
  "kf2k3pl": "kof2k3nd",  # Kof 2004 hack
  "kf2k3upl": "kof2k3nd",  # Kof 2004 ex hack
  "kof2k4se": "kof2k3nd",  # Kof 2004 spe hack
  "kof10th": "kof2k3nd",  # Kof 10th anniversary hack
  "kf10thep": "kof2k3nd",  # Kof 10th anniversary extra plus hack
  "svc": "svcnd", # SNK vs Capcom
  "svcpcb": "svcnd", # SNK vs Capcom Jamma
  "svcpcba": "svcnd", # SNK vs Capcom Jamma set 2
  "svcboot": "svcnd", # SNK vs Capcom Bootleg
  "svcplus": "svcnd", # SNK vs Capcom Plus hack
  "svcplusa": "svcnd", # SNK vs Capcom Plus set 2 hack
  "svcsplus": "svcnd", # SNK vs Capcom Super plus hack
  "samsho5": "samsh5nd", # Samurai Shodown 5 intial
  "samsho5h": "samsh5nd", # Samurai Shodown alt
  "samsho5b": "samsh5nd", # Samurai Shodown 5 bootleg
  "samsh5sp": "samsh5nd",  # Samurai Shodown 5 Spe
  "samsh5spho": "samsh5nd",  # Samurai Shodown 5 Spe alt
  "samsh5sph": "samsh5nd",  # Samurai Shodown 5 Spe less censored
  "rotd": "rotdnd",  # Rage of the dragons initial
  "rotdh": "rotdnd",  # Rage of the dragons alt
  "mslug3": "mslug3nd",  # Metal Slug 3 initial
  "mslug3h": "mslug3nd", # Metal Slug 3 set 2
  "mslug3b6": "mslug3", # Metal Slug 6 hack
  "mslug5": "mslug5nd",  # Metal Slug 5 initial
  "ms5plus": "mslug5nd",  # Metal Slug 5 plus hack
  "mslug5h": "mslug5nd",  # Metal Slug 5 set 2
  "ms5pcb": "mslug5nd",  # Metal Slug 5 Jamma
  "mslug4": "mslug4nd",  # Metal Slug 4 initial
  "ms4plus": "mslug4nd",  # Metal Slug 4 plus hack
  "mslug4h": "mslug4nd",  # Metal Slug 4 set 2
  "matrim": "matrimnd",  # Matrimele initial
  "matrimbl": "matrimnd",  # Matrimele bootleg
  "garou": "garound", # Garou initial
  "garouh": "garound", # Garou set 2
  "garoup": "garound",  # Garou prototype
  "garoubl": "garound",  # Garou bootleg
  "garoun": "garound"  # Garou decrypted C
}

def check_if_encrypted(rom_name):
  if rom_name in encrypted_roms:
    print("Error")
    print(rom_name + " is encrypted, please use : " + encrypted_roms[rom_name] + " instead, and remove " + rom_name + " folder.")
    exit(1)

def parse_args():
	parser = argparse.ArgumentParser(description="extract relevant neogeo rom files and generates romsets.xml file")
	parser.add_argument("-i", "--input_folder", dest="source_folder", required=False, default=".", help="set source folder")
	parser.add_argument("-o", "--output_folder", dest="output_folder", required=False, default=".", help="set output folder")
	return parser.parse_args()

def parse_database():
	db = {}
	root = ET.parse('neogeo-all.db').getroot()
	for software in root.findall('software'):
		db[software.get('name')] = software
	return db

def parse_software(db_entry):
	rom_infos = []
	title = db_entry.find('description')

	rom_infos.append({ 'type': 'romname', 'name':  db_entry.get('name') })
	rom_infos.append({ 'type': 'title', 'name': title.text })

	for data in db_entry.find('part').findall('dataarea'):
		#if any(unsupported in data.get('name') for unsupported in ("mcu", "audiocrypt", "audiocpu", "ymsnd", "ymsnd.deltat")):
		#	continue
		for rom in data.findall('rom'):
			flag = rom.get('loadflag')
			if flag != None and any(f in flag for f in ("fill", "ignore")):
				continue
			if flag == "continue":
				info = {'type': data.get('name'), 'name': rom_infos[-1].get('name'), 'size': rom.get('size'), 'offset': rom.get('offset'), 'flag': True}
			else:
				info = {'type': data.get('name'), 'name': rom.get('name'), 'size': rom.get('size'), 'offset': rom.get('offset'), 'flag': False}
			
			if  info is not None:
				element_found = False
				for item in rom_infos:
					if isinstance(item, dict):
						if (item['name'] == info['name']):
							element_found = True
				
				if element_found is False:
					rom_infos.append(info)

	return rom_infos

def get_software_list(romfiles):
	sl = []
	nb = 0
	for rf in romfiles:
		nb += 1
		if rf.get('flag') is True:
			continue
		if nb & 1 == 0 and rf.get('type') == "maincpu" and int(rf.get('size'), 16) < 0x100000:
			sl.pop()
			sl.append((romfiles[nb-2].get('name'), rf.get('name')))
		else:
			if nb == 1 and rf.get('type') == "maincpu" and rf.get('name')[-3:] == "bin":
				sl.append((rf.get('name'), "rename"))
			else:
				sl.append((rf.get('name'), ""))
	return sl

def copy_zip_software(output_folder, output_name, romfiles, dirpath, filename):
	softpath = os.path.join(dirpath, filename)
	zip_ref = zipfile.ZipFile(softpath, 'r')
	s_list = get_software_list(romfiles)
	for entry in s_list:
		if any(f in entry[0] for f in zip_ref.namelist()) is False:
			print("could not find rom "+entry[0]+" in "+softpath)
			return
		elif entry[1] != "" and entry[1] != "rename" and any(f in entry[1] for f in zip_ref.namelist()) is False:
			print("could not find rom "+entry[1]+" in "+softpath)
			return

	output_path = os.path.join(output_folder, output_name)
	if not os.path.exists(output_path):
		os.makedirs(output_path)

	for entry in s_list:
		if entry[1] == "":
			zip_ref.extract(entry[0], output_path)
		elif entry[1] == "rename":
			f = open(os.path.join(output_path, entry[0]), 'wb')
			f.write(zip_ref.read(entry[0]))
			f.close()
		else:
			f = open(os.path.join(output_path, entry[0]), 'wb')
			f.write(zip_ref.read(entry[0])+zip_ref.read(entry[1]))
			f.close()

	zip_ref.close()

def copy_dir_software(output_folder, romfiles, dirpath, dirname):
	softpath = os.path.join(dirpath, dirname)
	print("found dir at "+softpath)

	s_list = get_software_list(romfiles)
	for entry in s_list:
		print(entry)

	if not os.path.exists(output_folder):
		os.makedirs(output_folder)

def get_sprite_index_by_offset(offset):

  allowed_offset = {
    '0x000000': 64,
    '0x000001': 65,
    '0x200000': 68,
    '0x200001': 69,
    '0x400000': 72,
    '0x400001': 73,
    '0x800000': 80,
    '0x800001': 81,
    '0xc00000': 88,
    '0xc00001': 89,
    '0x1000000': 86,
    '0x1000001': 97,
    '0x1800000': 112,
    '0x1800001': 113,
    '0x2000000': 128,
    '0x2000001': 129,
    '0x3000000': 160,
    '0x3000001': 161
  }

  index = 9999
	
  if offset in allowed_offset:
    index = allowed_offset[offset]

  return index

def get_ymsnd_index_by_offset(offset):
  allowed_offset = {
    '0x000000': 16,
    '0x100000': 18,
    '0x200000': 20,
    '0x300000': 22,
    '0x400000': 24,
    '0x500000': 26,
    '0x600000': 28,
    '0x700000': 30,
    '0x800000': 32,
    '0x900000': 34,
    '0xa00000': 36,
    '0xb00000': 38,
    '0xc00000': 40
  }

  index = 9999

  if offset in allowed_offset:
    index = allowed_offset[offset]

  return index

def generate_romsets_info(folder, software_list):
	if not os.path.exists(folder):
		os.makedirs(folder)

	romsets = ET.Element('romsets')
	altered_rom_type = {'maincpu':'P', 'fixed':'S', 'audiocrypt': 'M', 'audiocpu': 'M', 'ymsnd': 'V', 'sprites': 'C'}

	for entry in software_list:
		romset = ET.SubElement(romsets, 'romset')
		romset.set('name', entry[0])

		rom_list = entry[1]
		rom_cpu_list = []
		rom_fix_list = []
		rom_spr_list = []
		rom_audiocpu_list = []
		rom_ymsnd_list = []

		for rom in rom_list:
			if rom['type'] == "title":
				romset.set('altname', rom['name'].strip())
			if rom['type'] == "maincpu":
				rom_cpu_list.append(rom)
			elif rom['type'] == "fixed":
				rom_fix_list.append(rom)
			elif rom['type'] == "sprites" and rom['flag'] is False:
				rom_spr_list.append(rom)
			elif rom['type'] == "audiocpu" or rom['type'] == "audiocrypt":
				rom_audiocpu_list.append(rom)
			elif rom['type'] == "ymsnd":
				rom_ymsnd_list.append(rom)

		for rom in rom_list:
			if rom['type'] == "sprites" and rom['flag'] is True:
				rom_spr_list.append(rom)

		# maincpu rom files - look for concatenation
		concatenate = False
		rom_size = 0
		for rom in rom_cpu_list:
			rom_size += int(rom.get('size'), 16)

		if len(rom_cpu_list) == 2 and rom_size <= 0x100000:
			concatenate = True

		# maincpu rom files
		index = 4
		for rom in rom_cpu_list:
			offs = rom.get('offset')

			if offs is None or index > 4:
				offs = "0"

			if concatenate is True:
				size = "{0:#x}".format(rom_size)
			else:
				size = rom.get('size')

			if not re.search("neo-sma$", rom.get('name')):
				ET.SubElement(romset, 'file', attrib={	'name': rom.get('name'),
														'type': altered_rom_type.get(rom['type']),
														'index': "{0:d}".format(index),
														'offset': offs,
														'size': size})
				
				# If the first block has an offset, duplicate the line
				if int(rom.get('offset'), 16) > 0 and index == 4:
					index += 2
					ET.SubElement(romset, 'file', attrib={	'name': rom.get('name'),
														'type': altered_rom_type.get(rom['type']),
														'index': "{0:d}".format(index),
														'offset': '0',
														'size': size})
					
				index += 2

		# Check neo-sma
		for rom in rom_cpu_list:
			if re.search("neo-sma$", rom.get('name')):
				size = rom.get('size')
				ET.SubElement(romset, 'file', attrib={	'name': rom.get('name'),
														'type': altered_rom_type.get(rom['type']),
														'index': '',
														'size': size})

		if index < 8:
			index = 8

		# fixed rom files
		for rom in rom_fix_list:
			offset = int(rom.get('offset'), 16)

			if offset > 0:
				index += int(offset / 1024 / 1024)	

			ET.SubElement(romset, 'file', attrib={	'name': rom.get('name'),
													'type': altered_rom_type.get(rom['type']),
													'index': "{0:d}".format(index),
													'offset': rom.get('offset'),
													'size': rom.get('size')})

		# sprites rom files
		for rom in rom_spr_list:
			rom_offs = rom.get('offset')

			if rom['flag'] is False:
				rom_offs = "0"
			else:
				rom_offs = rom.get('size')

			index = get_sprite_index_by_offset(rom.get('offset'))

			ET.SubElement(romset, 'file', attrib={	'name': rom.get('name'),
													'type': altered_rom_type.get(rom['type']),
													'index': "{0:d}".format(index),
													'offset': rom_offs,
													'size': rom.get('size')})


        # audiocpu rom files
		for rom in rom_audiocpu_list:
			rom_offs = rom.get('offset')
			offset = int(rom_offs, 16)
			index = 9

			ET.SubElement(romset, 'file', attrib={	'name': rom.get('name'),
                                                'type': altered_rom_type.get(rom['type']),
                                                'index': "{0:d}".format(index),
                                                'offset': "0",
                                                'size': rom.get('size')})

        # ymsnd rom files    
		for rom in rom_ymsnd_list:
			index = get_ymsnd_index_by_offset(rom.get('offset'))

			ET.SubElement(romset, 'file', attrib={	'name': rom.get('name'),
                                                'type': altered_rom_type.get(rom['type']),
                                                'index': "{0:d}".format(index),
                                                'offset': "0",
                                                'size': rom.get('size')})
            

	xml_str = minidom.parseString(ET.tostring(romsets)).toprettyxml(indent="	", encoding='utf8')
	xml_path = os.path.join(folder, "romsets.xml")

	f = open(xml_path, "w")
	f.write(xml_str.decode('utf8'))
	f.close()

if __name__ == '__main__':

	ARGS = parse_args()
	db = parse_database()

	source_folder = os.path.normpath(ARGS.source_folder)
	output_folder = os.path.normpath(ARGS.output_folder)

	software_list = []
	sorted_files = sorted(os.walk(source_folder))
	for dirpath, dirnames, filenames in sorted_files:
		if filenames:
			filenames.sort()
			for f in filenames:
				if f[-4:] == ".zip" and f[:-4] in db:
					rom_infos = parse_software(db.get(f[:-4]))
					software_list.append((f[:-4], rom_infos))
					copy_zip_software(output_folder, f[:-4], rom_infos, dirpath, f)

		if dirnames:
			dirnames.sort()
			for d in dirnames:
				if d in db:
					rom_infos = parse_software(db.get(d))
					software_list.append((d, rom_infos))
					copy_dir_software(output_folder, rom_infos, dirpath, d)

	if len(software_list) > 0:
		generate_romsets_info(output_folder, software_list)
