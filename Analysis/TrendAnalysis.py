import os
os.chdir("../")
from DataProcessing.DataLoad import getData

data=getData()
print(data.keys())


