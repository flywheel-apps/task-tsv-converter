#!/usr/bin/env python

import argparse
import copy
import csv
import fnmatch
import json
import os
import string
import sys


# CONFIG = {
#     'offsetDelta': 0,
#     'initialScannerEvent': 'DummyFix',
#     'events': [ 'bigface', 'matchface' ],
#     'stimuli': 'bigface',
#     'trial_type': 'TrialType',
#     'response_time': True,
#     'skip-rows': 1
# }

CONFIG = {}

# Functions to retrieve bids tsv header values for a given frame and event in that frame
def get_event(frame, event):
    return frame.get(CONFIG.get('trial_type'), event)

def get_onset(frame, event):
    onset = frame["{}.OnsetTime".format(event)]
    return onset if event in CONFIG['events'] else 'n/a'

# Should duration error be add/ subtracted from duration?
def get_duration(frame, event):
    duration_key = '{0}.Duration'.format(event)
    onset_to_onset_key = '{0}.OnsetToOnsetTime'.format(event)

    if duration_key in frame:
        return frame[duration_key]
    elif onset_to_onset_key in frame:
        return frame[onset_to_onset_key]
    else:
        return 'n/a'

def get_response_time(frame, event):
    return frame.get('{0}.RT'.format(event), 'n/a')

def get_correct(frame, event):
    if frame.get('{}.RESP'.format(event)) or frame.get('{}.CRESP'.format(event)):
        return frame['{}.RESP'.format(event)] == frame['{}.CRESP'.format(event)]
    else:
        return 'n/a'

def get_stim_gen(stim_prop):
    '''
    Wrapper so that the function takes the same arguments as the other methods
    '''
    def get_stim(frame, event):
        return frame.get(stim_prop, 'n/a')
    return get_stim

def get_accuracy(frame, event):
    return frame.get('{}.ACC'.format(event), 'n/a')

def get_response(frame, event):
    return frame.get('{}.RESP'.format(event), 'n/a')

def get_correct_response(frame, event):
    return frame.get('{}.CRESP'.format(event), 'n/a')

def check_for_stim():
    '''
    Adds stim properties to the closure dictionary and Properties list for the header
    '''
    if CONFIG.get('stimuli'):
        MY_PROPS['stim_file'] = get_stim_gen(CONFIG['stimuli'])
        MY_PROP_KEYS.append('stim_file')

def extract_frames(filename):
    '''
    Returns the list of log frames from the .txt
    '''
    frames = []
    with open(filename) as file:
        header = {}
        frame = -1
        for line in file:
            k = line.strip().split(':')
            if not frames and len(k) > 1 and 'Level' not in k[0]:
                header[k[0]] = string.join(k[1:], ':').strip()
            if 'Level: ' in line:
                frames.append(copy.deepcopy(header))
                frame += 1
            if len(k) > 1 and frames:
                frames[frame][k[0]] = string.join(k[1:], ':').strip()
    if len(frames) < 1:
        print "No log frames found, please make sure a valid log file was given."
    return frames

def extract_frames_from_csv(filename, skip_rows):
    '''
    Returns the list of log frames from the .txt
    '''
    frames = []
    with open(filename, 'rb') as file:
        reader = csv.reader(file)
        for i in range(skip_rows):
            reader.next()
        header = reader.next()
        for row in reader:
            if len(row) > len(header):
                print "Row is longer than header."
                return []
            frames.append({header[i]:row[i] for i in range(len(row)) if row[i] != ''})
    return frames

def get_initial_offset(frame, key, config):
    result = 0

    result = int(frame[key])

    delta = config.get('offsetDelta', 0)
    return result + delta

def fix_time_for_single_event(frame, event, offset, timeProps):
    '''
    Use the offset to correct the time properties that need to be corrected
    '''
    for offsetTimeProp in timeProps['offset']:
        key = '{0}.{1}'.format(event, offsetTimeProp)
        if key in frame:
            frame[key] = str((int(frame[key]) - offset)/1000.0)

    for nonOffsetTimeProp in timeProps['nonOffset']:
        key = '{0}.{1}'.format(event, nonOffsetTimeProp)
        if key in frame:
            frame[key] = str(int(frame[key])/1000.0)

