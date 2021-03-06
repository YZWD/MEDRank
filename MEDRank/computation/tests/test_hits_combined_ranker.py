#!/usr/bin/env python
# encoding: utf-8
"""
test_hits_combined_ranker.py

Created by Jorge Herskovic on 2008-06-18.
Copyright (c) 2008 Jorge Herskovic. All rights reserved.
"""

import unittest
import sys
sys.path.append('../')
from hits_combined_ranker import *
from MEDRank.computation.link_matrix import LinkMatrix

class test_hits_combined_ranker(unittest.TestCase):
    def setUp(self):
        """Copied shamelessly from test_pageranker
        The basic test's link structure will be a matrix describing 5 
        nodes with the following links between them:
            (0)-->(1)-->(2)-->(3)<--(4)
             ↑            ╲__ ↗|
             └─────────────────┘
        With this graph, node 3 is the biggest authority, and nodes 2 and 4
        are the biggest hubs.
        """
        self.m=LinkMatrix(5) # Create a 5x5 link_matrix
        self.r=HITSCombinedRanker(epsilon=1e-30)
        self.m[0, 1]=1
        self.m[1, 2]=1
        self.m[2, 3]=2
        self.m[4, 3]=1
        self.m[3, 0]=1
    def testConstruction(self):
        self.assert_(isinstance(self.r, HITSRanker))
    def testAuthorityEvaluation(self):
        authority_score=self.r.evaluate(self.m)
        authscores=zip(authority_score, xrange(len(authority_score)))
        authscores.sort()
        # The largest authority should be three
        self.assertEqual(3, authscores[-1][1]) 
        # The smallest authority should be four
        self.assertEqual(4, authscores[0][1])
    def testHubEvaluation(self):
        r=HITSCombinedRanker(epsilon=1e-30, 
                             combination_function=lambda x,y: y)
        hub_score=r.evaluate(self.m)
        hubscores=zip(hub_score, xrange(len(hub_score)))
        hubscores.sort()
        # The largest hub should be four
        self.assertEqual(4, hubscores[-1][1]) 
    def test_combined_evaluation(self):
        r=HITSCombinedRanker(epsilon=1e-30, 
                             combination_function=lambda x,y: 5*x+y)
        weird_score=r.evaluate(self.m)
        weirdscores=zip(weird_score, xrange(len(weird_score)))
        weirdscores.sort()
        # print weirdscores
        # The largest weirdscore should be three (it's dominated by authority)
        self.assertEqual(3, weirdscores[-1][1]) 
        
if __name__ == '__main__':
    unittest.main()