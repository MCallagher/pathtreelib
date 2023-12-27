""" Runnable module for pathtreelib.
"""

import argparse

from . import PathTree, PathTreeProperty

def main():
    """ Compute the tree on the pwd.
    The properties of the tree are printed, then the nodes can be exported in
    csv and Excel.

    It is possible to pass the following parameters:

    * -n, --n: the number of nodes to export (see node_limit in to_csv and in to_excel)
    * -x, --excel: the Excel file for export (only if specified)
    * -c, --csv: the csv file for export (only if specified)
    """

    # Parse command line parameters
    parser = argparse.ArgumentParser()
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
    tree = PathTree(".")

    # Pretty print results
    print("Tree properties (root property)")
    max_prp_len = max(list(len(prop.value) for prop, _ in tree.root.property.items()))
    max_val_len = max(list(len(str(value)) for _, value in tree.root.property.items()))
    for prop, value in tree.root.property.items():
        if prop not in [PathTreeProperty.HEIGHT, PathTreeProperty.DEPHT]:
            print(f"{prop.value.ljust(max_prp_len)} > {str(value).rjust(max_val_len)}")

    # Export results
    if params.excel != "":
        tree.to_excel(params.excel, node_limit=params.n)
    if params.csv != "":
        tree.to_csv(params.csv, node_limit=params.n)


if __name__ == "__main__":
    main()
