#!/usr/bin/env python3
"""Check inherited event qualifiers through ocperf's command-line interface."""
from __future__ import print_function
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


class EventQualifierTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='ocperf-qualifiers-')
        self.repo = os.path.dirname(os.path.abspath(__file__))
        self.core = os.path.join(self.root, 'core.json')
        with open(self.core, 'w') as stream:
            json.dump([{
                'EventName': 'UOPS_ISSUED.STALL_CYCLES', 'EventCode': '0xe',
                'UMask': '0x1', 'EdgeDetect': '1', 'Invert': '1',
                'CounterMask': '1', 'PublicDescription': 'Stall cycles',
                'Counter': '0,1'}], stream)
        self.env = dict(os.environ)
        for name in ('OFFCORE', 'UNCORE', 'UNCORE2', 'EVENTMAP2', 'EVENTMAP3',
                     'DIRECT_MSR'):
            self.env.pop(name, None)
        self.env.update(EVENTMAP=self.core, CACHEDIR=self.root,
                        PERF=os.path.join(self.repo, 'fake-perf.py'))

    def tearDown(self):
        shutil.rmtree(self.root)

    def check_qualifiers(self, flags, expected, raw, alias, event_code=0xe):
        name = 'uops_issued_stall_cycles' if alias else 'uops_issued.stall_cycles'
        first = name + (':' + flags if flags else '')
        env = self.env.copy()
        if raw:
            env['DIRECT_MSR'] = '1'
        command = [sys.executable, os.path.join(self.repo, 'ocperf.py'),
                   'stat', '--print', '-e', first + ',' + name, '/bin/true']
        process = subprocess.Popen(command, cwd=self.root, env=env,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        self.assertEqual(process.returncode, 0, stderr.decode('utf-8'))
        self.assertNotIn(b'bad event qualifier', stderr)
        text = stdout.decode('ascii')
        if flags in ('u', 'pp'):
            self.assertTrue(re.search((r':' if raw else r'/') + flags +
                                      r"(?:[ ',]|$)", text), text)
        if raw:
            events = re.findall(r'\br([0-9a-f]+)\b', text)
        else:
            events = re.findall(r'cpu(?:_core|_atom)?/([^/]+)/', text)
        self.assertGreaterEqual(len(events), 2, text)
        self.assertEqual(len(events) % 2, 0, text)
        for index, event in enumerate(events):
            # The second selection reloads the original defaults. An override
            # must not mutate the cached Event used by other selections.
            values = expected if index < len(events) // 2 else (1, 1, 1)
            if raw:
                value = int(event, 16)
                self.assertEqual(value & ~((255 << 24) | (1 << 23) | (1 << 18)),
                                 0x100 | event_code)
                self.assertEqual((value >> 24) & 255, values[0])
                self.assertEqual((value >> 23) & 1, values[1])
                self.assertEqual((value >> 18) & 1, values[2])
            else:
                for key, value in zip(('cmask', 'inv', 'edge'), values):
                    matches = re.findall(r'(?:^|,)' + key + r'=(\d+)', event)
                    self.assertEqual(matches, [str(value)], event)
                self.assertIn('event=0x%x,umask=0x1' % event_code, event)

    def test_actual_underscore_name_takes_precedence(self):
        with open(self.core) as stream:
            events = json.load(stream)
        actual = events[0].copy()
        actual.update(EventName='UOPS_ISSUED_STALL_CYCLES', EventCode='0x2d')
        with open(self.core, 'w') as stream:
            json.dump([actual] + events, stream)
        self.check_qualifiers('', (1, 1, 1), False, True, event_code=0x2d)
        self.check_qualifiers('', (1, 1, 1), True, True, event_code=0x2d)


def make_test(flags, values, raw, alias):
    def test(self):
        self.check_qualifiers(flags, values, raw, alias)
    return test


cases = [('', (1, 1, 1)), ('inv0', (1, 0, 1)), ('i0', (1, 0, 1)),
         ('inv=0', (1, 0, 1)), ('c10', (10, 1, 1)),
         ('cmask10', (10, 1, 1)), ('cmask=10', (10, 1, 1)),
         ('e0', (1, 1, 0)), ('edge=0', (1, 1, 0)),
         ('c0:i0:e0', (0, 0, 0)), ('u', (1, 1, 1)), ('pp', (1, 1, 1))]
for case_index, (qualifiers, expected) in enumerate(cases):
    for is_raw in (False, True):
        for is_alias in (False, True):
            test_name = 'test_case_%02d_raw_%s_alias_%s' % (
                case_index, is_raw, is_alias)
            setattr(EventQualifierTest, test_name,
                    make_test(qualifiers, expected, is_raw, is_alias))


if __name__ == '__main__':
    unittest.main()
