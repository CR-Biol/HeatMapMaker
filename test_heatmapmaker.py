import builtins
import unittest
from unittest.mock import patch, mock_open

import pandas as pd
from pandas.util.testing import assert_frame_equal

from heatmapmaker import CSV


class ReplaceOpenWithMockString:
    """Context Manager that replaces the builtin open function.
    This CTM is used to mock CSV file inputs.
    The nested structure of this CTM is neccessary since the open() function 
    itself is a CTM. 
    """
    def __init__(self):
        self.old_open = builtins.open
            
    def __enter__(self):
        builtins.open = self.MockStringAsInputStream

    def __exit__(self, *args):
        builtins.open = self.old_open

    class MockStringAsInputStream:
        def __init__(self, mock_string):
            self.content = mock_string

        def __enter__(self):
            return self.function(self.content)

        def __exit__(self, *args):
            pass

        def function(self, mock_string):
            for pseudo_line in mock_string.split("\n"):
                    yield pseudo_line


with ReplaceOpenWithMockString():
    csv_default = "\n".join(
        [
            "col_titles,default1,default2,default3",
            "col1,1,2,3",
            "col2,4,5,6",
            "col3,7,8,9"
        ]
    )
    default = CSV(csv_default)

    csv_with_semicolon = "\n".join(
        [
            "col_titles;semicolon1;semicolon2;semicolon3",
            "col1;1;2;3",
            "col2;4;5;6",
            "col3;7;8;9"
        ]
    )
    semicolon = CSV(
        csv_with_semicolon,
        seperator = ";",
        has_row_titles = True,
        has_col_titles = True
    )  

    csv_no_titles = "\n".join(
        [
            "1,2,3",
            "4,5,6",
            "7,8,9"
        ]
    )
    no_titles = CSV(
        path_to_csv_file = csv_no_titles,
        seperator = ",",
        has_row_titles = False,
        has_col_titles = False
    )
    csv_only_col_titles = "\n".join(
        [
            "col_only1,col_only2,col_only3",
            "1,2,3",
            "4,5,6",
            "7,8,9"
        ]
    )
    col_only = CSV(
        path_to_csv_file = csv_only_col_titles,
        seperator = ",",
        has_row_titles = False,
        has_col_titles = True
    )

    csv_only_row_titles = "\n".join(
        [
            "row_only1,1,2,3",
            "row_only2,4,5,6",
            "row_only3,7,8,9"
        ]
    )
    row_only = CSV(
        path_to_csv_file = csv_only_row_titles,
        seperator = ",",
        has_row_titles = True,
        has_col_titles = False
    )


