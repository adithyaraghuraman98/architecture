import os


with open("delete-folders.txt",'w') as f:
  	for name in ([name for name in os.listdir(".") if os.path.isdir(name) and len(name.split('_____'))==2]):
  		f.write(name+"\n")
