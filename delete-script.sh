for f in $(cat delete-folders.txt) ; do 
  rm -rf "$f"
done
