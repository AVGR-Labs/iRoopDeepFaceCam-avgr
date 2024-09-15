import os

class Enviroment:
    """
    A class to manage environment variables related to directory paths.
    
    This class provides functionality to check if an environment variable
    points to a valid directory, and to retrieve or reset the variable.
    """
    
    def __init__(self):
        # Initializes the Enviroment class with a DEFAULT attribute set to None
        self.DEFAULT = None
    
    def ready(self, target):
        """
        Checks if the environment variable 'target' is set and points to a valid directory.
        
        Parameters:
            target (str): The name of the environment variable to check.
        
        Returns:
            bool: True if the variable is set and points to a valid directory, False otherwise.
        """
        self.DEFAULT = os.getenv(target)
        if self.DEFAULT and os.path.isdir(self.DEFAULT):
            return True
        return False
    
    def Default(self):
        """
        Returns the current value of self.DEFAULT and resets it to None.
        
        Returns:
            str: The value of self.DEFAULT before it was reset to None.
        """
        d = self.DEFAULT
        self.DEFAULT = None
        return d
