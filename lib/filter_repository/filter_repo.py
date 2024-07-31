import os, sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/lib/RepositoryPattern")

from RepositoryPattern import base_repository


class filter_repo(base_repository.BaseRepository):
    def __init__(self):
        super().__init__()
        self.table_name = "filters"
        self.primary_key = "filter_id"
    
    def create(self, data):
        """create a new filters
        Args:
            data (dict): data to be inserted
        Returns:
            dict: data of the created filters
        Description:
            This function creates a new filters in the database.
        """
        return super().create(data)

    def read(self, value, column):
        """read a filters
        Args:
            value (str): value of the filters
            column (str): column to be read
        Returns:
            dict: data of the filters
        Description:
            This function reads a filters from the database.
        """
        return super().read(value, column)

    def update(self, value, data, column):
        return super().update(value, data, column)

    def delete(self, value, column):
        return super().delete(value, column)

    def filter(self, filters, select):
        return super().filter(filters, select)