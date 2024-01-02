""" Runnable module for pathtreelib.
"""

import argparse

from . import PathTree, PathTreeProperty


def main():
    """ Compute the tree on specified directory.
    The creation of the tree automatically computes the basic properties on
    all nodes. The properties compued on the root, that are valuable information
    to understand the structure of the tree, are printed (with exclusion of
    depth and height that would be less useful). The nodes of the computed tree
    can be exported in csv and Excel.

    It is possible to pass the following parameters:

    * -d, --dir: the directory to analyse
    * -n, --n: the number of nodes to export (see node_limit in to_csv and in to_excel)
    * -x, --excel: the Excel file for export (only if specified)
    * -c, --csv: the csv file for export (only if specified)

    Examples::

        >>> python -m pathtreelib -d . -n 1000 -x test.xlsx -c test.csv
            <num_dir>     >     218
            <num_file>    >     421
            <num_inode>   >     209
            <num_leaves>  >     430
            <num_nodes>   >     639
            <size>        > 8135024
            <simple_size> >    7 MB
    """

    # Parse command line parameters
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--dir", type=str, default=".",
        help="The directory to analyse"
    )
    parser.add_argument(
        "-n", "--n", type=int, default="1000000", 
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

    # Create tree
    tree = PathTree(params.dir)

    # Pretty print results
    print("Tree properties (root property)")
    max_prp_len = max(list(len(prop.value) for prop, _ in tree.root.property.items()))
    max_val_len = max(list(len(str(value)) for _, value in tree.root.property.items()))
    for prop, value in tree.root.property.items():
        if prop not in [PathTreeProperty.HEIGHT, PathTreeProperty.DEPTH]:
            print(f"{prop.value.ljust(max_prp_len)} > {str(value).rjust(max_val_len)}")

    # Export results
    if params.excel != "":
        tree.to_excel(params.excel, node_limit=params.n)
    if params.csv != "":
        tree.to_csv(params.csv, node_limit=params.n)


if __name__ == "__main__":
    main()
