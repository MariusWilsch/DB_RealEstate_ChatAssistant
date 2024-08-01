import os, sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/lib/RepositoryPattern")

from RepositoryPattern import base_repository


class threads_repo(base_repository.BaseRepository):
    def __init__(self):
        super().__init__(table_name="threads", primary_key="thread_id")
    
    def create(self, data = None):
        """create a new thread
        Args:
            data (dict): data to be inserted
        Returns:
            dict: data of the created thread
        Description:
            This function creates a new thread in the database.
        """
        return super().create(data=data)

    def read(self, value, column):
        """read a thread
        Args:
            value (str): value of the thread
            column (str): column to be read
        Returns:
            dict: data of the thread
        Description:
            This function reads a thread from the database.
        """
        return super().read(value, column)

    def update(self, value, data, column=None):
        """
        Update a thread in the database.
        Args:
            value (str): value of the thread
            data (dict): data to be updated
            column (str): column to be updated
        Returns:
            dict: data of the updated thread
        Description:
            This function updates a thread in the database.
        """
        return super().update(value, data, column)

    def delete(self, value, column):
        """
        Delete a thread from the database.
        Args:
            value (str): value of the thread
            column (str): column to be deleted
        Returns:
            dict: data of the deleted thread
        Description:
            This function deletes a thread from the database.
        """
        return super().delete(value, column)

    def filter(self, thread, select):
        """
        Filter filterss based on the provided thread.
        Args:
            thread (dict): thread to be applied
            select (str): columns to be selected
        Returns:
            dict: data of the filtered filterss
        Description:
            This function thread filterss based on the provided thread.
        """
        return super().filter(thread, select)