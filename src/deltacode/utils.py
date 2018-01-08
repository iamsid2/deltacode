#
# Copyright (c) 2017 nexB Inc. and others. All rights reserved.
# http://nexb.com and https://github.com/nexB/deltacode/
# The DeltaCode software is licensed under the Apache License version 2.0.
# Data generated with DeltaCode require an acknowledgment.
# DeltaCode is a trademark of nexB Inc.
#
# You may not use this software except in compliance with the License.
# You may obtain a copy of the License at: http://apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#
# When you publish or redistribute any data created with DeltaCode or any DeltaCode
# derivative work, you must accompany this data with the following acknowledgment:
#
#  Generated with DeltaCode and provided on an "AS IS" BASIS, WITHOUT WARRANTIES
#  OR CONDITIONS OF ANY KIND, either express or implied. No content created from
#  DeltaCode should be considered or used as legal advice. Consult an Attorney
#  for any legal advice.
#  DeltaCode is a free and open source software analysis tool from nexB Inc. and others.
#  Visit https://github.com/nexB/deltacode/ for support and download.
#

from __future__ import absolute_import

from collections import defaultdict


from commoncode import paths


def deltas(deltacode):
    """
    Return a generator of Delta dictionaries for JSON serialized ouput.
    """
    for category, deltas in deltacode.deltas.iteritems():
        for delta in deltas:
            yield delta.to_dict()


class AlignmentException(Exception):
    """
    Named exception for alignment errors.
    """
    pass


def align_trees(a_files, b_files):
    """
    Given two sequences of File objects 'a' and 'b', return a tuple of
    two integers that represent the number path segments to remove
    respectively from a File path in 'a' or a File path in 'b' to obtain the
    equal paths for two files that are the same in 'a' and 'b'.
    """
    # we need to find one uniquly named file that exists in 'a' and 'b'.
    a_names = defaultdict(list)
    for a_file in a_files:
        a_names[a_file.name].append(a_file)
    a_uniques = {k: v[0] for k, v in a_names.items() if len(v) == 1}

    b_names = defaultdict(list)
    for b_file in b_files:
        b_names[b_file.name].append(b_file)
    b_uniques = {k: v[0] for k, v in b_names.items() if len(v) == 1}

    candidate_found = False
    for a_name, a_unique in a_uniques.items():
        if a_name not in b_uniques:
            continue
        b_unique = b_uniques.get(a_name)
        if a_unique and a_unique.sha1 == b_unique.sha1:
            candidate_found = True
            break

    if not candidate_found:
        raise AlignmentException
    if a_unique.path == b_unique.path:
        return 0, 0

    common_suffix, common_segments = paths.common_path_suffix(a_unique.path, b_unique.path)
    a_segments = len(paths.split(a_unique.path))
    b_segments = len(paths.split(b_unique.path))

    return a_segments - common_segments, b_segments - common_segments


def fix_trees(a_files, b_files):
    """
    Given two sequences of File objects 'a' and 'b', use the tuple of two
    integers returned by align_trees() to remove the number of path segments
    required to create equal paths for two files that are the same in 'a' and
    'b'.
    """
    a_offset, b_offset = align_trees(a_files, b_files)
    for a_file in a_files:
        a_file.original_path = a_file.path
        a_file.path = '/'.join(paths.split(a_file.path)[a_offset:])

    for b_file in b_files:
        b_file.original_path = b_file.path
        b_file.path = '/'.join(paths.split(b_file.path)[b_offset:])


def index_delta_files(self, index_key='path'):
    """
    Return a dictionary of a list of File objects indexed by the key passed via
    the 'key' variable.  If no 'key' variable is passed, the dict is
    keyed by the File object's 'path' variable.  This function does not
    currently catch the AttributeError exception.
    """
    index = {}

    for f in self:
        key = getattr(f, index_key)

        if index.get(key) is None:
            index[key] = []
            index[key].append(f)
        else:
            index[key].append(f)

    return index
