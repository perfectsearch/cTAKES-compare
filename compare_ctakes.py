#!/usr/bin/python
#
# Copyright 2014 Perfect Search Corporation
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this 
# file except in compliance with the License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under 
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF 
# ANY KIND, either express or implied. See the License for the specific language governing
# permissions and limitations under the License.

import os, sys, getopt




def readcTakesResult(path, filename, cuiDict):
    tagsSet = ['<org.apache.ctakes.typesystem.type.textsem.MedicationMention',
               '<org.apache.ctakes.typesystem.type.textsem.SignSymptomMention',
               '<org.apache.ctakes.typesystem.type.textsem.ProcedureMention',
               '<org.apache.ctakes.typesystem.type.textsem.AnatomicalSiteMention',
               '<org.apache.ctakes.typesystem.type.textsem.DiseaseDisorderMention']

    ontologyRefDict = {}
    umlsConceptDict = {}
    filepath = os.path.join(path, filename )
    f = open(filepath, 'r')
    line = f.readline() # skip <?xml ...> & <CAS ...>
    line = f.readline() # skip <umls.cas.Sofa ...> (including record string)
    line = f.readline() # <org.apache.ctakes.typesystem.type.structured.DocumentID ...
    sourceFile = line.strip().split(' ')[3].split('"')[1]

    line = f.readline().strip() 
    annotationCount = 0
    while line != '':
        parts = line.strip().split(' ')
        if parts[0] in tagsSet:
            begin=parts[4].split('"')[1]
            end=parts[5].split('"')[1]
            ontologyRef = parts[7].split('"')[1]
            ontologyRefDict[ontologyRef] = (begin, end)
        elif parts[0] == '<org.apache.ctakes.typesystem.type.refsem.UmlsConcept':
            id = parts[1].split('"')[1]
            if parts[6].startswith('cui'):
                cui = parts[6].split('"')[1]
                tui = parts[7].split('"')[1]
            else:
                cui = parts[7].split('"')[1]
                tui = parts[8].split('"')[1]
            umlsConceptDict[id] = cui
        elif parts[0] == '<uima.cas.FSArray' and len(umlsConceptDict) > 0:
            ontologyRefId = parts[1].split('"')[1]
            size = int(parts[2].split('"')[1])
            for i in range(0, size):
                line = f.readline().strip()
                umlsConceptId = line.partition('>')[2].partition('<')[0]
                cui = umlsConceptDict[umlsConceptId]
                interval = ontologyRefDict[ontologyRefId]
                intervalList = []
                try:
                    intervalList = cuiDict[cui]
                except:
                    pass
                if interval not in intervalList:
                    annotationCount += 1
                    intervalList.append(interval)
                    cuiDict[cui] = intervalList
            line = f.readline().strip()
            
        line = f.readline().strip()
    return sourceFile, annotationCount
        
def dumpFileInterval(source, intervals):
    for interval in intervals:
        start = int(interval[0])
        end = int(interval[1])
        try:
            source.seek(start)
            snip = source.read(end - start)
            print ("\t%s:%s" % (str(interval), snip))
        except:
            pass

def checkForMissingCui(main, other, othersetname, source):
    missingcount = 0
    matchingcount = 0
    for cui, intervals in main.items():
        try:
            ctakesIntervals = other[cui]
            for interval in intervals:
                if interval not in ctakesIntervals:
                    missingcount += 1
                    print ("%s missing %s at %s" % (othersetname, cui, str(interval)))
                    dumpFileInterval(source, [interval])
                    print("but found at: %s" % str(ctakesIntervals))
                    dumpFileInterval(source, ctakesIntervals)                    
                else:
                    matchingcount += 1
        except:
            missingcount += len(intervals)
            print ("%s missing %s at %s" % (othersetname, cui, str(intervals).strip('[]')))
            dumpFileInterval(source, intervals)
    print ("Matched annotations: %d, Missing annotations: %d" % (matchingcount, missingcount))


    return matchingcount, missingcount



