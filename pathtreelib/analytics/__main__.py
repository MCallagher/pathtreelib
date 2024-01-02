""" Runnable module for pathtreelib.analytics.
"""

import argparse

from . import PathTreeAnalytics, PathTreeProperty


def main():
    """ Run a basic analysis on the specified directory.
    The analysis consist in computing the largest nodes in the tree, with
    respect to their size. To avoid redundancy, in the extracted nodes there is
    no pair of nodes where one node is the ancestor of the other. The results
    of the test are printed and the list of extracted large nodes can be
    exported in csv and Excel.

    It is possible to pass the following parameters:

    * -d, --dir: the directory to analyse
    * -k, --k: the number of large nodes requested
    * -x, --excel: the Excel file for export (only if specified)
    * -c, --csv: The csv file for export (only if specified)

    Examples::

        >>> python -m pathtreelib.analytics -d . -k 3 -x test.xlsx -c test.csv 
            gordon/pictures/equipment      >   3 GB
            gordon/black mesa/research.pdf >  15 MB
            gordon/black mesa/xen.txt      >   6 MB
    """

    # Parse command line parameters
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--dir", type=str, default=".",
        help="The directory to analyse"
    )
    parser.add_argument(
        "-k", "--k",     type=int, default="10", 
        help="The number of large Path requested"
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
    tree = PathTreeAnalytics(params.dir)
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
