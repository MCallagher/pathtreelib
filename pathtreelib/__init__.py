""" Enhancement of pathlib, representation with a tree data-structure.

This module enhances the functionalities of pathlib, interpreting the Path
objects as nodes of a tree and automatically creating their subtrees. The tree
can be explored for analysis purposes.
"""


from   pathlib import Path
from   typing import Union, Callable, Iterator, Any
from   enum import Enum
import copy
import xlsxwriter


__all__ = ["PathNode", "PathTree", "PathTreeProperty", "TreeException", "Size"]


class PathTreeProperty(Enum):
    """ Enumerator class for the tree properties.
    """

    HEIGHT = "<height>"
    """ Height (of a node): the minimal distance from the note to a leaf. """
    DEPHT = "<depth>"
    """ Depth (of a node): the distance from the note to the root. """
    NUM_OF_DIRECTORIES = "<num_dir>"
    """ No. of Directory (of a subtree): the number of directory in the subtree. """
    NUM_OF_FILES = "<num_file>"
    """ No. of Files (of a subtree): the number of files in the subtree. """
    NUM_OF_INODES = "<num_inode>"
    """ No. of inner nodes (of a subtree): the number of inner nodes in the subtree. """
    NUM_OF_LEAVES = "<num_leaves>"
    """ No. of leaves (of a subtree): the number of leaves in the subtree. """
    NUM_OF_NODES = "<num_nodes>"
    """ No. of nodes (of a subtree): the number of nodes in a subtree. """
    SIZE = "<size>"
    """ Size (of a subtree): the sum of the byte occupied by all the files in the subtree. """
    SIMPLE_SIZE = "<simple_size>"
    """ Size (of a subtree) in simplified format: the sum of the byte occupied by all the files in
    the subtree, expressed in KB, ..., TB accordingly. """
    PRUNED = "<pruned>"
    """ Pruned status (of a node): true if the node has been virtually removed from the tree, false
    otherwise. """


class Size(Enum):
    """ Enumerator class for the main byte multiples.
    """

    KB = 1024 ** 1
    """ Number of bytes in a kilobyte. """
    MB = 1024 ** 2
    """ Number of bytes in a megabyte. """
    GB = 1024 ** 3
    """ Number of bytes in a gigabyte. """
    TB = 1024 ** 4
    """ Number of bytes in a terabyte. """

    @staticmethod
    def simplified_size(size:int):
        """ Convert num of bytes to a sinthetic string.

        The size expressed with a multiple of the byte and with 1-3 significant
        digits. E.g. 23 MB
        """

        return \
            f"{size} B" if size < Size.KB.value else (
            f"{size // Size.KB.value} KB" if size < Size.MB.value else (
            f"{size // Size.MB.value} MB" if size < Size.GB.value else (
            f"{size // Size.GB.value} GB" if size < Size.TB.value else
            f"{size // Size.TB.value} TB"
            )))


class TreeException(Exception):
    """ Tree structure violated Exception.
    """


