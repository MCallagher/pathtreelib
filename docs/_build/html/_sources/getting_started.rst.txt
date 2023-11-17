
.. image:: https://img.shields.io/badge/Version-Alpha-blue

.. image:: https://img.shields.io/badge/License-MIT-blue

***********
pathtreelib
***********
The pathtreelib module aim to provide simple tools to analyse files and
directories. The files and directories are represented by nodes which are
organized in a tree structure (linked).

The task that inspired this module is the analysis of a volume content to
understand where to free space.

============
How it works
============
-----
Nodes
-----
Each directory/file is represented by a node containing information about the
path of the element, the node of the parent, the nodes of the children and the
properties associated to it.

This information are populated when creating every single node: the children
nodes are created and then the children' children are created and so on.
The result is that all the nodes in the subtrees of the initial nodes are
computed. The initial node is the root of the tree hence it has no parent.

-----
Trees
-----
The tree class is initialized with a single node (the root) and, by default, a
set of basic properties is automatically computed, such as height, depth, number
of nodes, size of the nodes/subtrees.

The tree class provide the following functionalities:

* Different types of iteration on the nodes (e.g. depth-first, breadth-first)
* Computation of different types of custom properties (e.g. bottom-up, top-down)
* Pruning of part of the trees
* Exporting in csv and Excel

----------
Properties
----------
The basic properties of the nodes computed by default are listed in a specific
enum, its values are the key to access the properties on the node. Custom
properties can be computed as well by using the correct funciton according to
type of the property. 

Examples of the types of properties are the following: height is bottom-up
function since it must be computed on children first and on parent later while
the depth is a top-down function since it must be computed on parent first and
on children later. In addition, there is the possibility to compute a property
that depends only on the property of a single node (no parent/children
information required).

The computation of a property is described by functions that contain the
operations to perform on the node to obtain the result. The process is similar
to a recursion, where there is a base case and an recursive case. For example, a
bottom-up property requires a function to compute the property on the leaves
(base case) and a function to compute the property on the inner nodes using also
the information on the children (recursive case).

===============
Getting started
===============
-------------------
Tree initialization
-------------------
Initialize a tree and automatically compute basic tree properties on every node.
A tree can be initialized also with a Path object or a PathNode and automatic
property computation can be turned off.

.. code-block:: python

   from pathtreelib import PathTree
   tree = PathTree("foo")

-----------
Node fields
-----------
Access to the fields of a node, in particular the root. Each node exposes its
Path, the parent as PathNode, the list of children as PathNodes and a dictionary
containint its properties.

.. code-block:: python
   
   node = tree.root
   node.path
   node.parent
   node.children
   node.properties

------------------
Iteration on nodes
------------------
Iterate on the nodes of the tree. It is possible to iterate in three different
ways: breadth-first (used for __iter__), depth-first and validated.
The first two ways are classic approaches, the third is custom-made and consist
in a breadth-first where subtrees that do not satisfy a validation condition are
pruned from the iteration: if the condition is not satisfied on a node, it and
its subtree are excluded from the iteration.

.. code-block:: python

   # Breadth-first (default)
   for node in tree:
      pass
   # Breadth-first
   for node in tree.breadth_first_iter():
      pass
   # Depth-first
   for node in tree.depth_first_iter():
      pass
   # Validated iter
   validation_func = lambda node: node.property[PathTreeProperty.DEPTH] < 5
   for node in tree.validated_iter(validation_func):
      pass

--------------------
Property computation
--------------------
There are three types of properties supported:

* Bottom-up: the property is computed on the children (the leaves are the base
case) and then on the parent (recursive case)
* Top-down: the property is computed on the parent (the root is the base case)
and then on the children (recursive case)
* Individual property: the property can be computed on the node independently
from the others

^^^^^^^^^^^^^^^^^^
Bottom-up property
^^^^^^^^^^^^^^^^^^
We use the height as an example. The height of the nodes is a bottom-up property
that has two cases:

1. If the node is a leaf, then the height is 0
2. If the node is an inode, the height is the minimum height of the children +1
   (assuming the property is already computed on the children)

The first case is expressed by a function that maps a node into an integer and
that will be applied only on leaves. The second case is expressed by a function
that maps a node and a list of nodes into an integer: the node contains an inode
while the list contains its children.

Note. The second case function could take as parameter only the inode since its
children are simply inode.children, however it is preferred to keep explicitly
the parameter as a remainder of how the property is computed.

.. code-block:: python

   leaf_func = lambda leaf: 0
   inode_func = lambda inode, children: 1 + min([child.property["height"] for child in children])
   tree.compute_bottom_up_property("height", leaf_func=leaf_func, inode_func=inode_func)

