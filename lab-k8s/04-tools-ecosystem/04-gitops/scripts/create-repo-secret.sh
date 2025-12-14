#!/bin/bash

# Create ArgoCD Repository Secret
# This script adds a private Git repository credential to ArgoCD.

REPO_URL=$1
USERNAME=$2
PASSWORD=$3 # Or Personal Access Token (PAT)

if [ -z "$REPO_URL" ] || [ -z "$USERNAME" ] || [ -z "$PASSWORD" ]; then
  echo "Usage: $0 <repo-url> <username> <password/token>"
  exit 1
fi

echo "Adding repository credentials for $REPO_URL..."

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: repo-$(echo $REPO_URL | md5sum | cut -c1-8)
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: repository
stringData:
  type: git
  url: $REPO_URL
  username: $USERNAME
  password: $PASSWORD
EOF

echo "Repository credentials added."
