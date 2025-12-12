# Terraform Lab

## 1. Introduction
**Terraform** is an infrastructure as code tool that lets you build, change, and version cloud and on-prem resources safely and efficiently.

## 2. Lab Setup

In this lab, we will use the `local` provider to manage files, avoiding the need for cloud credentials.

### Prerequisites
*   `terraform` CLI installed.

### Step 1: Initialize
Run `terraform init` in this directory.

### Step 2: Plan
Run `terraform plan`.
You should see that Terraform plans to create a file named `hello.txt`.

### Step 3: Apply
Run `terraform apply`. Type `yes`.
Check the file:
```bash
cat hello.txt
```

### Step 4: Modify
Edit `main.tf` and change the content.
Run `terraform apply` again.
See how Terraform updates the file in place.

### Step 5: Destroy
Run `terraform destroy`.
The file `hello.txt` will be deleted.

## 3. Code
See `main.tf`.
