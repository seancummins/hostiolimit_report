#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""
hostiolimit_report.py - Reports per-SG Symmetrix Host IO Limit information

Requirements:
- Python 2.7.x (haven't tested in 3.x, but it might work)
- EMC Solutions Enabler
- SYMCLI bin directory in PATH

"""

import argparse
import subprocess
import sys
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
sys.path.append('/opt/emc/SYMCLI/bin')


def symcli_gentree(command):
    command += ' -output xml_e'
    result = ET.fromstring(subprocess.check_output(command, shell=True))
    return result


def matrix_to_string(matrix, header=None):
    # Stolen from http://mybravenewworld.wordpress.com/2010/09/19/print-tabular-data-nicely-using-python/
    """
    Return a pretty, aligned string representation of a nxm matrix.

    This representation can be used to print any tabular data, such as
    database results. It works by scanning the lengths of each element
    in each column, and determining the format string dynamically.

    @param matrix: Matrix representation (list with n rows of m elements).
    @param header: Optional tuple or list with header elements to be displayed.
    """
    if type(header) is list:
        header = tuple(header)
    lengths = []
    if header:
        for column in header:
            lengths.append(len(column))
    for row in matrix:
        for column in row:
            i = row.index(column)
            column = str(column)
            cl = len(column)
            try:
                ml = lengths[i]
                if cl > ml:
                    lengths[i] = cl
            except IndexError:
                lengths.append(cl)

    lengths = tuple(lengths)
    format_string = ""
    for length in lengths:
        format_string += "%-" + str(length) + "s   "
    format_string += "\n"

    matrix_str = ""
    if header:
        matrix_str += format_string % header
    for row in matrix:
        matrix_str += format_string % tuple(row)

    return matrix_str


### Define and Parse CLI arguments
parser = argparse.ArgumentParser(description='Reports FASTVP information per Symmetrix Device.')
rflags = parser.add_argument_group('Required arguments')
rflags.add_argument('-sid',      required=True, help='Symmetrix serial number')
sflags = parser.add_argument_group('Additional optional arguments')
sflags.add_argument('-csv',                help='Flag; Outputs in CSV format', action="store_true")
args = parser.parse_args()

# Capture SG data in ET tree
sgtree = symcli_gentree('symsg -sid %s list -v' % args.sid)

### Put SG information into data structure
# sg{ '<sgname>' :
#                     { 'sgname'     : '<sgname>',
#                       'hiol_status'   : '<None|Defined>',
#                       'hiol_mbps'   : '<None|Defined>',
#                       'hiol_iops'   : '<None|Defined>'
#                     }
#   }
sgdata = dict()

# Iterate through all Storage Groups, capturing membership information and adding SG names to tdevdata
for elem in sgtree.iterfind('SG'):
    sg_name = elem.find('SG_Info/name').text
    sg_hiol_status = elem.find('SG_Info/HostIOLimit_status').text
    sg_hiol_mbps = elem.find('SG_Info/HostIOLimit_max_mb_sec').text
    sg_hiol_iops = elem.find('SG_Info/HostIOLimit_max_io_sec').text
    sgdata[sg_name] = dict()
    sgdata[sg_name]['sgname'] = sg_name
    sgdata[sg_name]['hiol_status'] = sg_hiol_status
    sgdata[sg_name]['hiol_mbps'] = sg_hiol_mbps
    sgdata[sg_name]['hiol_iops'] = sg_hiol_iops



# Build the report table
report = list()

header = ['SGName', 'HIOL_Status', 'IOPS', 'MB/sec']

for sg in sgdata.values():
    row = (sg['sgname'], sg['hiol_status'], sg['hiol_iops'], sg['hiol_mbps'])
    report.append(row)

if args.csv:
    print(','.join(header))
    for row in report:
        print(','.join(str(x) for x in row))
else:
    print(matrix_to_string(report, header))
