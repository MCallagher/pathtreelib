
""" TestCase to evaluate PathTree correctness.
"""

from   pathlib import Path
import unittest as ut
import gc

from   pathtreelib import PathTree, PathTreeProperty

class TestTree(ut.TestCase):
    """ Test the tree structure, properties and methods.

    The structure tested is the following:

    - test
        - sub1
            - file1.txt (10 B)
            - file2.txt (20 B)
        - sub2
            - file3.txt (30 B)
            - subsub1
                - file4.txt (40 B)
                - file4.txt (50 B)
    """

    _directories = [
        Path("test"),
        Path("test/sub1"),
        Path("test/sub2"),
        Path("test/sub2/subsub1"),
    ]

    _files = [
        Path("test/sub1/file1.txt"),
        Path("test/sub1/file2.txt"),
        Path("test/sub2/file3.txt"),
        Path("test/sub2/subsub1/file4.txt"),
        Path("test/sub2/subsub1/file5.txt")
    ]

    def setUp(self) -> None:
        """ Create directories and files for the test.

        Create the tree of directories and files specified in the class
        docstring.
        """

        for directory in TestTree._directories:
            directory.mkdir(exist_ok=True)
        for idx, file in enumerate(TestTree._files, 1):
            with open(file, "w", encoding="utf8") as file:
                file.write("1234567890" * idx)

    def test_tree(self):
        """ Check the tree structure and properties.

        Check the number of children of the nodes and test each of the basic
        properties.
        """

        tree = PathTree("test")
        root = tree.root
        self.assertEqual(len(root.children), 2, f"Node path: {root.path.name}")
        s_1, s_2 = root.children
        self.assertEqual(len(s_2.children), 2, f"Node path: {s_2.path.name}")
        ss_1, f_3 = s_2.children
        self.assertEqual(len(s_1.children), 2, f"Node path: {s_1.path.name}")
        f_1, f_2 = s_1.children
        self.assertEqual(len(ss_1.children), 2, f"Node path: {ss_1.path.name}")
        f_4, f_5 = ss_1.children

        ref_properties = [
            (PathTreeProperty.HEIGHT,            [2,1,1,1,0,0,0,0,0]),
            (PathTreeProperty.DEPHT,             [0,1,1,2,2,2,2,3,3]),
            (PathTreeProperty.NUM_OF_DIRECTORIES,[4,1,2,1,0,0,0,0,0]),
            (PathTreeProperty.NUM_OF_FILES,      [5,2,3,2,1,1,1,1,1]),
            (PathTreeProperty.NUM_OF_INODES,     [4,1,2,1,0,0,0,0,0]),
            (PathTreeProperty.NUM_OF_LEAVES,     [5,2,3,2,1,1,1,1,1]),
            (PathTreeProperty.NUM_OF_NODES,      [9,3,5,3,1,1,1,1,1]),
            (PathTreeProperty.SIZE,              [150,30,120,90,10,20,30,40,50]),
            (PathTreeProperty.SIMPLE_SIZE,       [
                "150 B","30 B","120 B","90 B","10 B","20 B","30 B","40 B","50 B"
            ])
        ]

        for idx, node in enumerate([root, s_1, s_2, ss_1, f_1, f_2, f_3, f_4, f_5]):
            for prop_name, prop_values in ref_properties:
                self.assertEqual(
                    node.property[prop_name],
                    prop_values[idx],
                    f"Node path: {node.path.name}, property: {prop_name}"
                )

    def test_pruning(self):
        """ Test the logical and phisical pruning.
        """

        tree = PathTree("test")

        tree.logical_pruning(lambda node: node.property[PathTreeProperty.SIZE] > 30)
        logical_active_nodes = 0
        for node in tree:
            if not node.property[PathTreeProperty.PRUNED]:
                logical_active_nodes += 1
        self.assertEqual(logical_active_nodes, 5)

        tree.physical_pruning(lambda node: node.property[PathTreeProperty.SIZE] > 30)
        phisical_active_nodes = 0
        for node in tree:
            phisical_active_nodes += 1
        self.assertEqual(phisical_active_nodes, 5)

    def test_copy(self):
        """ Test the tree copy.

        Create a copy of the tree, delete the original and check the structure.
        """

        tree = PathTree("test")
        new_tree = tree.copy()
        for node in tree:
            del node
        del tree
        gc.collect()
        root = new_tree.root
        self.assertEqual(len(root.children), 2, f"Node path: {root.path.name}")
        s_1, s_2 = root.children
        self.assertEqual(len(s_2.children), 2, f"Node path: {s_2.path.name}")
        ss_1 = s_2.children[0]
        self.assertEqual(len(s_1.children), 2, f"Node path: {s_1.path.name}")
        self.assertEqual(len(ss_1.children), 2, f"Node path: {ss_1.path.name}")


    def tearDown(self) -> None:
        """ Remove directories and files for the test.

        Delete the tree of directories and files specified in the class
        docstring.
        """

        for file in TestTree._files:
            file.unlink()
        TestTree._directories.reverse()
        for directory in TestTree._directories:
            directory.rmdir()
        TestTree._directories.reverse()

if __name__ == "__main__":
    ut.main()