class TestCSV(unittest.TestCase):
    """Unit test case for the CSV class used in heatmapmaker."""
    def test_basic_default(self):
        rows = default.rows
        self.assertEqual(
            rows, 
            [
                ["col_titles", "default1", "default2", "default3"],
                ["col1", "1", "2", "3"],
                ["col2", "4", "5", "6"],
                ["col3", "7", "8", "9"]
            ]
        )
        cols = default.cols
        self.assertEqual(
            cols, 
            [
                ["col_titles", "col1", "col2", "col3"],
                ["default1", "1", "4", "7"],
                ["default2", "2", "5", "8"],
                ["default3", "3", "6", "9"]
            ]
        )
        row_titles = default.get_row_titles()
        self.assertEqual(row_titles, ["col1", "col2", "col3"]) 
        col_titles = default.get_col_titles()
        self.assertEqual(col_titles, ["default1", "default2", "default3"])

        row_data = default.get_data_per_row_without_titles()
        self.assertEqual(row_data, [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]])
        col_data = default.get_data_per_col_without_titles()
        self.assertEqual(col_data, [["1", "4", "7"], ["2", "5", "8"], ["3", "6", "9"]])


    def test_basic_semicolon(self):
        rows = semicolon.rows
        self.assertEqual(
            rows, 
            [
                ["col_titles", "semicolon1", "semicolon2", "semicolon3"],
                ["col1", "1", "2", "3"],
                ["col2", "4", "5", "6"],
                ["col3", "7", "8", "9"]
            ]
        )
        cols = semicolon.cols
        self.assertEqual(
            cols, 
            [
                ["col_titles", "col1", "col2", "col3"],
                ["semicolon1", "1", "4", "7"],
                ["semicolon2", "2", "5", "8"],
                ["semicolon3", "3", "6", "9"]
            ]
        )
        row_titles = semicolon.get_row_titles()
        self.assertEqual(row_titles, ["col1", "col2", "col3"]) 
        col_titles = semicolon.get_col_titles()
        self.assertEqual(col_titles, ["semicolon1", "semicolon2", "semicolon3"])

        row_data = semicolon.get_data_per_row_without_titles()
        self.assertEqual(row_data, [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]])
        col_data = semicolon.get_data_per_col_without_titles()
        self.assertEqual(col_data, [["1", "4", "7"], ["2", "5", "8"], ["3", "6", "9"]])


    def test_basic_no_titles(self):
        rows = no_titles.rows
        self.assertEqual(
            rows, 
            [
                ["1", "2", "3"],
                ["4", "5", "6"],
                ["7", "8", "9"]
            ]
        )
        cols = no_titles.cols
        self.assertEqual(
            cols, 
            [
                ["1", "4", "7"],
                ["2", "5", "8"],
                ["3", "6", "9"]
            ]
        )
        row_titles = no_titles.get_row_titles()
        self.assertEqual(row_titles, None) 
        col_titles = no_titles.get_col_titles()
        self.assertEqual(col_titles, None)

        row_data = no_titles.get_data_per_row_without_titles()
        self.assertEqual(row_data, [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]])
        col_data = no_titles.get_data_per_col_without_titles()
        self.assertEqual(col_data, [["1", "4", "7"], ["2", "5", "8"], ["3", "6", "9"]])


    def test_basic_col_titles(self):
        rows = col_only.rows
        self.assertEqual(
            rows, 
            [
                ["col_only1", "col_only2", "col_only3"],
                ["1", "2", "3"],
                ["4", "5", "6"],
                ["7", "8", "9"]
            ]
        )
        cols = col_only.cols
        self.assertEqual(
            cols, 
            [
                ["col_only1", "1", "4", "7"],
                ["col_only2", "2", "5", "8"],
                ["col_only3", "3", "6", "9"]
            ]
        )
        row_titles = col_only.get_row_titles()
        self.assertEqual(row_titles, None) 
        col_titles = col_only.get_col_titles()
        self.assertEqual(col_titles, ["col_only1", "col_only2", "col_only3"])

        row_data = col_only.get_data_per_row_without_titles()
        self.assertEqual(row_data, [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]])
        col_data = col_only.get_data_per_col_without_titles()
        self.assertEqual(col_data, [["1", "4", "7"], ["2", "5", "8"], ["3", "6", "9"]])


    def test_basic_row_titles(self):
        rows = row_only.rows
        self.assertEqual(
            rows, 
            [
                ["row_only1", "1", "2", "3"],
                ["row_only2", "4", "5", "6"],
                ["row_only3", "7", "8", "9"]
            ]
        )
        cols = row_only.cols
        self.assertEqual(
            cols, 
            [                
                ["row_only1", "row_only2", "row_only3"],
                ["1", "4", "7"],
                ["2", "5", "8"],
                ["3", "6", "9"]
            ]
        )
        row_titles = row_only.get_row_titles()
        self.assertEqual(row_titles, ["row_only1", "row_only2", "row_only3"]) 
        col_titles = row_only.get_col_titles()
        self.assertEqual(col_titles, None)

        row_data = row_only.get_data_per_row_without_titles()
        self.assertEqual(row_data, [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]])
        col_data = row_only.get_data_per_col_without_titles()
        self.assertEqual(col_data, [["1", "4", "7"], ["2", "5", "8"], ["3", "6", "9"]])


    def test_parse_data(self):
        data_as_strings = default.get_data_per_row_without_titles()
        data_as_floats = default.parse_data(data_as_strings)
        self.assertEqual(
            data_as_floats, 
            [
                [1.0, 2.0, 3.0], 
                [4.0, 5.0, 6.0], 
                [7.0, 8.0, 9.0]
            ]
        )


    def test_to_df_with_default(self):
        derived_dataframe = default.to_df()
        data = [
            [1.0, 2.0, 3.0], 
            [4.0, 5.0, 6.0], 
            [7.0, 8.0, 9.0]
        ]
        row_titles = ["col1", "col2", "col3"]
        col_titles = ["default1", "default2", "default3"]
        
        target_dataframe = pd.DataFrame(
            data,
            index = row_titles,
            columns = col_titles
        )
        assert_frame_equal(derived_dataframe, target_dataframe)


    def test_all_are_the_same_length(self):
        all_are_the_same_length = default.all_are_the_same_length
        self.assertTrue(
            all_are_the_same_length(
                [
                    [1, 1, 1, 1],
                    [2, 2, 2, 2],
                    [3, 3, 3, 3]
                ]
            )
        )
        self.assertFalse(
            all_are_the_same_length(
                [
                    [1, 1, 1],
                    [2, 2, 2, 2],
                    [3, 3, 3, 3]
                ]
            )
        )
        self.assertFalse(
            all_are_the_same_length(
                [
                    [1, 1, 1, 1],
                    [2, 2, 2],
                    [3, 3, 3, 3]
                ]
            )
        )
        self.assertFalse(
            all_are_the_same_length(
                [
                    [1, 1, 1, 1],
                    [2, 2, 2, 2],
                    [3, 3, 3, 3, 3]
                ]
            )
        )
        self.assertTrue(
            all_are_the_same_length(
                [
                    [1, 1, 1, 1],
                    (2, 2, 2, 2),
                    "3333"
                ]
            )
        )
                

if __name__ == "__main__":
    unittest.main()