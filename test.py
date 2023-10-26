
""" TestCase to evaluate PathTree correctness.
"""

from   pathlib import Path
import unittest as ut
import json
import gc

from   pathtreelib import PathTree, PathTreeProperty

class TestTreeRefactor(ut.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        test_file = "test_lib.json"
        text = None
        with open(test_file, "r", encoding="utf8") as f:
            text = f.read()
        self.assertIsNotNone(text, f"Failed to load test file {test_file}")

        self.test_setup = json.loads(text)["test1"]["setup"]
        self.test_solution = json.loads(text)["test1"]["solution"]

    def setUp(self) -> None:
        """ Create directories and files for the test.
        """

        for directory in self.test_setup["dir"]:
            Path(directory).mkdir(exist_ok=True)
        for fileinfo in self.test_setup["files"]:
            with open(Path(fileinfo["name"]), "w", encoding="utf8") as file:
                file.write("X" * fileinfo["size"])

    def test_parent_children_structure(self):
        sol_parent = self.test_solution["parent"]
        sol_children = self.test_solution["children"]

        root_path = self.test_setup["dir"][0]
        tree = PathTree(root_path)
        for node in tree:
            if node.parent is None:
                self.assertEqual("", sol_parent[node.path.as_posix()])
            else:
                self.assertEqual(node.parent.path.as_posix(), sol_parent[node.path.as_posix()])
            self.assertEqual(
                [child.path.as_posix() for child in node.children],
                sol_children[node.path.as_posix()]
            )

    def test_property_computation(self):
        property_keys = [
            PathTreeProperty.HEIGHT,             PathTreeProperty.DEPHT,
            PathTreeProperty.NUM_OF_DIRECTORIES, PathTreeProperty.NUM_OF_FILES,
            PathTreeProperty.NUM_OF_INODES,      PathTreeProperty.NUM_OF_LEAVES,
            PathTreeProperty.NUM_OF_NODES,       PathTreeProperty.SIZE,
            PathTreeProperty.SIMPLE_SIZE
        ]

        root_path = self.test_setup["dir"][0]
        tree = PathTree(root_path)
        for idx, node in enumerate(tree):
            for property_key in property_keys:
                self.assertEqual(
                    node.property[property_key],
                    self.test_solution[property_key.value][idx]
                )

    def test_logical_physical_pruning(self):
        """ Test the logical and phisical pruning.
        """

        root_path = self.test_setup["dir"][0]
        tree = PathTree(root_path)
        sol_active_nodes = self.test_solution["unpruned"]

        def prune_small_nodes(node):
            return node.property[PathTreeProperty.SIZE] > self.test_setup["pruning_size"]

        tree.logical_pruning(prune_small_nodes)
        logical_active_nodes = list(
            node.path.as_posix()
            for node in tree
            if not node.property[PathTreeProperty.PRUNED]
        )
        self.assertEqual(logical_active_nodes, sol_active_nodes)

        tree.physical_pruning(prune_small_nodes)
        phisical_active_nodes = list(
            node.path.as_posix()
            for node in tree
        )
        self.assertEqual(phisical_active_nodes, sol_active_nodes)

    def test_copy(self):
        """ Test the tree copy.

        Create a copy of the tree, delete the original and check the structure.
        """

        sol_parent = self.test_solution["parent"]
        sol_children = self.test_solution["children"]

        tree = PathTree("test")
        new_tree = tree.copy()
        for node in tree:
            del node
        del tree
        gc.collect()
        for node in new_tree:
            if node.parent is None:
                self.assertEqual("", sol_parent[node.path.as_posix()])
            else:
                self.assertEqual(node.parent.path.as_posix(), sol_parent[node.path.as_posix()])
            self.assertEqual(
                [child.path.as_posix() for child in node.children],
                sol_children[node.path.as_posix()]
            )

    def tearDown(self) -> None:
        """ Remove directories and files for the test.
        """

        for fileinfo in self.test_setup["files"]:
            Path(fileinfo["name"]).unlink()
        rev_dirs = [directory for directory in self.test_setup["dir"]]
        rev_dirs.reverse()
        for directory in rev_dirs:
            Path(directory).rmdir()


if __name__ == "__main__":
    ut.main()
