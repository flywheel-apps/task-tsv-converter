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
#     'skip-rows': 1,
#     'accuracy': '{event}.ACC',
#     'onset': '{event}.OnsetTime',
#     'next_onset': '{Extraevent}.OnsetTime', ie Fix event in Pokemon
#     'csv_null_values': ['', 'NULL'],
#     'null_output': 'n/a',
#     'start_run': 0,
# }

CONFIG = {}

# Functions to retrieve bids tsv header values for a given frame and event in that frame

def get_item_fn(item, default):
    '''
    Wrapper to quickly make configurable functions to get bids header values
    '''
    def get_item(frame, event):
        if not CONFIG.get(item):
            return frame.get(default.format(event), CONFIG.get('null_output', 'n/a'))
        elif event in CONFIG[item]:
            return frame.get(CONFIG[item].replace('{event}', '{}').format(event), CONFIG.get('null_output', 'n/a'))
        else:
            return frame.get(CONFIG[item], CONFIG.get('null_output', 'n/a'))
    return get_item

get_event = get_item_fn('trial_type', 'TrialType')
get_onset = get_item_fn('onset', '{}.OnsetTime')
get_accuracy = get_item_fn('accuracy', '{}.ACC')
get_response = get_item_fn('response', '{}.RESP')
get_correct_response = get_item_fn('correct', '{}.CRESP')

# Should duration error be add/ subtracted from duration?
def get_duration(frame, event):
    duration_key = '{0}.Duration'.format(event)
    onset_to_onset_key = '{0}.OnsetToOnsetTime'.format(event)
    onset = get_onset(frame, event)
    next_onset = get_item_fn('next_onset', '')(frame, event)

    if duration_key in frame:
        return frame[duration_key]
    elif onset_to_onset_key in frame:
        return frame[onset_to_onset_key]
    elif onset and next_onset:
        try:
            return str(float(next_onset) - float(onset))
        except ValueError:
            return CONFIG.get('null_output', 'n/a')
    else:
        return CONFIG.get('null_output', 'n/a')

def get_response_time(frame, event):
    return frame.get('{0}.RT'.format(event), CONFIG.get('null_output', 'n/a'))

def get_correct(frame, event):
    resp = get_response(frame, event)
    cresp = get_correct_response(frame, event)
    if resp != CONFIG.get('null_output', 'n/a') and cresp != CONFIG.get('null_output', 'n/a'):
        return resp == cresp
    else:
        return CONFIG.get('null_output', 'n/a')

def get_stim_gen(stim_prop):
    '''
    Wrapper so that the function takes the same arguments as the other methods
    '''
    def get_stim(frame, event):
        return frame.get(stim_prop, CONFIG.get('null_output', 'n/a'))
    return get_stim

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

def extract_frames_from_csv(filename, skip_rows, null_vals):
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
            frames.append({header[i]:row[i] for i in range(len(row)) if row[i] not in null_vals})
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
    offsetTimeProps = ['OffsetTime', 'OnsetTime']+['RTTime' for i in [0] if CONFIG.get('response_time')]
    nonOffsetTimeProps = ['RT', 'Duration', 'OnsetToOnsetTime']
    timeProps = {'offset': offsetTimeProps, 'nonOffset': nonOffsetTimeProps}
    for frame in frames:
        presentEvents = []
        key = '{0}.OffsetTime'.format(CONFIG.get('initialScannerEvent'))
        if key in frame or (not CONFIG.get('initialScannerEvent') and offset is None):
            runs.append([])
            runIndex += 1
            if CONFIG.get('initialScannerEvent'):
                presentEvents = [CONFIG.get('initialScannerEvent')]
                offset = get_initial_offset(frame, key, CONFIG)
                fix_time_for_single_event(frame, CONFIG.get('initialScannerEvent'), offset, timeProps)
            else:
                presentEvents = [event for event in CONFIG['events'] if "{}.".format(event) in string.join(frame.keys(), '||')]
                offset = 0
        elif offset is not None:
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
    if filename[-4:].lower() == '.txt':
        rawFrames = extract_frames(filename)
    else:
        rawFrames = extract_frames_from_csv(filename, CONFIG.get('skip-rows', 0), CONFIG.get('csv_null_values', ['', 'NULL']))

    print "Converting frames..."
    bidsRuns = raw_to_bids_runs(rawFrames)
    outFilenames = []
    outfilebasename = input_filename
    print "Found {} runs".format(len(bidsRuns))
    if conf.get('config', {}).get('FileName'):
        outfilebasename = conf.get('config', {}).get('FileName')
    if len(bidsRuns) > 1:
        first_run = CONFIG.get('start_run', 0)
        outFilenames = ['{}_run-{}.tsv'.format(outfilebasename[:-4], i) for i in range(first_run, first_run+len(bidsRuns))]
    else:
        outFilenames = ['{}.tsv'.format(outfilebasename[:-4])]
    for i, run in enumerate(bidsRuns):
        to_tsv(run, os.path.join(output_folder, outFilenames[i]))
        print 'Created {}'.format(os.path.join(output_folder, outFilenames[i]))