def raw_to_bids_runs(frames):
    '''
    converts the raw frames to runs of bids frames
    '''
    runs = []
    runIndex = -1
    offset = None
    offsetTimeProps = ['OffsetTime', 'OnsetTime']+['RTTime' for i in [0] if CONFIG['response_time']]
    nonOffsetTimeProps = ['RT', 'Duration', 'OnsetToOnsetTime']
    timeProps = {'offset': offsetTimeProps, 'nonOffset': nonOffsetTimeProps}
    for frame in frames:
        presentEvents = []
        key = '{0}.OffsetTime'.format(CONFIG.get('initialScannerEvent'))
        if key in frame:
            runs.append([])
            runIndex += 1
            presentEvents = [CONFIG.get('initialScannerEvent')]
            offset = get_initial_offset(frame, key, CONFIG)
            fix_time_for_single_event(frame, CONFIG.get('initialScannerEvent'), offset, timeProps)
        elif offset:
            presentEvents = [event for event in CONFIG['events'] if "{}.".format(event) in string.join(frame.keys(), '||')]
            for event in presentEvents:
                fix_time_for_single_event(frame, event, offset, timeProps)
        for event in presentEvents:
            bidsFrame = {}
            for bidsKey, closure in MY_PROPS.items():
                bidsFrame[bidsKey] = closure(frame, event)
            runs[runIndex].append(bidsFrame)
    return runs

def to_tsv(bidsFrames, outFile):
    '''
    Writes the bids frames to a csv
    '''
    with open(outFile, 'wb') as csvfile:
        writer = csv.DictWriter(csvfile, MY_PROP_KEYS, dialect=csv.excel_tab)
        writer.writeheader()
        for bidsFrame in bidsFrames:
            writer.writerow(bidsFrame)

if __name__ == '__main__':


    # Gear basics
    input_folder = '/flywheel/v0/input/file/'
    output_folder = '/flywheel/v0/output/'
    print os.listdir('/flywheel/v0/input/file/')
    # Grab the input file path
    input_filename = os.listdir(input_folder)[0]
    filename = os.path.join(input_folder, input_filename)

    config = '/flywheel/v0/config.json'

    if config:
        print "Reading configurations..."
        CONFIGS = {}
        with open(config) as configFile:
            conf = json.load(configFile)
        CONFIGS = conf['inputs'].get('LogConfig', {}).get('value', {})
        ks = CONFIGS.keys()
        for k in ks:
            if fnmatch.fnmatch(input_filename, "*{}*".format(k)):
                CONFIG = CONFIGS[k]

    if not CONFIG or not isinstance(CONFIG, dict):
        print "Valid CONFIG not found for task {} in project.info.context.LogConfig".format(input_filename)
        sys.exit(17)

    MY_PROP_KEYS= ['onset', 'duration', 'trial_type', 'response_time',
                   'response', 'correct_response', 'accuracy']
    MY_PROPS = {
        'trial_type': get_event,
        'onset': get_onset,
        'duration': get_duration,
        'response_time': get_response_time,
        'response': get_response,
        'correct_response': get_correct_response,
        'accuracy': get_accuracy
    }

    if not CONFIG.get('response_time'):
        MY_PROP_KEYS.remove('response_time')
        MY_PROPS.pop('response_time')
    if not CONFIG.get('trial_type'):
        MY_PROP_KEYS.remove('trial_type')
        MY_PROPS.pop('trial_type')

    check_for_stim()
    print "Extracting frames..."
    rawFrames = extract_frames(filename) if filename[-4:] == '.txt' else extract_frames_from_csv(filename, CONFIG.get('skip-rows', 0))

    print "Converting frames..."
    bidsRuns = raw_to_bids_runs(rawFrames)
    outFilenames = []
    print "Found {} runs".format(len(bidsRuns))
    if len(bidsRuns) > 1:
        outFilenames = ['{}_run-{}.tsv'.format(input_filename[:-4], i) for i in range(len(bidsRuns))]
    else:
        outFilenames = ['{}.tsv'.format(input_filename[:-4])]
    for i, run in enumerate(bidsRuns):
        to_csv(run, os.path.join(output_folder, outFilenames[i]))
        print 'Created {}'.format(os.path.join(output_folder, outFilenames[i]))