class PathNode():
    """ The PathNode class describe a tree node containing information
    associated to a path.

    The children of a node are sorted by: type (directories first, then files),
    path (alphabetically on the file/dir name).

    Instance variables:
        path: the path associated to the node
        parent: the parent directory of the node, as a PathNode object
        children: the children files/directories of the node, as list of
            PathNode objects
        data: a dictionary that can contain custom properties of the node
            (e.g. height, subtree size, ...)
    """

    def __init__(self, path:Path, parent:Union["PathNode",None]=None) -> None:
        """ Create a new path node and all its subtree.

        Params:
            path: the path of the node
            parent: the path of the parent node (if None, it is a root node)
        """

        self.path = path
        self.parent = parent
        self.children = self.__compute_children()
        self.property = {}

    def __compute_children(self):
        """ Iteratively scan and generate the subtree of the node.
        """

        children = []
        try:
            if self.path.is_dir():
                for child in self.path.iterdir():
                    children.append(PathNode(child, self))
                children.sort(key=lambda node:f"{0 if node.path.is_dir() else 1}|{node.path.name}")
        except PermissionError:
            pass
        except FileNotFoundError:
            pass
        return children

    def is_root(self) -> bool:
        """ Return true if and only if the node is root.

        Check if the node has a parent node.

        Return:
            True if and only if the node is root.
        """

        return self.parent is None

    def is_leaf(self) -> bool:
        """ Return true if and only if the node is a leaf.

        Check if the node has children nodes.

        Return:
            True if and only if the node is a leaf.
        """

        return len(self.children) == 0

    def is_inode(self) -> bool:
        """ Return true if and only if the node is an inner node.

        Check if the node has children nodes.

        Return:
            True if and only if the node is an inner node.
        """

        return not self.is_leaf()

    def is_file(self) -> bool:
        """ Return true if and only if the node is a file.

        Check if the node is a file.

        Return:
            True if and only if the node is a file.
        """

        return not self.is_dir()

    def is_dir(self) -> bool:
        """ Return true if and only if the node is a directory.

        Check if the node is a directory.

        Return:
            True if and only if the node is a directory.
        """

        return self.path.is_dir()

    def compute_bottom_up_property(
            self,
            property_name:Union[str,PathTreeProperty],
            base_func:Callable[["PathNode"], Any],
            recursive_func:Callable[["PathNode", list["PathNode"]], Any]
            ) -> None:
        """ Compute a property of bottom-up type in the subtree of the node.

        The bottom-up properties are recursively computed from the leaves
        (files) to the root: when the node is a leaf the proerty can be computed
        directly (without involving other nodes), when the node is an inner node
        the property is computed based also on the children nodes properties.
        Hence there are 2 functions that must be specified: the base case
        function (for leaves), the recursive function (for inner nodes).

        Params:
            property_name: the name of the property (used as key in property
            dict)
            base_func: the function to compute the property on the leaves
            recursive_func: the function to compute the property on the inner
            nodes (assuming it is already computed on the leaves)

        Params of base_func:
            leaf: the current node (as PathNode)

        Params of recursive_func:
            inode: the current node (as PathNode)
            children: the list of children (as PathNode) of the current node

        Code sample for computing the height:
        ```
        base_func = lambda node: 0
        recursive_func = lambda node, children: 1 + min([
            int(child.property["height"])
            for child in children
        ])
        root.compute_bottom_up_property("height", base_func, recursive_func)
        ```
        """

        if self.is_leaf():
            self.property[property_name] = base_func(self)
        else:
            for child in self.children:
                child.compute_bottom_up_property(property_name, base_func, recursive_func)
            self.property[property_name] = recursive_func(self, self.children)

    def compute_top_down_property(
            self,
            property_name:Union[str,PathTreeProperty],
            root_func:Callable[["PathNode"], Any],
            parent_func:Callable[["PathNode", "PathNode"], Any]
            ) -> None:
        """ Compute a property of top-down type in the subtree of the node.

        The top-down properties are recursively computed from the root to the
        leaves: when the node is root the proerty can be computed directly
        (without involving other nodes), when the node is a not-root node the
        property is computed based also on the parent node properties. Hence
        there are 2 functions that must be specified: the root function (for the
        root), the parent function (for not-root nodes).

        Params:
            property_name: the name of the property (used as key in property
            dict)
            root_func: the function to compute the property on the root
            parent_func: the function to compute the property on the not-root
            nodes (assuming it is already computed on the parent)

        Params of root_func:
            root: the current node (as PathNode)

        Params of parent_func:
            node: the current node (as PathNode)
            parent: the parent (as PathNode) of the current node

        Code sample for computing the depth:
        ```
        root_func = lambda root: 0
        parent_func = lambda node, parent: 1 + parent.property["depth"]
        root.compute_top_down_property("depth", root_func, parent_func)
        ```
        """

        if self.is_root():
            self.property[property_name] = root_func(self)
        else:
            if self.parent is not None:
                self.property[property_name] = parent_func(self, self.parent)
            else:
                raise TreeException(f"Not-root node has not a parent ({self})")
        for child in self.children:
            child.compute_top_down_property(property_name, root_func, parent_func)

    def compute_individual_property(
            self,
            property_name:Union[str,PathTreeProperty],
            property_func:Callable[["PathNode"], Any]
        ):
        """ Compute an individual property in the subtree of the node.

        The property does not exploit any knowledge on other nodes. However can
        exploit information stored in the node property dict (e.g. previously
        computed height).

        Params:
            property_name: the name of the property (used as key in property
            dict)
            property_func: the function to compute the property on the node

        Params of property_func:
            node: the current node (as PathNode)

        Code sample for computing the a flag to identify directories:
        ```
        property_func = lambda node: node.path.is_dir()
        root.compute_individual_property("is_dir", property_func)
        ```
        """

        self.property[property_name] = property_func(self)
        for child in self.children:
            child.compute_individual_property(property_name, property_func)

    def remove_property(self, property_name:str) -> bool:
        """ Remove a property of the node.

        Params:
            property_name: the name of the property to remove.

        Return:
            True if the property is successfully removed, false if the property
            is missing.
        """

        if property_name in self.property:
            self.property.pop(property_name)
            return True
        return False

    def copy(self) -> "PathNode":
        """ Return a deepcopy of the node.

        The pointers to other nodes are copied without modification hence point
        to the same nodes.

        Return:
            A copy of the node.
        """

        return copy.deepcopy(self)

    def __str__(self) -> str:
        """ Return a string describing the node properties.

        Print the node name then the properties.

        Return:
            A string describing the node.
        """

        properties = []
        for prop, value in self.property.items():
            if isinstance(prop, PathTreeProperty):
                properties.append(f"{prop.name}={value}")
            else:
                properties.append(f"{prop}={value}")
        return f"[Pathnode] > Path: '{self.path}' | Properties: {', '.join(properties)}"


