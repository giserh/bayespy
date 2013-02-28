######################################################################
# Copyright (C) 2013 Jaakko Luttinen
#
# This file is licensed under Version 3.0 of the GNU General Public
# License. See LICENSE for a text of the license.
######################################################################

######################################################################
# This file is part of BayesPy.
#
# BayesPy is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# BayesPy is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with BayesPy.  If not, see <http://www.gnu.org/licenses/>.
######################################################################

"""
Unit tests for `deterministic` module.
"""

import unittest

import numpy as np
import scipy

from numpy import testing

from ..node import Node
from ..deterministic import tile

from bayespy import utils

class TestTile(unittest.TestCase):

    def check_message_to_children(self, tiles, u_parent, u_tiled,
                                  dims=None, plates=None):
        # Set up the dummy model
        class Dummy(Node):
            def get_moments(self):
                return u_parent

        X = Dummy(dims=dims, plates=plates)
        Y = tile(X, tiles)

        u_Y = Y._compute_moments(u_parent)

        for (x,y) in zip(u_Y, u_tiled):
            testing.assert_allclose(x, y,
                                    err_msg="Incorrect moments.")


    def test_message_to_children(self):
        """
        Test the moments of Tile node.
        """
        # Define th check function
        check_message_to_children = self.check_message_to_children
        # Check scalar
        check_message_to_children(2,
                                  (5,),
                                  ([5,5],), 
                                  dims=[()],
                                  plates=()),
        # Check 1-D
        check_message_to_children(2,
                                  ([1,2],),
                                  ([1,2,1,2],),
                                  dims=[()],
                                  plates=(2,))
        # Check N-D
        check_message_to_children(2,
                                  ([[1,2],
                                    [3,4],
                                    [5,6]],),
                                  ([[1,2,1,2],
                                    [3,4,3,4],
                                    [5,6,5,6]],),
                                  dims=[()],
                                  plates=(3,2))
        # Check not-last plate
        check_message_to_children([2,1],
                                  ([[1,2],
                                    [3,4]],),
                                  ([[1,2],
                                    [3,4],
                                    [1,2],
                                    [3,4]],),
                                  dims=[()],
                                  plates=(2,2))
        # Check several plates
        check_message_to_children([2,3],
                                  ([[1,2],
                                    [3,4]],),
                                  ([[1,2,1,2,1,2],
                                    [3,4,3,4,3,4],
                                    [1,2,1,2,1,2],
                                    [3,4,3,4,3,4]],),
                                  dims=[()],
                                  plates=(2,2))
        # Check non-zero dimensional variables
        check_message_to_children(2,
                                  ([[1,2],
                                    [3,4]],),
                                  ([[1,2],
                                    [3,4],
                                    [1,2],
                                    [3,4]],),
                                  dims=[(2,)],
                                  plates=(2,))
        # Check several moments
        check_message_to_children(2,
                                  ([[1,2],
                                    [3,4]],
                                   [1,2]),
                                  ([[1,2],
                                    [3,4],
                                    [1,2],
                                    [3,4]],
                                   [1,2,1,2]),
                                  dims=[(2,),()],
                                  plates=(2,))
        
        
    def check_message_to_parent(self, tiles, m_children, m_true,
                                dims=None, plates_parent=None,
                                plates_children=None):
        # Set up the dummy model
        class Dummy(Node):
            pass
            #def _get_message_and_mask_to_parent(self, index):
            #    return (m_children, True)

        X = Dummy(dims=dims, plates=plates_parent)
        Y = tile(X, tiles)
        #Y.mask = True
        #Z = Dummy(dims=dims, plates=plates_children)

        #m = Y._message_to_parent(0)
        m = Y._compute_message_to_parent(0, m_children, None)

        for (x,y) in zip(m, m_true):
            testing.assert_allclose(x, y,
                                    err_msg="Incorrect message.")


    def test_message_to_parent(self):
        """
        Test the parent message of Tile node.
        """
        # Define th check function
        check = self.check_message_to_parent
        # Check scalar
        check(2,
              ([5,5],), 
              (10,),
              dims=[()],
              plates_parent=(),
              plates_children=(2,)),
        # Check 1-D
        check(2,
              ([1,2,3,4],),
              ([4,6],),
              dims=[()],
              plates_parent=(2,),
              plates_children=(4,))
        # Check N-D
        check(2,
              ([[1,2,7,8],
                [3,4,9,0],
                [5,6,1,2]],),
              ([[8,10],
                [12,4],
                [6,8]],),
              dims=[()],
              plates_parent=(3,2),
              plates_children=(3,4))
        # Check not-last plate
        check([2,1],
              ([[1,2],
                [3,4],
                [5,6],
                [7,8]],),
              ([[6,8],
                [10,12]],),
              dims=[()],
              plates_parent=(2,2),
              plates_children=(4,2))
        # Check several plates
        check([2,3],
              ([[1,2,1,2,1,2],
                [3,4,3,4,3,4],
                [1,2,1,2,1,2],
                [3,4,3,4,3,4]],),
              ([[6,12],
                [18,24]],),
              dims=[()],
              plates_parent=(2,2),
              plates_children=(4,6))
        # Check broadcasting if message has unit axis for tiled plate
        check(2,
              ([[1,],
                [2,],
                [3,]],),
              ([[2,],
                [4,],
                [6,]],),
              dims=[()],
              plates_parent=(3,2),
              plates_children=(3,4))
        # Check broadcasting if message has unit axis for non-tiled plate
        check(2,
              ([[1,2,3,4]],),
              ([[4,6]],),
              dims=[()],
              plates_parent=(3,2),
              plates_children=(3,4))
        # Check non-zero dimensional variables
        check(2,
              ([[1,2],
                [3,4],
                [5,6],
                [7,8]],),
              ([[6,8],
                [10,12]],),
              dims=[(2,)],
              plates_parent=(2,),
              plates_children=(4,))
        # Check several moments
        check(2,
              ([[1,2],
                [3,4],
                [5,6],
                [7,8]],
               [1,2,3,4]),
              ([[6,8],
                [10,12]],
               [4,6]),
              dims=[(2,),()],
              plates_parent=(2,),
              plates_children=(4,))
        
        
        