^^^^^^^^^^^^^^^^^
Top-down property
^^^^^^^^^^^^^^^^^
We use the depth as an example. The depth of the nodes is a top-down property
that has two cases:

1. If the node is the root, then the depth is 0
2. If the node has a parent, the depth is the depth of the parent +1 (assuming
   the property is already computed on the parent)

The first case is expressed by a function that maps a node into an integer and
that will be applied only on the root. The second case is expressed by a
function that maps two nodes into an integer: the nodes are a node and its
parent.

Note. The second case function could take as parameter only a node since its
paernt is simply node.parent, however it is preferred to keep explicitly
the parameter as a remainder of how the property is computed.

.. code-block:: python

   root_func = lambda root: 0
   notroot_func = lambda node, parent: 1 + parent.property["depth"]
   tree.compute_dop_down_property("depth", root_func=root_func, notroot_func=notroot_func)

^^^^^^^^^^^^^^^^^^^
Individual property
^^^^^^^^^^^^^^^^^^^
We use the flag is directory as an example. The property of being a directory
for a node depends exclusively on the node itself, hence in this case there is
no more than one case to manage:

1. If the path of the node is a directory then true, else false

The case is expressed by a function that maps a node into a boolean and that
will be applied to each node in the tree.

.. code-block:: python

   property_func = lambda node: node.path.is_dir()
   tree.compute_individual_property("is_dir", property_func)

-------
Pruning
-------
The pruning can help reducing the time requested to navigate the tree by removing the nodes that are not considered useful. The usefulness of a node is expressed by a boolean function that evaluates true only on nodes that must be keep in the tree.
There are two modes of pruning: logical and physical.

As an example, we show the pruning of all nodes that have size smaller than 1 KB (1024 B).

^^^^^^^^^^^^^^^
Logical pruning
^^^^^^^^^^^^^^^
The logical pruning does not explicitly remove any node from the tree but set the property pruned to true if the node should be considered logically removed from the tree.

.. code-block:: python

   keep_condition = lambda node: node.property[PathTreeProperty.SIZE] > 1024
   tree.logical_pruning(keep_condition=keep_condition)

^^^^^^^^^^^^^^^^
Physical pruning
^^^^^^^^^^^^^^^^
The physical pruning explicitly removes any node (and its subtree) that does not
satisfy the condition, however the property of the nodes are not recomputed.
E.g. suppose a root has height of 5, if the pruning condition removes all the
leaves, the real height of the tree becomes 4, however the value of the property
would still be 5.

.. code-block:: python

   keep_condition = lambda node: node.property[PathTreeProperty.SIZE] > 1024
   tree.physical_pruning(keep_condition=keep_condition)

---------
Exporting
---------
The nodes can be exported in csv or Excel. Each node is mapped to a record
containing the path of the node and, by default, all its properties (the
property list is customizable). To prevent accidental huge exports the number of
nodes that can be exported is limited, by default, to a million nodes (the limit
can be changed or removed). In addition, to export only interesting rows, it is
possible to specify a condition to export only nodes that satisfy a specific
criteria.

.. code-block:: python

   tree.to_csv(csvfile="test.csv", properties["heigth", "depth", "is_dir"], node_limit=-1)
   tree.to_excel(csvfile="test.xlsx", properties["heigth", "depth", "is_dir"], node_limit=-1)

--------
Examples
--------
Analysis of the whole C volume in Windows to find the most space consuming
folders with holiday pictures (folders with a large number of jpg files).

.. code-block:: python

   # Generate the whole tree (could take a while if the volume is large)
   tree = PathTree("C:/")

   # Compute on each node the number of picture in its subtree
   tree.compute_bottom_up_property(
      "num_of_jpg",
      leaf_func=lambda leaf: 1 if leaf.path.suffix == '.jpg' else 0,
      inode_func=lambda inode, children: sum([child.property["num_of_jpg"] for child in children])
   )

   # Keep only the subtrees of interest (that have at least 10 pics)
   tree.physical_pruning(keep_condition=lambda node: node.property["num_of_jpg"] > 10)

   # The nodes that are now leaves are the photo directories we are looking for
   tree.compute_individual_property("photo_dir", lambda node: len(node.children) == 0)

   # Find the 3 largest photo directories
   photo_dirs = [
      node
      for node in tree
      if node.property["photo_dir"]
   ]
   photo_dirs.sort(key=node.property[PathTreeProperty.SIZE], reverse=True)
   print("The 3 largest photo directories:", photo_dirs[:3])

   # Export all the photo directories with the main information to csv
   tree.to_csv(
      "large_photo_dirs",
      properties=["num_of_jpg", PathTreeProperty.SIZE],
      node_condition=lambda node: node.property["photo_dir"]
   )