class PathTree():
    """ The PathTree class describe a tree made up by PathNode nodes.

    The structure mimic the directory tree but add analytic functionalities.

    Instance variables:
        root: the root PathNode of the tree
        property: the properties of the tree (equivalent to the root properties)
    """

    def __init__(self, root:Union[str, Path, PathNode], skip_properties:bool=False) -> None:
        """ Create a new PathTree, based on the root node.

        Params:
            root: the root path
            skip_properties: ignore computation of tree's main properties.
        """

        if isinstance(root, str):
            root = Path(root)
        if isinstance(root, Path):
            root = PathNode(root)
        self.root = root
        self.property = root.property
        if not skip_properties:
            self.__compute_basic_properties()

    def __iter__(self) -> Iterator:
        """ Return a default iterator on the nodes of the tree.

        The order is breadth-first and uses the iterator returned by the
        `breadth_first_iter()` function. To use the depth/first order, use the
        iterator returned by the `depth_first_iter()` function.

        Returns:
            An iterator for the nodes of the tree.
        """
        return self.breadth_first_iter()

    def breadth_first_iter(self) -> Iterator:
        """ Return an iterator on the nodes of the tree using breadth-first
        order.

        Return:
            An iterator for the nodes of the tree, in breadth-first order.
        """

        nodes = [self.root]
        while len(nodes) > 0:
            node = nodes.pop(0)
            nodes = nodes + node.children
            yield node

    def depth_first_iter(self) -> Iterator:
        """ Return an iterator on the nodes of the tree using depth-first
        order.

        Return:
            An iterator for the nodes of the tree, in depth-first order.
        """

        nodes = [self.root]
        while len(nodes) > 0:
            node = nodes.pop(0)
            nodes = node.children + nodes
            yield node

    def validated_iter(self, valid_func:Callable[[PathNode], bool]) -> Iterator:
        """ Return an iterator on filtered nodes of the tree.

        The nodes that do not satisfy the condition are excluded and so their
        subtree.

        Params:
            valid_func: the criteria to keep nodes.

        Return:
            An iterator that exclude not valid nodes and subtrees.

        Params of valid_func:
            node: the node to test
        
        Return of valid_func:
            True if the node is acceptable, false otherwise.
        """

        nodes = [self.root] if valid_func(self.root) else []
        while len(nodes) > 0:
            node = nodes.pop(0)
            nodes = [child for child in node.children if valid_func(child)] + nodes
            yield node

    def compute_bottom_up_property(
            self,
            property_name:Union[str,PathTreeProperty],
            leaf_func:Callable[["PathNode"], Any],
            inode_func:Callable[["PathNode", list["PathNode"]], Any]
            ) -> None:
        """ Compute a property of bottom-up type in the tree.

        This function calls the namesake function of the `PathNode` on the root.
        Check `PathNode.compute_bottom_up_property()` for more details.

        Params:
            property_name: the name of the property (used as key in property
            dict)
            leaf_func: the function to compute the property on the leaves
            inode_func: the function to compute the property on the inner
            nodes (assuming it is already computed on the leaves)

        Params of leaf_func:
            leaf: the current node (as PathNode)

        Params of inode_func:
            inode: the current node (as PathNode)
            children: the list of children (as PathNode) of the current node
        """

        self.root.compute_bottom_up_property(property_name, leaf_func, inode_func)

    def compute_top_down_property(
            self,
            property_name:Union[str,PathTreeProperty],
            root_func:Callable[["PathNode"], Any],
            notroot_func:Callable[["PathNode", "PathNode"], Any]
            ) -> None:
        """ Compute a property of top-down type in the subtree of the node.

        This function calls the namesake function of the `PathNode` on the root.
        Check `PathNode.compute_top_down_property()` for more details.

        Params:
            property_name: the name of the property (used as key in property
            dict)
            root_func: the function to compute the property on the root
            notroot_func: the function to compute the property on the not-root
            nodes (assuming it is already computed on the parent)

        Params of root_func:
            root: the current node (as PathNode)

        Params of notroot_func:
            node: the current node (as PathNode)
            parent: the parent (as PathNode) of the current node
        """

        self.root.compute_top_down_property(property_name, root_func, notroot_func)

    def compute_individual_property(
            self,
            property_name:Union[str,PathTreeProperty],
            property_func:Callable[["PathNode"], Any]
        ):
        """ Compute an individual property in the tree.

        This function calls the namesake function of the `PathNode` on the root.
        Check `PathNode.compute_individual_property()` for more details.

        Params:
            property_name: the name of the property (used as key in property
            dict)
            property_func: the function to compute the property on the node

        Params of property_func:
            node: the current node (as PathNode)
        """

        self.root.compute_individual_property(property_name, property_func)

    def compute_basic_property(self, property_name:PathTreeProperty) -> None:
        """ Compute a basic property, contained in `PathTreeProperty` enum.
        """

        if property_name == PathTreeProperty.HEIGHT:
            self.__compute_height()
        elif property_name == PathTreeProperty.DEPHT:
            self.__compute_depth()
        elif property_name == PathTreeProperty.NUM_OF_DIRECTORIES:
            self.__compute_num_of_directories()
        elif property_name == PathTreeProperty.NUM_OF_FILES:
            self.__compute_num_of_files()
        elif property_name == PathTreeProperty.NUM_OF_INODES:
            self.__compute_num_of_inode()
        elif property_name == PathTreeProperty.NUM_OF_LEAVES:
            self.__compute_num_of_leaves()
        elif property_name == PathTreeProperty.NUM_OF_NODES:
            self.__compute_num_of_nodes()
        elif property_name == PathTreeProperty.SIZE:
            self.__compute_size()
        elif property_name == PathTreeProperty.SIMPLE_SIZE:
            self.__compute_simple_size()

    def __compute_height(self):
        """ Compute the height of the nodes in the tree.
        """

        self.compute_bottom_up_property(
            PathTreeProperty.HEIGHT,
            lambda leaf: 0,
            lambda inode, children:
                1 + min(list(int(child.property[PathTreeProperty.HEIGHT])
                    for child in children
                ))
        )

    def __compute_depth(self):
        """ Compute the depth of the nodes in the tree.
        """

        self.compute_top_down_property(
            PathTreeProperty.DEPHT,
            lambda root: 0,
            lambda node, parent: 1 + parent.property[PathTreeProperty.DEPHT]
        )

    def __compute_num_of_directories(self):
        """ Compute the num. of directories in all the subtrees.
        """

        self.compute_bottom_up_property(
            PathTreeProperty.NUM_OF_DIRECTORIES,
            lambda leaf: 1 if leaf.path.is_dir() else 0,
            lambda inode, children:
                (1 if inode.path.is_dir() else 0) +
                sum(list(child.property[PathTreeProperty.NUM_OF_DIRECTORIES]
                    for child in children
                ))
        )

    def __compute_num_of_files(self):
        """ Compute the num. of files in all the subtrees.
        """

        self.compute_bottom_up_property(
            PathTreeProperty.NUM_OF_FILES,
            lambda leaf: 1 if leaf.path.is_file() else 0,
            lambda inode, children:
                sum(list(child.property[PathTreeProperty.NUM_OF_FILES]
                    for child in children
                ))
        )

    def __compute_num_of_inode(self):
        """ Compute the num. of internal nodes in all the subtrees.
        """

        self.compute_bottom_up_property(
            PathTreeProperty.NUM_OF_INODES,
            lambda leaf: 0,
            lambda inode, children:
                1 + sum(list(child.property[PathTreeProperty.NUM_OF_INODES]
                    for child in children
                ))
        )

    def __compute_num_of_leaves(self):
        """ Compute the num. of leaves in all the subtrees.
        """

        self.compute_bottom_up_property(
            PathTreeProperty.NUM_OF_LEAVES,
            lambda leaf: 1,
            lambda inode, children:
                sum(list(child.property[PathTreeProperty.NUM_OF_LEAVES]
                    for child in children
                ))
        )

    def __compute_num_of_nodes(self):
        """ Compute the num. of nodes in all the subtrees.
        """

        self.compute_individual_property(
            PathTreeProperty.NUM_OF_NODES,
            lambda node:
                node.property[PathTreeProperty.NUM_OF_DIRECTORIES] +
                node.property[PathTreeProperty.NUM_OF_FILES]
        )

    def __compute_size(self):
        """ Compute the size (in bytes) of all the subtrees.
        """

        self.compute_bottom_up_property(
            PathTreeProperty.SIZE,
            lambda leaf: leaf.path.stat().st_size if leaf.path.is_file() else 0,
            lambda inode, children:
                sum(list(child.property[PathTreeProperty.SIZE]
                    for child in children
                ))
        )

    def __compute_simple_size(self):
        """ Compute the (simplified) size of all the subtrees.

        The size expressed with a multiple of the byte and with 1-3 significant
        digits. E.g. 23 MB
        """

        def simplified_size(node:PathNode):
            size = node.property[PathTreeProperty.SIZE]
            return \
                f"{size} B" if size < Size.KB.value else (
                f"{size // Size.KB.value} KB" if size < Size.MB.value else (
                f"{size // Size.MB.value} MB" if size < Size.GB.value else (
                f"{size // Size.GB.value} GB" if size < Size.TB.value else
                f"{size // Size.TB.value} TB"
                )))

        self.compute_individual_property(
            PathTreeProperty.SIMPLE_SIZE,
            simplified_size
        )

    def __compute_basic_properties(self) -> None:
        """ Compute the basic properties for the nodes of the tree.

        The basic properties are:
        - height of the nodes
        - depth of the nodes
        - number of directories in the nodes' subtrees
        - number of files in the nodes' subtrees
        - number of nodes in the nodes' subtrees
        - size (in bytes) of the nodes' subtrees
        - simple size (in KB...TB) of the nodes' subtrees
        """

        self.compute_basic_property(PathTreeProperty.HEIGHT)
        self.compute_basic_property(PathTreeProperty.DEPHT)
        self.compute_basic_property(PathTreeProperty.NUM_OF_DIRECTORIES)
        self.compute_basic_property(PathTreeProperty.NUM_OF_FILES)
        self.compute_basic_property(PathTreeProperty.NUM_OF_INODES)
        self.compute_basic_property(PathTreeProperty.NUM_OF_LEAVES)
        self.compute_basic_property(PathTreeProperty.NUM_OF_NODES)
        self.compute_basic_property(PathTreeProperty.SIZE)
        self.compute_basic_property(PathTreeProperty.SIMPLE_SIZE)


    def remove_property(self, property_name:str) -> tuple[bool, bool]:
        """ Remove a property from all the nodes in the tree.

        If the property is missing from one node, no exception is raised.

        Params:
            property_name: the name of the property to remove.

        Return:
            A tuple containing two booleans:
                1. True if the property appeared in all nodes, false otherwise
                2. True if the property appeared in at least one node, false
                otherwise
        """

        in_all_nodes = True
        in_one_node = False
        for node in self:
            status = node.remove_property(property_name)
            in_all_nodes = in_all_nodes and status
            in_one_node = in_one_node or status
        return in_all_nodes, in_one_node

    def physical_pruning(self, keep_condition:Callable[[PathNode],bool]) -> None:
        """ Remove (physically) the all the subtrees where the root does not
        satisfy the keep condition.

        The tree is scanned in breadth-first order. For each node, the keep
        condition is checked and if it is not satisfied all the corresponding
        subtree is physically removed from the tree.

        Note that the properties of the nodes are not recomputed.

        Params:
            keep_condition: the boolean function that assess if a node, and its
            subtree, should be kept or pruned.

        Params of keep_condition:
            node: the node to check.
        Return of keep_condition:
            True if the node (and subtree) must be kept, false if it must be
            pruned.
        """

        nodes = [self.root]
        while len(nodes) > 0:
            node = nodes.pop(0)

            idx = 0
            while idx < len(node.children):
                if not keep_condition(node.children[idx]):
                    node.children.pop(idx)
                else:
                    idx += 1

            nodes = nodes + node.children

    def logical_pruning(self, keep_condition:Callable[[PathNode],bool]) -> None:
        """ Remove (logically) the all the subtrees where the root does not
        satisfy the keep condition.

        The logical removal is applied using the property
        `PathTreeProperty.PRUNED`: if true, the node is removed.

        The tree is scanned in breadth-first order. For each node, the keep
        condition is checked and if it is not satisfied all the corresponding
        subtree is logically removed from the tree.

        Params:
            keep_condition: the boolean function that assess if a node, and its
            subtree, should be kept or pruned.

        Params of keep_condition:
            node: the node to check.
        Return of keep_condition:
            True if the node (and subtree) must be kept, false if it must be
            pruned.
        """

        self.root.compute_top_down_property(
            PathTreeProperty.PRUNED,
            lambda root: False,
            lambda node, parent:
                parent.property[PathTreeProperty.PRUNED] or
                not keep_condition(node)
        )

    def get_node(self, path:Union[str,Path]) -> Union[PathNode, None]:
        """ Return the PathNode corresponding to the passed Path.

        Params:
            path: the path to search in the tree
        
        Return:
            The PathNode corresponding to the passed Path if exists, None
            otherwise.
        """

        if isinstance(path, str):
            path = Path(path)
        parts = path.parts
        node = self.root
        idx = 1
        found = True
        while found:
            if path == node.path:
                return node
            found = False
            for child in node.children:
                if parts[idx] == child.path.parts[idx]:
                    node = child
                    found = True
                    break
            idx += 1
        return None

    #TODO remove from basic module
    def get_k_largest_nodes(self, k:int, keep_ancestors:bool=False) -> list[PathNode]:
        """ Return the k nodes with larger size.

        By default, the list contains the nodes that have the largest size but
        in case two nodes in the same lineage belong to the top-k list, the
        ancestor is removed from the list. Still, all the ancestors of each node
        can be easily computed.

        Keeping only the last nodes in the hierarchy allows to go deeper in the
        tree and highlight the large nodes, ignoring (typically) less
        meaningfull ancestors.

        Params:
            k: the number of largest nodes requested.
            keep_ancestors: if true, return exactly the k largest nodes, if
            false, return the k largest nodes, taking at max one node for
            each lineage.
        
        Return:
            The top-k largest nodes.
        """
        top_k = []
        queue = [self.root]
        while len(top_k) < k:
            node = queue.pop(0)
            queue += node.children
            queue.sort(key=lambda n:n.property[PathTreeProperty.SIZE], reverse=True)
            top_k.append(node)
            if node.parent in top_k and not keep_ancestors:
                top_k.remove(node.parent)
        return top_k

    #TODO remove from basic module
    def get_large_nodes(self, limit:int) -> list[PathNode]:
        """ Return the list of nodes larger than the passed limit.

        Params:
            limit: the limit size, nodes with larger size will be included.

        Return:
            The nodes with size larger than the passed limit.
        """
        large_nodes = []
        queue = [self.root]
        while len(queue) > 0:
            node = queue.pop(0)
            if node.property[PathTreeProperty.SIZE] >= limit:
                large_nodes.append(node)
                queue += node.children
        return large_nodes

    def copy(self) -> "PathTree":
        """ Return a deepcopy of the tree and all its nodes.

        Return:
            A deepcopy of the tree.
        """

        new_root = self.root.copy()
        new_nodes = [new_root]
        while len(new_nodes) > 0:
            new_node = new_nodes.pop(0)
            new_children = [child.copy() for child in new_node.children]
            new_node.children = new_children
            for new_child in new_children:
                new_child.parent = new_node
            new_nodes = new_nodes + new_children
        return PathTree(new_root, skip_properties=True)

    def __str__(self) -> str:
        """ Return a string describing the tree properties.

        Print the property of the root.

        Return:
            A string describing the tree.
        """

        return f"[PathTree] > Root: ({str(self.root)})"

    def to_csv(
            self,
            csvfile:Union[Path, str],
            properties:Union[list[Union[str, PathTreeProperty]], None]=None,
            node_condition:Callable[[PathNode], bool]=lambda node: True,
            node_limit:int=1000000
        ) -> None:
        """ Export all nodes of the tree to a csv.

        The export includes the name of the path and a list of properties. Due
        to the high number of nodes a directory tree can have, by default, the
        export is limited to the first 1 million nodes.

        Params:
            csvfile: the name of the csv for the export.
            properties: the list of properties to include in the export. If None
            all parameters are included.
            node_condition: the condition a node must meet to be exported (by
            default all nodes are exported).
            node_limit: the max number of nodes that can be exported. If <= 0,
            no limitation is applied.
        """

        if isinstance(csvfile, str):
            csvfile = Path(csvfile)
        if properties is None:
            properties = list(self.root.property.keys())

        # Header
        str_properties = []
        for prop in properties:
            if isinstance(prop, PathTreeProperty):
                str_properties.append(prop.value)
        header = ";".join(["path"] + str_properties)

        # Data
        lines = []
        for node in self.breadth_first_iter():
            if 0 < node_limit <= len(lines):
                break
            if not node_condition(node):
                continue
            line = [node.path.as_posix()]
            for curr_property in properties:
                line.append(str(node.property[curr_property]))
            lines.append(";".join(line))

        with open(csvfile, "w", encoding="utf8") as f:
            f.write(header + "\n")
            for line in lines:
                f.write(line + "\n")

    def to_excel(
            self,
            excelfile:Union[Path, str],
            properties:Union[list[Union[str, PathTreeProperty]], None]=None,
            node_condition:Callable[[PathNode], bool]=lambda node: True,
            node_limit:int=1000000
        ) -> None:
        """ Export all nodes of the tree to Excel.

        The export includes the name of the path and a list of properties. Due
        to the high number of nodes a directory tree can have, by default, the
        export is limited to the first 1 million nodes.

        Params:
            excelfile: the name of the Excel for the export.
            properties: the list of properties to include in the export. If None
            all parameters are included.
            node_condition: the condition a node must meet to be exported (by
            default all nodes are exported).
            node_limit: the max number of nodes that can be exported. If <= 0,
            no limitation is applied.
        """

        if isinstance(excelfile, str):
            excelfile = Path(excelfile)

        if properties is None:
            properties = list(self.root.property.keys())

        workbook = xlsxwriter.Workbook(excelfile)
        sheet = workbook.add_worksheet(f"Export - {self.root.path}")

        # Header
        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': "#002060"
        })
        sheet.write(0, 0, "Path", header_format)
        for col, prop in enumerate(properties, 1):
            if isinstance(prop, PathTreeProperty):
                sheet.write(0, col, prop.value, header_format)
            else:
                sheet.write(0, col, prop, header_format)

        # Data
        row = 1
        for node in self.breadth_first_iter():
            if 0 < node_limit < row:
                break
            if not node_condition(node):
                continue

            sheet.write(row, 0, str(node.path))
            for col, prop in enumerate(properties, 1):
                if prop in node.property:
                    sheet.write(row, col, node.property[prop])
            row += 1

        sheet.autofit()
        workbook.close()
