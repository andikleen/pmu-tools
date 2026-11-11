#!/usr/bin/env python3
"""Exercise OFFCORE overrides through ocperf's command-line entry point."""
from __future__ import print_function
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


class OffcoreOverrideTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='ocperf-offcore-')
        self.repo = os.path.dirname(os.path.abspath(__file__))
        self.cache = os.path.join(self.root, 'cache')
        os.mkdir(self.cache)
        self.core = self.write_json('core.json', [{
            'EventName': 'OFFCORE_RESPONSE', 'EventCode': '0xb7',
            'UMask': '0x1', 'EdgeDetect': '0', 'Invert': '0',
            'PublicDescription': 'Offcore response', 'Counter': '0,1'}])
        self.matrix_data = [
            {'MATRIX_REQUEST': 'CUSTOM_READ', 'MATRIX_RESPONSE': 'NULL',
             'MATRIX_VALUE': '0x2', 'DESCRIPTION': 'Custom reads'},
            {'MATRIX_REQUEST': 'NULL', 'MATRIX_RESPONSE': 'CUSTOM_HIT',
             'MATRIX_VALUE': '0x8', 'DESCRIPTION': 'Custom hits'}]
        self.matrix = self.write_json('custom_matrix.json', self.matrix_data)
        mapfile = os.path.join(self.root, 'mapfile.csv')
        with open(mapfile, 'w') as stream:
            stream.write('Family-model,Version,Filename,EventType\n')
        topology = os.path.join(self.root, 'topology')
        with open(topology, 'w') as stream:
            for pmu in ('cpu', 'cpu_core', 'cpu_atom'):
                stream.write('/sys/bus/event_source/devices/%s/'
                             'format/offcore_rsp\n' % pmu)
        self.env = dict(os.environ)
        for name in ('OFFCORE', 'UNCORE', 'UNCORE2', 'EVENTMAP2', 'EVENTMAP3',
                     'DIRECT_MSR'):
            self.env.pop(name, None)
        self.env.update(EVENTMAP=self.core, TOPOLOGY=topology,
                        CACHEDIR=self.cache, MAPFILE=mapfile,
                        PERF=os.path.join(self.repo, 'fake-perf.py'))

    def tearDown(self):
        shutil.rmtree(self.root)

    def write_json(self, name, data):
        path = os.path.join(self.root, name)
        with open(path, 'w') as stream:
            json.dump(data, stream)
        return path

    def run_ocperf(self, override, event='offcore_response.custom_read.custom_hit'):
        env = self.env.copy()
        if override is not None:
            env['OFFCORE'] = override
        command = [sys.executable, os.path.join(self.repo, 'ocperf.py'),
                   'stat', '--print', '-e', event, '/bin/true']
        process = subprocess.Popen(command, cwd=self.root, env=env,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        self.assertEqual(process.returncode, 0, stderr.decode('utf-8'))
        self.assertNotIn(b'Traceback', stderr)
        return stdout, stderr

    def check_matrix(self, override):
        stdout, stderr = self.run_ocperf(override)
        self.assertIn(b'offcore_rsp=0x80002', stdout)
        self.assertIn(b'name=offcore_response_custom_read_custom_hit', stdout)
        self.assertNotIn(b'Cannot open offcore', stderr)

    def test_absolute_path(self):
        self.check_matrix(self.matrix)

    def test_relative_path(self):
        self.check_matrix('./custom_matrix.json')

    def test_existing_basename(self):
        self.check_matrix('custom_matrix.json')

    def test_cached_basename(self):
        shutil.copyfile(self.matrix, os.path.join(self.cache, 'cached_matrix.json'))
        self.check_matrix('cached_matrix.json')

    def test_wildcard(self):
        self.check_matrix(os.path.join(self.root, '*_matrix.json'))

    def test_cpu_identifier(self):
        shutil.copyfile(self.matrix,
                        os.path.join(self.cache, 'GenuineIntel-6-TEST-offcore.json'))
        self.check_matrix('GenuineIntel-6-TEST')

    def test_default_cpu_matrix(self):
        shutil.copyfile(self.core,
                        os.path.join(self.cache, 'GenuineIntel-6-TEST-core.json'))
        shutil.copyfile(self.matrix,
                        os.path.join(self.cache, 'GenuineIntel-6-TEST-offcore.json'))
        self.env['EVENTMAP'] = 'GenuineIntel-6-TEST'
        self.check_matrix(None)

    def test_no_override_for_core_file(self):
        stdout, stderr = self.run_ocperf(None, 'offcore_response')
        self.assertIn(b'event=0xb7,umask=0x1', stdout)
        self.assertNotIn(b'offcore_rsp=', stdout)
        self.assertNotIn(b'Cannot open offcore', stderr)


if __name__ == '__main__':
    unittest.main()
