cTAKES-compare
==============

cTAKES-compare is a tool for comparing the annotations between two sets of cTAKES output

This tool compares two sets of cTakes output files.
All of the discrepancies between the annotations for a source file are reported.

The output is assumed to have been written to files using the CAS to XML file
consumer. To run, copy each output set into a sub-directory of a single
parent directory. These should be the only sub-directories of the parent
directory.

The '-c' parameter is the absolute or relative path to the parent directory.

Optionally, the tool can also print out the text interval in the source
document that corresponds to any annotations that are missed by one of
the annotation files. This options is enabled if the '-s' parameters is
set to the absolute or relative path to a directory containing the source
documents.


    usage: compare_ctakes.py -c <ctakes output directory> [-s <source directory>]
