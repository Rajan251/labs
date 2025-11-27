# ============================================================================
# Makefile for Terraform + Ansible Project
# ============================================================================
# Provides convenient targets for common operations
# ============================================================================

.PHONY: help init plan apply configure deploy destroy clean verify

# Default target
.DEFAULT_GOAL := help

# Directories
TERRAFORM_DIR := terraform
ANSIBLE_DIR := ansible

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

## help: Display this help message
help:
	@echo "$(BLUE)Terraform + Ansible Makefile$(NC)"
	@echo ""
	@echo "Available targets:"
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## /  /' | column -t -s ':'

## init: Initialize Terraform
init:
	@echo "$(BLUE)Initializing Terraform...$(NC)"
	@cd $(TERRAFORM_DIR) && terraform init

## validate: Validate Terraform configuration
validate:
	@echo "$(BLUE)Validating Terraform configuration...$(NC)"
	@cd $(TERRAFORM_DIR) && terraform validate

## plan: Plan Terraform changes
plan:
	@echo "$(BLUE)Planning Terraform changes...$(NC)"
	@cd $(TERRAFORM_DIR) && terraform plan

## apply: Apply Terraform changes
apply:
	@echo "$(BLUE)Applying Terraform changes...$(NC)"
	@cd $(TERRAFORM_DIR) && terraform apply

## output: Show Terraform outputs
output:
	@cd $(TERRAFORM_DIR) && terraform output

## configure: Run Ansible playbook
configure:
	@echo "$(BLUE)Configuring servers with Ansible...$(NC)"
	@cd $(ANSIBLE_DIR) && ansible-playbook -i inventory/hosts.ini setup.yml

## ping: Test Ansible connectivity
ping:
	@echo "$(BLUE)Testing Ansible connectivity...$(NC)"
	@cd $(ANSIBLE_DIR) && ansible all -i inventory/hosts.ini -m ping

## deploy: Full deployment (Terraform + Ansible)
deploy:
	@echo "$(BLUE)Running full deployment...$(NC)"
	@./scripts/deploy.sh

## destroy: Destroy all infrastructure
destroy:
	@echo "$(YELLOW)Destroying infrastructure...$(NC)"
	@./scripts/destroy.sh

## clean: Clean generated files
clean:
	@echo "$(BLUE)Cleaning generated files...$(NC)"
	@rm -f $(ANSIBLE_DIR)/inventory/hosts.ini
	@rm -f $(TERRAFORM_DIR)/tfplan
	@rm -f $(TERRAFORM_DIR)/.terraform.lock.hcl
	@rm -rf $(TERRAFORM_DIR)/.terraform
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

## verify: Verify deployment
verify:
	@echo "$(BLUE)Verifying deployment...$(NC)"
	@cd $(ANSIBLE_DIR) && ansible all -i inventory/hosts.ini -m shell -a "uptime"

## ssh-web: SSH to first web server
ssh-web:
	@cd $(TERRAFORM_DIR) && \
	IP=$$(terraform output -json web_instance_public_ips | jq -r '.[0]') && \
	ssh -i ~/.ssh/terraform-key ubuntu@$$IP

## ssh-app: SSH to first app server
ssh-app:
	@cd $(TERRAFORM_DIR) && \
	IP=$$(terraform output -json app_instance_public_ips | jq -r '.[0]') && \
	ssh -i ~/.ssh/terraform-key ubuntu@$$IP

## logs: Show Terraform and Ansible logs
logs:
	@echo "$(BLUE)Recent Terraform state:$(NC)"
	@cd $(TERRAFORM_DIR) && terraform show | head -50
	@echo ""
	@echo "$(BLUE)Ansible inventory:$(NC)"
	@cat $(ANSIBLE_DIR)/inventory/hosts.ini 2>/dev/null || echo "No inventory file found"

## fmt: Format Terraform files
fmt:
	@echo "$(BLUE)Formatting Terraform files...$(NC)"
	@cd $(TERRAFORM_DIR) && terraform fmt -recursive

## lint: Lint Ansible playbooks
lint:
	@echo "$(BLUE)Linting Ansible playbooks...$(NC)"
	@cd $(ANSIBLE_DIR) && ansible-lint setup.yml || true

## test: Run tests
test: validate ping
	@echo "$(GREEN)✅ All tests passed$(NC)"
