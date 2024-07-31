import os, sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/lib/RepositoryPattern")

from RepositoryPattern import base_repository


class user_repo(base_repository.BaseRepository):
    def __init__(self):
        super().__init__(table_name="users", primary_key="user_id")
    
    def create(self, data = None):
        """create a new user
        Args:
            data (dict): data to be inserted
        Returns:
            dict: data of the created user
        Description:
            This function creates a new user in the database.
        """
        return super().create(data=data)

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

    def update(self, value, data, column=None):
        """
        Update a user in the database.
        Args:
            value (str): value of the user
            data (dict): data to be updated
            column (str): column to be updated
        Returns:
            dict: data of the updated user
        Description:
            This function updates a user in the database.
        """
        return super().update(value, data, column)

    def delete(self, value, column):
        """
        Delete a user from the database.
        Args:
            value (str): value of the user
            column (str): column to be deleted
        Returns:
            dict: data of the deleted user
        Description:
            This function deletes a user from the database.
        """
        return super().delete(value, column)

    def filter(self, filters, select):
        """
        Filter users based on the provided filters.
        Args:
            filters (dict): filters to be applied
            select (str): columns to be selected
        Returns:
            dict: data of the filtered users
        Description:
            This function filters users based on the provided filters.
        """
        return super().filter(filters, select)