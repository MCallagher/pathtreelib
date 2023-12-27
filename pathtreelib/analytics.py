""" Set of analytics tools for PathTree.
"""

import argparse

from pathtreelib import PathNode, PathTree, PathTreeProperty


class PathTreeAnalytics(PathTree):
    """ An extension to PathTree with more analytics functions.
    """

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


def main():
    """ Run a basic test on the pwd.
    The results of the test are printed and can be exported in csv and Excel.
    """

    # Parse command line parameters
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-k", "--k",     type=int, default="10", 
        help="The number of large Path to examine"
    )
    parser.add_argument(
        "-x", "--excel", type=str, default="",
        help="The Excel file for export (only if specified)"
    )
    parser.add_argument(
        "-c", "--csv",   type=str, default="",
        help="The csv file for export (only if specified)"
    )
    params = parser.parse_args()

    # Create tree and perform analysis
    tree = PathTreeAnalytics(".")
    largest = tree.get_k_largest_nodes(params.k)

    # Pretty print results
    max_len = max(list(len(node.path.as_posix()) for node in largest))
    for node in largest:
        print(
            f"{node.path.as_posix().ljust(max_len)} > " +
            f"{node.property[PathTreeProperty.SIMPLE_SIZE]:>6s}"
        )

    # Export results
    if params.excel != "":
        tree.to_excel(params.excel, node_condition=lambda node: node in largest)
    if params.csv != "":
        tree.to_csv(params.csv, node_condition=lambda node: node in largest)


if __name__ == "__main__":
    main()
