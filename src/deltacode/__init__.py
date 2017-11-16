#
#  Copyright (c) 2017 nexB Inc. and others. All rights reserved.
#
from __future__ import absolute_import

from collections import OrderedDict

from deltacode.models import Scan
from deltacode import utils

__version__ = '0.0.1.beta'


class DeltaCode:
    """
    Handles the basic operations on a pair of incoming ScanCode scans (in JSON
    format) and the Delta objects created from a comparison of the files (in
    the form of File objects) contained in those scans.
    """
    def __init__(self, new_path, old_path):
        self.new = Scan(new_path)
        self.old = Scan(old_path)
        self.deltas = self.determine_delta()

    def align_scan(self):
        """
        Seeks to align the paths of a pair of files (File objects) in the pair
        of incoming scans so that the attributes and other characteristics of
        the files can be compared with one another.  Calls utils.fix_trees(),
        which calls utils.align_trees().
        """
        try:
            utils.fix_trees(self.new.files, self.old.files)
        except utils.AlignmentException:
            for f in self.new.files:
                f.original_path = f.path
            for f in self.old.files:
                f.original_path = f.path

    def determine_delta(self):
        """
        Given new and old scans, return an OrderedDict of Delta objects grouping
        the objects under the keys 'added', 'modified', 'removed' or 'unmodified'.
        Returns None if no File objects can be loaded from either scan.
        """
        if self.new.files is None or self.old.files is None:
            return None

        deltas = OrderedDict([
            ('added', []),
            ('removed', []),
            ('modified', []),
            ('unmodified', [])
        ])

        # align scan and create our index
        self.align_scan()
        new_index = self.new.index_files()
        old_index = self.old.index_files()

        # gathering counts to ensure no files lost or missing from our 'deltas' set
        new_files_to_visit = self.new.files_count
        old_files_to_visit = self.old.files_count

        # perform the deltas
        for path, new_files in new_index.items():
            for new_file in new_files:
                new_files_to_visit -= 1

                if new_file.type != 'file':
                    continue

                try:
                    delta_old_files = old_index[path]
                except KeyError:
                    deltas['added'].append(Delta(new_file, None, 'added'))
                    continue

                # at this point, we have a delta_old_file.
                # we need to determine wheather this is identical,
                # or a modification.
                for f in delta_old_files:
                    if new_file.sha1 == f.sha1:
                        deltas['unmodified'].append(Delta(new_file, f, 'unmodified'))
                        continue
                    else:
                        deltas['modified'].append(Delta(new_file, f, 'modified'))

        # now time to find the added.
        for path, old_files in old_index.items():
            for old_file in old_files:
                old_files_to_visit -= 1
                
                if old_file.type != 'file':
                    continue

                try:
                    # This file already classified as 'modified' or 'unmodified' so do nothing
                    new_index[path]
                except KeyError:
                    deltas['removed'].append(Delta(None, old_file, 'removed'))
                    continue
            
        # make sure everything is accounted for
        assert new_files_to_visit == 0
        assert old_files_to_visit == 0

        return deltas

    def get_stats(self):
        """
        Given a list of Delta objects, return a 'counts' dictionary keyed by
        category -- i.e., the keys of the determine_delta() OrderedDict of
        Delta objects -- that contains the count as a value for each category.
        """
        added, modified, removed, unmodified = 0, 0, 0, 0

        added = len(self.deltas['added'])
        modified = len(self.deltas['modified'])
        removed = len(self.deltas['removed'])
        unmodified = len(self.deltas['unmodified'])

        return OrderedDict([('added', added), ('modified', modified), ('removed', removed), ('unmodified', unmodified)])

    def to_dict(self):
        """
        Given an OrderedDict of Delta objects, return an OrderedDict with a
        'deltacode_version' field, a 'deltacode_stats' field, a 'deltas_count'
        field, and a 'deltas' field containing a list of our Delta objects.
        """
        if self.deltas == None:
            return
        
        return OrderedDict([
            ('added', [d.to_dict() for d in self.deltas.get('added')]),
            ('removed', [d.to_dict() for d in self.deltas.get('removed')]),
            ('modified', [d.to_dict() for d in self.deltas.get('modified')]),
            ('unmodified', [d.to_dict() for d in self.deltas.get('unmodified')]),
        ])


class Delta:
    """
    A tuple reflecting a comparison of two files -- each of which is a File
    object -- and the category that characterizes the comparison:
    'added', 'modified', 'removed' or 'unmodified'.
    """
    def __init__(self, new_file=None, old_file=None, delta_type=None):
        # TODO: add check to ensure both are File objects
        self.new_file = new_file
        self.old_file = old_file
        self.category = delta_type

    def to_dict(self):
        if self.new_file == None and self.old_file == None:
            return

        if self.new_file == None:
            return OrderedDict([
                ('new', None),
                ('old', self.old_file.to_dict()),
            ])
        elif self.old_file == None:
            return OrderedDict([
                ('new', self.new_file.to_dict()),
                ('old', None),
            ])
        else:
            return OrderedDict([
                ('new', self.new_file.to_dict()),
                ('old', self.old_file.to_dict()),
            ])
