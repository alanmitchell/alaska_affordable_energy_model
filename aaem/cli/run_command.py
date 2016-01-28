"""
run_command.py

    A commad for the cli to run the model
"""
import pycommand
from aaem import driver
import os.path

class RunCommand(pycommand.CommandBase):
    """
    run command class
    """
    usagestr = ('usage: run path_to_model_run '
                                    '[list_of_communities (with underscores)] ')
    description = 'Run model for given communities. (default = all communities)'

    def run(self):
        """
        run the command
        """
        if self.args and os.path.exists(self.args[0]):
            base = os.path.abspath(self.args[0])
        else:
            print  "run needs a directory"
            return 0
        
        config = os.path.join(base,"config")
        if len(self.args[1:]) != 0:
            coms = self.args[1:]
        else:
            coms = [a for a in os.listdir(config) if '.' not in a]
        
        batch = {}
        for com in coms:
            batch[com] = os.path.join(config,com,com+"_driver.yaml")
        
        driver.run(batch, "")