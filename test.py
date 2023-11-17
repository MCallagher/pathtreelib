
""" TestCase to evaluate PathTree correctness.
"""

from   pathlib import Path
import unittest as ut
import json
import gc

from   pathtreelib import PathTree, PathTreeProperty

class TestTreeRefactor(ut.TestCase):
    """ Set of test for the PathTree class.

    The tests check:
    - tree structure (parent, children)
    - property computation
    - logical and physical pruning
    - tree copy
    - iterators
    - get node
    - export
    """

    def __init__(self, *args, **kwargs):
        """ Initialize the test set importing the test source.
        """

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
        """ Test parent children structure. 
        """

        sol_parent = self.test_solution["parent"]
        sol_children = self.test_solution["children"]

        tree = PathTree(self.test_setup["root"])
        for node in tree:
            if node.parent is None:
                self.assertEqual("", sol_parent[node.path.as_posix()])
            else:
                self.assertEqual(node.parent.path.as_posix(), sol_parent[node.path.as_posix()])
            self.assertEqual(
                [child.path.as_posix() for child in node.children],
                sol_children[node.path.as_posix()]
            )

    def test_is_functions(self):
        """ Test the is_* functions of PathNode.
        """

        tree = PathTree(self.test_setup["root"])

        root = list(node.path.as_posix() for node in tree if node.is_root())
        leaves = list(node.path.as_posix() for node in tree if node.is_leaf())
        inodes = list(node.path.as_posix() for node in tree if node.is_inode())
        files = list(node.path.as_posix() for node in tree if node.is_file())
        dirs = list(node.path.as_posix() for node in tree if node.is_dir())

        self.assertEqual(root,   self.test_solution["root"])
        self.assertEqual(leaves, self.test_solution["leaves"])
        self.assertEqual(inodes, self.test_solution["inodes"])
        self.assertEqual(files,  self.test_solution["files"])
        self.assertEqual(dirs,   self.test_solution["dirs"])


    def test_property_computation(self):
        """ Test property computation.
        """

        property_keys = [
            PathTreeProperty.HEIGHT,             PathTreeProperty.DEPTH,
            PathTreeProperty.NUM_OF_DIRECTORIES, PathTreeProperty.NUM_OF_FILES,
            PathTreeProperty.NUM_OF_INODES,      PathTreeProperty.NUM_OF_LEAVES,
            PathTreeProperty.NUM_OF_NODES,       PathTreeProperty.SIZE,
            PathTreeProperty.SIMPLE_SIZE
        ]

        tree = PathTree(self.test_setup["root"])
        for idx, node in enumerate(tree):
            for property_key in property_keys:
                self.assertEqual(
                    node.property[property_key],
                    self.test_solution[property_key.value][idx]
                )

    def test_logical_physical_pruning(self):
        """ Test logical and phisical pruning.
        """

        tree = PathTree(self.test_setup["root"])
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
        """

        sol_parent = self.test_solution["parent"]
        sol_children = self.test_solution["children"]

        tree = PathTree(self.test_setup["root"])
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

    def test_iterators(self):
        """ Test the iterators.
        """

        sol_bfs_order = self.test_solution["bfs_order"]
        sol_dfs_order = self.test_solution["dfs_order"]
        sol_valid_order = self.test_solution["valid_order"]

        def filter_small_nodes(node):
            return node.property[PathTreeProperty.SIZE] > self.test_setup["pruning_size"]

        tree = PathTree(self.test_setup["root"])

        bfs_order = list(node.path.as_posix() for node in tree.breadth_first_iter())
        self.assertEqual(bfs_order, sol_bfs_order)
        dfs_order = list(node.path.as_posix() for node in tree.depth_first_iter())
        self.assertEqual(dfs_order, sol_dfs_order)
        valid_order = list(node.path.as_posix() for node in tree.validated_iter(filter_small_nodes))
        self.assertEqual(valid_order, sol_valid_order)

    def test_get_node(self):
        """ Test the get_node function.
        """

        tree = PathTree(self.test_setup["root"])
        for node in tree:
            self.assertEqual(tree.get_node(node.path.as_posix()), node)

    def test_export(self):
        """ Test exports
        """

        def filter_small_nodes(node):
            return node.property[PathTreeProperty.SIZE] > self.test_setup["pruning_size"]

        csv_filename = Path("test.csv")
        excel_filename = Path("test.xlsx")

        tree = PathTree(self.test_setup["root"])

        tree.to_csv(
            csv_filename,
            properties=[PathTreeProperty.DEPTH, PathTreeProperty.HEIGHT],
            node_condition=filter_small_nodes,
            node_limit=3
        )
        with open(csv_filename, "r", encoding="utf8") as f:
            s = f.read()
            self.assertEqual(s, self.test_solution["csv"])
        csv_filename.unlink()

        tree.to_excel(
            excel_filename,
            properties=[PathTreeProperty.DEPTH, PathTreeProperty.HEIGHT],
            node_condition=filter_small_nodes,
            node_limit=3
        )
        self.assertTrue(excel_filename.exists())
        excel_filename.unlink()

    def tearDown(self) -> None:
        """ Remove directories and files for the test.
        """

        for fileinfo in self.test_setup["files"]:
            Path(fileinfo["name"]).unlink()
        rev_dirs = self.test_setup["dir"]
        rev_dirs.reverse()
        for directory in rev_dirs:
            Path(directory).rmdir()
        rev_dirs.reverse()


if __name__ == "__main__":
    ut.main()
