import os, sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/lib/RepositoryPattern")

from RepositoryPattern import base_repository


class user_repo(base_repository.BaseRepository):
    def __init__(self):
        super().__init__()
        self.table_name = "users"
        self.primary_key = "user_id"
    
    def create(self, data):
        """create a new user
        Args:
            data (dict): data to be inserted
        Returns:
            dict: data of the created user
        Description:
            This function creates a new user in the database.
        """
        return super().create(data)

    def read(self, value, column):
        """read a user
        Args:
            value (str): value of the user
            column (str): column to be read
        Returns:
            dict: data of the user
        Description:
            This function reads a user from the database.
        """
        return super().read(value, column)

    def update(self, value, data, column):
        return super().update(value, data, column)

    def delete(self, value, column):
        return super().delete(value, column)

    def filter(self, filters, select):
        return super().filter(filters, select)