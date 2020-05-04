#!/usr/bin/env python

import argparse
import copy
import csv
import fnmatch
import json
import os
import string
import sys


# config = {
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

config = {}

# Functions to retrieve bids tsv header values for a given frame and event in that frame

def get_item_fn(item, default):
    '''
    Wrapper to quickly make configurable functions to get bids header values
    '''
    def get_item(frame, event):
        if not config.get(item):
            return frame.get(default.format(event), config.get('null_output', 'n/a'))
        elif event in config[item]:
            return frame.get(config[item].replace('{event}', '{}').format(event), config.get('null_output', 'n/a'))
        else:
            return frame.get(config[item], config.get('null_output', 'n/a'))
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
            return config.get('null_output', 'n/a')
    else:
        return config.get('null_output', 'n/a')

def get_response_time(frame, event):
    return frame.get('{0}.RT'.format(event), config.get('null_output', 'n/a'))

def get_correct(frame, event):
    resp = get_response(frame, event)
    cresp = get_correct_response(frame, event)
    if resp != config.get('null_output', 'n/a') and cresp != config.get('null_output', 'n/a'):
        return resp == cresp
    else:
        return config.get('null_output', 'n/a')

def get_stim_gen(stim_prop):
    '''
    Wrapper so that the function takes the same arguments as the other methods
    '''
    def get_stim(frame, event):
        return frame.get(stim_prop, config.get('null_output', 'n/a'))
    return get_stim

def check_for_stim():
    '''
    Adds stim properties to the closure dictionary and Properties list for the header
    '''
    if config.get('stimuli'):
        MY_PROPS['stim_file'] = get_stim_gen(config['stimuli'])
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

    result = float(frame[key])

    delta = config.get('offsetDelta', 0)
    return result + delta

def fix_time_for_single_event(frame, event, offset, time_props):
    '''
    Use the offset to correct the time properties that need to be corrected
    '''
    for offset_time_prop in time_props['offset']:
        key = '{0}.{1}'.format(event, offset_time_prop)
        if key in frame:
            frame[key] = str((float(frame[key]) - offset)/1000.0)

    for non_offset_time_prop in time_props['nonOffset']:
        key = '{0}.{1}'.format(event, non_offset_time_prop)
        if key in frame:
            frame[key] = str(float(frame[key])/1000.0)

def raw_to_bids_runs(frames):
    '''
    converts the raw frames to runs of bids frames
    '''
    runs = []
    run_index = -1
    offset = None
    offset_time_props = ['OffsetTime', 'OnsetTime']+['RTTime' for i in [0] if config.get('response_time')]
    non_offset_time_props = ['RT', 'Duration', 'OnsetToOnsetTime']
    time_props = {'offset': offset_time_props, 'nonOffset': non_offset_time_props}
    for frame in frames:
        present_events = []
        key = '{0}.OffsetTime'.format(config.get('initialScannerEvent'))
        if key in frame or (not config.get('initialScannerEvent') and offset is None):
            runs.append([])
            run_index += 1
            if config.get('initialScannerEvent'):
                present_events = [config.get('initialScannerEvent')]
                offset = get_initial_offset(frame, key, config)
                fix_time_for_single_event(frame, config.get('initialScannerEvent'), offset, time_props)
            else:
                present_events = [event for event in config['events'] if "{}.".format(event) in string.join(frame.keys(), '||')]
                offset = 0
        elif offset is not None:
            present_events = [event for event in config['events'] if "{}.".format(event) in string.join(frame.keys(), '||')]
            for event in present_events:
                fix_time_for_single_event(frame, event, offset, time_props)
        for event in present_events:
            bids_frame = {}
            for bids_key, closure in MY_PROPS.items():
                bids_frame[bids_key] = closure(frame, event)
            runs[run_index].append(bids_frame)
    return runs

def to_tsv(bids_frames, out_file):
    '''
    Writes the bids frames to a csv
    '''
    with open(out_file, 'wb') as csvfile:
        writer = csv.DictWriter(csvfile, MY_PROP_KEYS, dialect=csv.excel_tab)
        writer.writeheader()
        for bids_frame in bids_frames:
            writer.writerow(bids_frame)

def get_output_filenames(input_filename, number_of_bids_runs, custom_filename=None):
    output_filenames = []
    output_file_basename = input_filename
    if custom_filename:
        output_file_basename = custom_filename
    if number_of_bids_runs > 1:
        first_run = config.get('start_run', 0)
        output_filenames = ['{}_run-{}.tsv'.format(output_file_basename[:-4], i) for i in range(first_run, first_run+number_of_bids_runs)]
    else:
        output_filenames = ['{}.tsv'.format(output_file_basename[:-4])]
    return output_filenames

if __name__ == '__main__':


    # Gear basics
    input_folder = '/flywheel/v0/input/file/'
    output_folder = '/flywheel/v0/output/'
    print os.listdir('/flywheel/v0/input/file/')
    # Grab the input file path
    input_filename = os.listdir(input_folder)[0]
    filename = os.path.join(input_folder, input_filename)

    CONFIG_PATH = '/flywheel/v0/config.json'
    print "Reading configurations..."
    configs = {}
    with open(CONFIG_PATH) as config_file:
        job_config = json.load(config_file)
    configs = job_config['inputs'].get('LogConfig', {}).get('value', {})
    ks = configs.keys()
    for k in ks:
        if fnmatch.fnmatch(input_filename, "*{}*".format(k)):
            config = configs[k]

    if not config or not isinstance(config, dict):
        print "Valid config not found for task {} in project.info.context.LogConfig".format(input_filename)
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

    if not config.get('response_time'):
        MY_PROP_KEYS.remove('response_time')
        MY_PROPS.pop('response_time')
    if not config.get('trial_type'):
        MY_PROP_KEYS.remove('trial_type')
        MY_PROPS.pop('trial_type')

    check_for_stim()
    print "Extracting frames..."
    if filename[-4:].lower() == '.txt':
        raw_frames = extract_frames(filename)
    else:
        raw_frames = extract_frames_from_csv(filename, config.get('skip-rows', 0), config.get('csv_null_values', ['', 'NULL']))

    print "Converting frames..."
    bids_runs = raw_to_bids_runs(raw_frames)
    print "Found {} runs".format(len(bids_runs))

    output_filenames = get_output_filenames(input_filename, len(bids_runs), custom_filename=job_config.get('config', {}).get('Filename'))

    for i, run in enumerate(bids_runs):
        to_tsv(run, os.path.join(output_folder, output_filenames[i]))
        print 'Created {}'.format(os.path.join(output_folder, output_filenames[i]))
