# -*- coding:utf-8 -*-
# ----------------------------------------------------------------------
# Copyright 2016 Juergen Probst
#
# This file is part of pyMPB.
#
# pyMPB is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyMPB is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyMPB.  If not, see <http://www.gnu.org/licenses/>.
# ----------------------------------------------------------------------

from __future__ import division
from numpy import linspace
import defaults
import log


class KSpace(object):
    def __init__(
            self, points_list,
            k_interpolation=defaults.default_k_interpolation,
            use_uniform_interpolation=False,
            point_labels=list(), **kwargs):
        """Setup a k-space for the simulation with custom k-points.

        :param points_list:
            The sequence of critical k-points: Usually, a list of
            3-tuples, but can also be a list of 2-tuples or a list of
            numbers, from which the 3-tuples will be built internally by
            expanding the missing dimensions with zeros, e.g.
            [0.5,(0.5, 1)] -> [(0.5, 0, 0), (0.5, 1, 0)].
        :param k_interpolation:
            In the simulation, the points_list will be expanded by
            linearly interpolating between every consecutive pair of
            points, by adding k_interpolation points between each pair.
            (default: defaults.default_k_interpolation)
        :param use_uniform_interpolation:
            MPB Version 1.5 and newer provides the kinterpolate_uniform
            function, which distributes the k-vectors uniformly in
            k-space. Set this to True if you want to use that (default:
            False).
        :param point_labels:
            (optional) A list of strings, one for each point in
            points_list. These strings denotes the high symmetry or
            critical point label of the points, e.g. 'Gamma' for the
            point (0, 0, 0). These labels will be added as comments to
            the point definitions in the ctl file and more importantly
            can be used as labels on the k-vector axis
        :param kwargs: only used internally

        """
        # build list of 3-tuples:
        three_list = []
        for item in points_list:
            try:
                # is it a sequence?
                length = len(item)
                if hasattr(item, 'isalnum'):
                    # This is a string. That is a single item,
                    # even though it has a length:
                    length = 0
            except TypeError:
                # This item is not a list, tuple or similar.
                length = 0
            if length == 0:
                three_list.append((item, 0, 0))
            elif length == 1:
                three_list.append((item[0], 0, 0))
            elif length == 2:
                three_list.append((item[0], item[1], 0))
            elif length == 3:
                three_list.append(tuple(item))
            else:
                three_list.append(tuple(item[0:3]))
                log.warning(
                    'KSpace: a point has been supplied with length > 3. '
                    'I will only use the first 3 entries.')

        # make sure point_labels has the right length, if it is specified:
        pllen = len(point_labels)
        if pllen and pllen < len(three_list):
            # fill up with empty labels:
            point_labels.extend([''] * (len(three_list) - pllen))
        # make local copy, and cut away excess labels:
        point_labels = point_labels[:len(three_list)]

        self.k_interpolation = k_interpolation
        self.use_uniform_interpolation = use_uniform_interpolation
        if use_uniform_interpolation and not defaults.newmpb:
            log.warning('Requested kinterpolate_uniform function in KSpace, '
                        'but this is only available starting from MPB v.1.5. '
                        'Will fall back to simple interpolate function.')
            self.use_uniform_interpolation = False
        self.points_list = three_list
        self.point_labels = point_labels
        self.__dict__.update(kwargs)

    def __str__(self):
        vector3 = '    (vector3 %s %s %s)\n'
        vector3_commented = '    (vector3 %s %s %s)%s\n'
        if self.point_labels:
            # only add '  ;' if label is not empty:
            comments = ['  ;' + pl if pl else pl for pl in self.point_labels]
            vectors = ''.join(
                vector3_commented % (
                    xyz[0], xyz[1], xyz[2], comments[i])
                for i, xyz in enumerate(self.points()))
        else:
            vectors = ''.join(vector3 % (x, y, z) for x, y, z in self.points())

        if self.use_uniform_interpolation:
            interpol_func = defaults.k_uniform_interpolation_function
        else:
            interpol_func = defaults.k_interpolation_function

        if self.k_interpolation:
            return ('(%s %i (list\n%s))' %
                    (interpol_func,
                     self.k_interpolation,
                     vectors))
        else:
            return '(list\n%s)' % vectors

    def __repr__(self):
        s = '; '.join('{0}={1!s}'.format(key, val) for key, val in
                      self.__dict__.items())
        return '<kspace.KSpace object: {0}>'.format(s)

    def count_interpolated(self):
        """Return total number of k-vecs after interpolation."""
        return (len(self.points()) - 1) * (self.k_interpolation + 1) + 1

    def points(self):
        """Return the bare list of k-points, before any k_interpolation is
        applied.

        """
        return self.points_list

    def has_labels(self):
        """Was this KSpace object created with point_labels specified?"""
        return (len(self.point_labels) and
                len(self.points()) == len(self.point_labels))

    def labels(self):
        """Return the list of labels, one for each entry in points().

        If this KSpace object was not created with point_labels specified,
        this will return an empty list.

        """
        if self.has_labels():
            return self.point_labels[:]
        else:
            return []


class KSpaceTriangular(KSpace):
    def __init__(
            self, k_interpolation=defaults.default_k_interpolation,
            use_uniform_interpolation=False):
        """Setup a k-space for the simulation with critical k-points along the
        boundary of the irreducible brillouin zone of the triangular/hexagonal
        lattice, i.e.: [Gamma, M, K, Gamma].

        """
        KSpace.__init__(
            self,
            points_list=[(0, 0, 0), (0, 0.5, 0), ('(/ -3)', '(/ 3)', 0),
                         (0, 0, 0)],
            k_interpolation=k_interpolation,
            use_uniform_interpolation=use_uniform_interpolation,
            point_labels=['Gamma', 'M', 'K', 'Gamma'])


class KSpaceRectangular(KSpace):
    def __init__(
            self, k_interpolation=defaults.default_k_interpolation,
            use_uniform_interpolation=False):
        """Setup a k-space for the simulation with critical k-points along the
        boundary of the irreducible brillouin zone of the rectangular lattice,
        i.e.: [Gamma, X, M, Gamma].

        """
        KSpace.__init__(
            self,
            points_list=[(0, 0, 0), (0.5, 0, 0), (0.5, 0.5, 0),
                         (0, 0, 0)],
            k_interpolation=k_interpolation,
            use_uniform_interpolation=use_uniform_interpolation,
            point_labels=['Gamma', 'X', 'M', 'Gamma'])


class KSpaceRectangularGrid(KSpace):
    def __init__(self, x_steps, y_steps):
        """Setup a k-space with k-points distributed on a rectangular grid.

        The k-points are distributed in the k_x-k_y-plane over the smallest
        rectangular brillouin zone of the rectangular lattice, i.e. k_x (k_y)
        varies in x_steps (y_steps) from -0.5 to 0.5 (inclusive), respectively.

        """
        grid = [(x, y, 0.0)
                for y in linspace(-0.5, 0.5, y_steps)
                for x in linspace(-0.5, 0.5, x_steps)]
        # x_steps and y_steps needed in bandstructure plot in graphics.py:
        KSpace.__init__(
            self, points_list=grid, k_interpolation=0,
            use_uniform_interpolation=False,
            x_steps=x_steps, y_steps=y_steps)