def compareCTakes(pathToCTakesOutput, ctakesResultsList, pathToSource): 

    docCount = 0

    analysisResults = {}


    for dirname, dirnames, filenames in os.walk(os.path.join(pathToCTakesOutput, ctakesResultsList[0])):
        for filename in filenames:
            print ("")
            print ("******* %s *******" % filename )
            docCount +=1


            controlCuiDict = {}
            controlName = ''

            for ctakesResult in ctakesResultsList:
                ctakesCuiDict = {}
                result = readcTakesResult(os.path.join(pathToCTakesOutput, ctakesResult), filename, ctakesCuiDict)
                annotationCount = result[1]
                sourceFileName = result[0]
                sourcePath = os.path.join(pathToSource, sourceFileName)
                source = 0
                try:
                    source = open(sourcePath, 'r')
                except:
                    pass

                print ("%s annotations: %d" % (ctakesResult, annotationCount))
                if controlName == '':
                    controlName = ctakesResult
                if controlName == ctakesResult: 
                    controlCuiDict = ctakesCuiDict
                    results = {}
                    try:
                        results = analysisResults[ctakesResult]
                        results['found'] = results['found'] + annotationCount
                    except:
                        results['found'] = annotationCount
                    analysisResults[ctakesResult] = results
                    continue
                print ("")
                result = checkForMissingCui( controlCuiDict, ctakesCuiDict, ctakesResult, source)
                matchingcount = result[0]
                missingcount = result[1]

                results = {}
                try:
                    results = analysisResults[ctakesResult]
                    results['matched'] = results['matched'] + matchingcount

                    results['missed'] = results['missed'] + missingcount
                    results['found'] = results['found'] + annotationCount
                except:
                    results['matched'] = matchingcount
                    results['missed'] = missingcount
                    results['found'] = annotationCount
                
                analysisResults[ctakesResult] = results

                print ("")

                result = checkForMissingCui(ctakesCuiDict, controlCuiDict, controlName, source)
                matchingcount = result[0]
                missingcount = result[1]

                results = {}
                try:
                    results = analysisResults[ctakesResult]
                    results['matched1'] = results['matched1']  + matchingcount
                    results['missed1'] = results['missed1']  + missingcount
                except:
                    results['matched1'] = matchingcount
                    results['missed1'] = missingcount
                analysisResults[ctakesResult] = results

                print ("")

    print ("")
    print ("")
    print ("Documents analyzed: %d" % (docCount))
    
    print ("")
    print ("")
    print ("Total Annotations Found")
    for key in analysisResults.keys():
        results = analysisResults[key]    
        print ("%s Total annotations Found: %d" % (key, results['found']))

    print ("")
    print ("Comparision with %s" % controlName)

    for key in analysisResults.keys():
        if key == controlName:
            continue
        results = analysisResults[key]
        print ("%s Matched %d annotations, Missed %d annotations" % (key, results['matched'], results['missed']))
        print ("%s Matched %d annotations, Missed %d annotations" % (controlName, results['matched1'], results['missed1']))



def printUsage():
    print ("This tool compares two sets of cTakes output files.")
    print ("All discrepancies between the annotations for a source file are reported.")
    print ("")
    print ("The output is assumed to have been written to files using the CAS to XML file ")
    print ("consumer. To run, copy each output set into a subdirectory of a single ")
    print ("parent directory. These should be the only subdirectories of the parent")
    print ("directory.")
    print ("")
    print ("The '-c' parameter is the absolute or relative path to the parent directory.")
    print ("")
    print ("Optionally, the tool can also print out the text interval in the source")
    print ("document that corresponds to any annotations that are missed by one of")
    print ("the annotation files. This options is enabled if the '-s' parameters is")
    print ("set to the absolute or relative path to a directory containing the source")
    print ("documents.")
    print ("")
    
    print ('usage: compare_ctakes.py -c <ctakes output directory> [-s <source directory>]')



def main(argv):
    pathToSource = ""
    pathToCTakesOutput = ""
    try:
        opts, args = getopt.getopt(argv, "hc:s:", ["ctakesoutput=", "sourcedir="]) 
    except getopt.GetoptError:
        printUsage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            printUsage()
            sys.exit()
        elif opt in ("-c", "--ctakesoutput"):
            pathToCTakesOutput = arg
        elif opt in ("-s", "--sourcedir"):
            pathToSource = arg

    if pathToCTakesOutput == '':
        printUsage()
        sys.exit()
    
    print ("Directory of cTakes outputs: %s" % pathToCTakesOutput) 
    if pathToSource != '':
        print ("Source Directory: %s" % pathToSource)
    
    ctakesResultsList = []
    for dirname, dirnames, filenames in os.walk(pathToCTakesOutput):
        for dir in dirnames:
            ctakesResultsList.append(dir)
    
    
    compareCTakes(pathToCTakesOutput, ctakesResultsList, pathToSource)


if __name__ == "__main__":
    main(sys.argv[1:])
