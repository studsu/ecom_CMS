#!/bin/bash

# Navigate to the directory containing your Git repository (replace 'path/to/your/repo' with the actual path)
cd /home/rd/smokeking.in
# Get the current date and time
current_datetime=$(date +"%Y-%m-%d %H:%M:%S")

# Perform git add to stage all changes
git add .

# Perform git commit with the current date and time as the commit message
git commit -m "Server-Commit on $current_datetime"

# Perform git push to push changes to the remote repository
git push origin main   # Replace 'main' with your branch name if it's different

