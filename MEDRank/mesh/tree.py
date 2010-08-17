#!/usr/bin/env python
# encoding: utf-8
"""
tree.py

Created by Jorge Herskovic on 2008-04-22.
Copyright (c) 2008 Jorge Herskovic. All rights reserved.
"""

import sys
import os.path
from MEDRank.utility.logger import logging, ULTRADEBUG
from MEDRank.mesh.tree_node import TreeNode
from MEDRank.file.disk_backed_dict import StringDBDict
from MEDRank.evaluation.vocabulary_vector import VocabularyVector

_DEFAULT_TREE_DATA=os.path.join(sys.exec_prefix, "medrank_data",
                                "mesh09_data.db")

class TermNotInTree(KeyError):
    """Exception that states that a term was not found in the tree."""
    pass

class PositionNotInTree(IndexError):
    """Exception that signals that a position wasn't found in the tree."""
    pass
    
class Tree(object):
    """Describes a tree of MeSH terms. The contents should be tree_node,
    generated by the build_mesh_tree_file script. The tree contains a 
    term name (string)->tree_node mapping."""
    def __init__(self, filename="*&$#$%#", file_mode="r", cachesize=1048576):
        # If the filename isn't specified, use the default one (None has a
        # special meaning, so we can't use it - it means create a temp file)
        if filename=="*&$#$%#":
            filename=_DEFAULT_TREE_DATA
        logging.info("Initializing tree with data from %r", filename)
        self._tree=StringDBDict(persistent_file=filename, file_mode=file_mode,
                                cachesize=cachesize)
        self._invlookup=None # Init the inverse name lookup database lazily
        self._origname=filename
        self.terms=self._tree.keys()
        self.terms.sort()
        # This one is for speedy retrieval and indexing
        self._term_list_as_dict=None
        self.num_terms=len(self.terms)
        return
    def original_filename(self):
        """Returns the original filename of the tree."""
        return self._origname
    def __repr__(self): 
        return "<MeSH Semantic tree from %s with %d terms>" % \
                (self._origname, self.num_terms)
    
    @staticmethod
    def common_root(pos1, pos2):
        """Determines the common dotted root of a pair of tree positions."""
        pos1_split=pos1.split(".")
        pos2_split=pos2.split(".")
        common_terms=[]
        for x in zip(pos1_split, pos2_split):
            if x[0]!=x[1]: break
            common_terms.append(x[0])
        return '.'.join(common_terms)
    
    def semantic_distance(self, term1, term2):
        """Distance between two nodes, assuming there is a single root node
        for the tree linking all subtrees. Qualifiers and descriptors are
        automatically excluded"""
        node1=self._tree[term1]
        node2=self._tree[term2]
        if node1.is_qualifier() or node2.is_qualifier():
            return -1
        if node1.is_descriptor() or node2.is_descriptor():
            return -1
        distance=999999999999
        for pos1 in node1.position:
            pos1='#.%s' % pos1
            for pos2 in node2.position:
                # The extra item in pos 1 and pos 2 emulates the common root 
                # node
                pos2='#.%s' % pos2
                root=self.common_root(pos1, pos2)
                rootdots=root.count(".")
                dist_1=pos1.count(".")-rootdots
                dist_2=pos2.count(".")-rootdots
                dist=dist_1+dist_2
                if dist < 0.0:
                    raise ValueError("Problem: %s<->%s have a negative "
                                     "distance", pos1, pos2)
                if dist < distance: distance=dist
        return distance
    def distance(self, term1, term2):
        """Distance between two nodes, assuming no single root node
        for the tree linking all subtrees."""
        # Check for same-treeness
        possible_trees1=self._tree[term1].get_trees()
        possible_trees2=self._tree[term2].get_trees()
        combination_thereof=[x in possible_trees2 for x in possible_trees1]
        if True not in combination_thereof:
            return -1
        sd=self.semantic_distance(term1, term2)
        return sd
    def deepest_of_list(self, list_of_terms):
        return max((self._tree[x].deepest_depth(), x)
                   for x in list_of_terms)[1]
    def _init_inverse_lookup(self):
        """Sets up the internal data store to perform reverse lookups."""
        logging.debug("First request of a reverse lookup. Building the " \
                      "inverse lookup dictionary.")
        self._invlookup={}
        for k, items in self._tree.iteritems():
            for item in items.position:
                self._invlookup[item]=k
        logging.log(ULTRADEBUG, "Done building inverse lookup dictionary.")
        return

    def reverse_lookup(self, term):
        """Perform a reverse lookup, after setting up the reverse lookup
        dictionary if necessary."""
        if self._invlookup is None:
            self._init_inverse_lookup()
        try:
            return self._invlookup[term]
        except KeyError:
            raise PositionNotInTree("%s is not a position in this tree." %
                                    term)

    def __getitem__(self, key):
        try:
            return self._tree[key.lower()]
        except KeyError:
            raise TermNotInTree("The term %s is not in the tree %r." % 
                                (key, self))

    def eliminate_checktags(self, list_of_terms):
        """Returns a list of terms with the checktags omitted."""
        return [x for x in list_of_terms if x not in checktags]

    def eliminate_descriptors(self, list_of_terms):
        return [x for x in list_of_terms 
                if not self._tree[x].is_descriptor(x)]
    def eliminate_qualifiers(self, list_of_terms):
        return [x for x in list_of_terms
                if not self[x].is_qualifier()]
    def only_checktags(self, list_of_terms):
        return [x for x in list_of_terms if x in checktags]
    def only_qualifiers(self, list_of_terms):
        return [x for x in list_of_terms if self._tree[x].is_qualifier()]
    def only_descriptors(self, list_of_terms):
        return [x for x in list_of_terms if self._tree[x].is_descriptor()]
    def index(self, term):
        """Returns the index of a term in the sorted term list"""
        if self._term_list_as_dict is None:
            # Precompute all indexes
            logging.debug("Building MeSH tree index.")
            currindex=0
            self._term_list_as_dict={}
            for each_term in self.terms:
                self._term_list_as_dict[each_term]=currindex
                for each_synonym in self[each_term].synonyms:
                    self._term_list_as_dict[each_synonym]=currindex
                currindex+=1
        try:
            return self._term_list_as_dict[term]
        except KeyError:
            raise TermNotInTree("Term %s is not a member of tree %r" % 
                                (term, self))
    def term_vector(self, list_of_terms):
        """Returns a VocabularyVector representing the list of terms as seen 
        by this tree."""
        new_vector=VocabularyVector(self.num_terms)
        for term in list_of_terms:
            try:
                new_vector[self.index(term)]=1
            except TermNotInTree:
                logging.warn('Weird: term %r could not be found in %r. It '
                             'should be there.',
                             term, self)
        return new_vector
        
