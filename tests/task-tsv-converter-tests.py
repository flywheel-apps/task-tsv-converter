
import unittest
import task_gen
import shutil
import copy

class TaskGenTestCases(unittest.TestCase):

    def setUp(self):
        self.init_frame = {
            'Group': '1',
            'InitFix.OnsetDelay': '9',
            'SessionTime': '15:30:43',
            'InitFix.OnsetTime': '38345',
            'Run1EventList': '1',
            'VersionPersist': '1',
            'RandomSeed': '-1018970304',
            'InitFix.RT': '0',
            'InitFix.RESP': '',
            'Run1EventList.Cycle': '2',
            'InitFix.OnsetToOnsetTime': '0',
            'Running': 'Run1EventList',
            'trigger': '?',
            'Run1EventList.Sample': '1',
            'InitFix.RTTime': '0',
            'InitFix.ACC': '0',
            'InitFix.DurationError': '-9',
            'DataFile.Basename': 'Pokenogo_jitter-065-1',
            'Level': '3',
            'SessionStartDateTimeUtc': '2/11/2018 8:30:43 PM',
            'Display.RefreshRate': '60.318',
            'Procedure': 'FixateProc',
            'SessionDate': '02-11-2018',
            'Image': 'pokemon/pokeball.bmp',
            'Session': '1',
            'InitFix.CRESP': '',
            'Experiment': 'Pokenogo_jitter',
            'InitFix.OffsetTime': '10',
            'Subject': '065'
        }
        self.event_frame = {
            'Fixcross.OffsetDelay': '0',
            'Group': '1',
            'Fixcross.OnsetDelay': '4',
            'Fixcross.OffsetTime': '54189',
            'Experiment': 'Pokenogo_jitter',
            'SessionTime': '15:30:43',
            'GoImage.RTTime': '0',
            'Run1EventList': '2',
            'Fixcross.CRESP': '',
            'GoImage.RESP': '',
            'VersionPersist': '1',
            'RandomSeed': '-1018970304',
            'Fixcross.OnsetToOnsetTime': '0',
            'Fixcross.RTTime': '0',
            'GoImage.OnsetToOnsetTime': '497',
            'Fixcross.RT': '0',
            'Run1EventList.Cycle': '2',
            'GoImage.OffsetTime': '51343',
            'GoImage.RT': '0',
            'Running': 'Run1EventList',
            'trigger': '2353.3',
            'Run1EventList.Sample': '2',
            'GoImage.DurationError': '0',
            'GoImage.OnsetTime': '51343',
            'Fixcross.OnsetTime': '51840',
            'DataFile.Basename': 'Pokenogo_jitter-065-1',
            'Fixcross.DurationError': '-4',
            'GoImage.CRESP': '1',
            'Level': '3',
            'SessionStartDateTimeUtc': '2/11/2018 8:30:43 PM',
            'Fixcross.ACC': '0',
            'Fixcross.RESP': '',
            'Display.RefreshRate': '60.318',
            'Procedure': 'GoProc',
            'SessionDate': '02-11-2018',
            'Image': 'pokemon/charizard.bmp',
            'GoImage.ACC': '0',
            'Session': '1',
            'GoImage.OnsetDelay': '7',
            'Subject': '065'
        }
        self.config = {
            "stimuli": "Image",
            "initialScannerEvent": "InitFix",
            "trial_type": "Procedure",
            "offsetDelta": 15,
            "events": [
                "GoImage",
                "NogoImage"
            ],
            "response_time": True,
            "encoding": "utf-16",
            "next_onset": "Fixcross.OnsetTime"
        }

    def tearDown(self):
        task_gen.CONFIG = {}

    def test_extract_frames(self):
        # Test getting raw frames from log text file
        frames = task_gen.extract_frames("logfiles/Valid.txt")
        self.assertEqual(len(frames), 4)
        self.assertTrue(frames[0].get('Image'), False)

    def test_invalid_text_logfile(self):
        frames = task_gen.extract_frames("logfiles/Invalid.txt")
        self.assertEqual(len(frames), 0)

    def test_extract_frames_from_csv(self):
        # Test getting raw frames from csv log file
        frames = task_gen.extract_frames_from_csv("logfiles/Valid.csv", 0, ['', 'NULL'])
        self.assertEqual(len(frames), 1)
        self.assertTrue(frames[0].get('tooslow'), False)

    def test_invalid_csv_logfile(self):
        # Test a file without any proper frames
        frames = task_gen.extract_frames_from_csv("logfiles/Invalid.csv", 0, ['', 'NULL'])
        self.assertEqual(len(frames), 0)

    def test_get_initial_offset(self):
        # Test getting the initial offset from different sources
        frame = copy.deepcopy(self.init_frame)
        CONFIG = copy.deepcopy(self.config)
        key = '{0}.OffsetTime'.format(CONFIG.get('initialScannerEvent'))

        offset = task_gen.get_initial_offset(frame, key, CONFIG)
        self.assertEqual(offset, 25)

    def test_no_config_offset(self):
        # Test getting the initial offset from different sources when offset delta isn't given
        frame = copy.deepcopy(self.init_frame)
        CONFIG = copy.deepcopy(self.config)
        CONFIG.pop('offsetDelta')
        key = '{0}.OffsetTime'.format(CONFIG.get('initialScannerEvent'))

        offset = task_gen.get_initial_offset(frame, key, CONFIG)
        self.assertEqual(offset, 10)

    def test_fix_time_for_single_event(self):
        frame = copy.deepcopy(self.event_frame)
        CONFIG = copy.deepcopy(self.config)
        offset = 10
        event = "GoImage"
        timeProps = {'offset': ['OffsetTime', 'OnsetTime'],
                     'nonOffset': ['RT', 'Duration', 'OnsetToOnsetTime']}

        task_gen.fix_time_for_single_event(frame, event, offset, timeProps)

        for key, item in frame.iteritems():
            e, p = key.split('.') if '.' in key else key, None
            if event == e:
                if p in timeProps['offset']:
                    preFix = self.event_frame.get('{}.{}'.format(e,p))
                    self.assertEqual(item, preFix+10)
                elif p in timeProps['nonOffset']:
                    preFix = self.event_frame.get('{}.{}'.format(e,p))
                    self.assertEqual(item, preFix)

    def test_get_event(self):
        frame = copy.deepcopy(self.event_frame)
        CONFIG = copy.deepcopy(self.config)
        task_gen.CONFIG = CONFIG
        trial_type = task_gen.get_event(frame, 'GoImage')

        self.assertEqual(trial_type, 'GoProc')

    def test_get_duration(self):
        frame = copy.deepcopy(self.event_frame)
        frame['GoImage.Duration'] = '497'
        CONFIG = copy.deepcopy(self.config)
        task_gen.CONFIG = CONFIG
        Duration = task_gen.get_duration(frame, 'GoImage')

        self.assertEqual(Duration, '497')

        frame.pop('GoImage.Duration')
        OnsetToOnsetTime = task_gen.get_duration(frame, 'GoImage')

        self.assertEqual(OnsetToOnsetTime, '497')

        frame.pop('GoImage.OnsetToOnsetTime')
        OnsetToNextOnsetTime = task_gen.get_duration(frame, 'GoImage')

        # Because there's subtraction involved, it returns a float
        self.assertEqual(OnsetToNextOnsetTime, '497.0')

    def test_output_filenames(self):
        CONFIG = copy.deepcopy(self.config)
        task_gen.CONFIG = CONFIG

        # Test no start_run config or custom filename
        output_filenames = task_gen.get_output_filenames('task_events.csv', 1)

        self.assertEqual(output_filenames, ['task_events.tsv'])

        # Test no start_run but custom filename
        output_filenames = task_gen.get_output_filenames('task_events.csv', 1, custom_filename='custom_name.tsv')

        self.assertEqual(output_filenames, ['custom_name.tsv'])

        # Test no start_run with mulitple runs
        output_filenames = task_gen.get_output_filenames('task_events.csv', 3)

        self.assertEqual(output_filenames, ['task_events_run-0.tsv', 'task_events_run-1.tsv', 'task_events_run-2.tsv'])

        # Test start run with one run
        task_gen.CONFIG['start_run'] = 2
        output_filenames = task_gen.get_output_filenames('task_events.csv', 1)

        self.assertEqual(output_filenames, ['task_events.tsv'])

        # Test start run with multiple runs
        output_filenames = task_gen.get_output_filenames('task_events.csv', 3)

        self.assertEqual(output_filenames, ['task_events_run-2.tsv', 'task_events_run-3.tsv', 'task_events_run-4.tsv'])

if __name__ == "__main__":

    unittest.main()
    run_module_suite()
