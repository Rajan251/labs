# Terraform Interview Questions Guide (2-5 Years Experience)

## Category 1: Most Frequently Asked Interview Questions

### Foundation & Core Concepts (Phone Screening: 15-30 min)

**1. [Beginner] What is Terraform and how does it differ from other IaC tools like Ansible or CloudFormation?**

*Looking for:* Understanding of declarative vs imperative, state management, multi-cloud support

**2. [Beginner] Explain the Terraform workflow (write, plan, apply).**

*Looking for:* Understanding of `terraform init`, `plan`, `apply`, `destroy`

**3. [Intermediate] What is Terraform state and why is it important?**

*Looking for:* State tracking, drift detection, locking, remote backends

**4. [Intermediate] How do you manage sensitive data in Terraform?**

*Looking for:* Sensitive variables, AWS Secrets Manager, Vault integration, `.tfvars` files in `.gitignore`

**5. [Beginner] What are Terraform providers and how do you use them?**

*Looking for:* Provider configuration, version constraints, multiple provider instances

**6. [Intermediate] Explain the difference between `count` and `for_each`.**

*Looking for:* When to use each, index vs key-based access, resource replacement behavior

**7. [Intermediate] What is a Terraform module and why would you use one?**

*Looking for:* Reusability, abstraction, versioning, module sources

**8. [Beginner] How do you handle dependencies between resources in Terraform?**

*Looking for:* Implicit dependencies (resource references), explicit `depends_on`

**9. [Intermediate] What is `terraform import` and when would you use it?**

*Looking for:* Importing existing infrastructure, limitations, state management

**10. [Intermediate] Explain Terraform's lifecycle meta-arguments.**

*Looking for:* `create_before_destroy`, `prevent_destroy`, `ignore_changes`

**11. [Beginner] What are data sources in Terraform?**

*Looking for:* Reading existing infrastructure, difference from resources

**12. [Intermediate] How do you manage multiple environments (dev, staging, prod) in Terraform?**

*Looking for:* Workspaces, separate directories, tfvars files, remote backends

**13. [Beginner] What is the purpose of `terraform.tfvars`?**

*Looking for:* Variable assignment, precedence, `.auto.tfvars`

**14. [Intermediate] Explain remote backends and state locking.**

*Looking for:* S3 + DynamoDB, Terraform Cloud, concurrent access prevention

**15. [Intermediate] What happens if you delete a resource from Terraform code?**

*Looking for:* Resource destruction on next apply, state removal

**16. [Beginner] How do you output values from Terraform?**

*Looking for:* Output blocks, `terraform output`, module outputs

**17. [Intermediate] What is the difference between local and remote provisioners?**

*Looking for:* `local-exec` vs `remote-exec`, when to avoid provisioners

**18. [Intermediate] How do you handle Terraform version constraints?**

*Looking for:* `required_version`, provider version constraints, lock files

**19. [Beginner] What is `terraform validate` and when do you use it?**

*Looking for:* Syntax validation, CI/CD integration

**20. [Intermediate] Explain the purpose of `.terraform.lock.hcl`.**

*Looking for:* Dependency lock file, provider version locking (Terraform 0.14+)

---

## Category 2: Scenario-Based Questions

### Real-World Problem Solving (Technical Round: 45-60 min)

**1. [Intermediate] Scenario: State File Corruption**

**Scenario:** Your team's Terraform state file has become corrupted and `terraform plan` is showing that it wants to destroy and recreate all resources. What steps would you take?

*Looking for:*
- Check state file backups (S3 versioning)
- Use `terraform state pull` to inspect
- `terraform import` to rebuild state
- State file recovery procedures
- Prevention: versioning, backups, state locking

**2. [Intermediate] Scenario: Drift Detection**

**Scenario:** Someone manually modified an EC2 instance's security group in the AWS console. How would you detect and resolve this drift?

*Looking for:*
- `terraform plan` shows changes
- `terraform refresh` to update state
- Decision: apply to revert or update code to match
- Prevention: IAM policies, CloudTrail monitoring

**3. [Advanced] Scenario: Large-Scale Refactoring**

**Scenario:** You need to rename 50 resources in your Terraform code without destroying and recreating them. How do you approach this?

*Looking for:*
- `terraform state mv` for each resource
- Scripting the state moves
- `moved` blocks (Terraform 1.1+)
- Testing in non-prod first
- State backup before changes

**4. [Intermediate] Scenario: Circular Dependency**

**Scenario:** You have a circular dependency: Security Group A references Security Group B, and B references A. How do you resolve this?

*Looking for:*
- Create security groups first without rules
- Add rules separately using `aws_security_group_rule`
- Understanding of Terraform's dependency graph

**5. [Advanced] Scenario: Multi-Region Deployment**

**Scenario:** You need to deploy identical infrastructure across 5 AWS regions. What's your approach?

*Looking for:*
- Module design for reusability
- Provider aliases for multiple regions
- `for_each` over regions map
- Workspace strategy or separate state files
- Considerations: region-specific AMIs, availability zones

**6. [Intermediate] Scenario: Secrets Leak**

**Scenario:** A developer accidentally committed AWS credentials in a `.tfvars` file to Git. What immediate and long-term actions do you take?

*Looking for:*
- Immediate: Rotate credentials, remove from Git history
- Long-term: Pre-commit hooks, secrets scanning (git-secrets, truffleHog)
- Use Secrets Manager/Vault
- `.gitignore` for `.tfvars`
- Team training

**7. [Advanced] Scenario: Zero-Downtime Deployment**

**Scenario:** You need to update a launch template for an Auto Scaling Group without downtime. Walk through your approach.

*Looking for:*
- Instance refresh configuration
- `create_before_destroy` lifecycle
- Blue-green deployment strategy
- Health checks and monitoring
- Rollback plan

**8. [Intermediate] Scenario: Cost Explosion**

**Scenario:** Your Terraform apply accidentally created 100 NAT Gateways instead of 3. How did this happen and how do you prevent it?

*Looking for:*
- Bug in `count` or `for_each` logic
- Always review `terraform plan` output
- Cost estimation tools (Infracost)
- Budget alerts in AWS
- Code review process

**9. [Advanced] Scenario: State File Locking Issue**

**Scenario:** `terraform apply` fails with "Error acquiring state lock" but no one is running Terraform. How do you troubleshoot?

*Looking for:*
- Check DynamoDB lock table
- Identify stale lock (crashed process)
- `terraform force-unlock` with caution
- Verify no concurrent runs (CI/CD)
- Implement proper locking timeout

**10. [Intermediate] Scenario: Module Version Conflict**

**Scenario:** Two teams are using different versions of your shared VPC module, causing inconsistencies. How do you manage this?

*Looking for:*
- Semantic versioning for modules
- Module registry (Terraform Cloud/Enterprise)
- Deprecation strategy
- Migration guide for breaking changes
- Version constraints in module calls

**11. [Advanced] Scenario: Cross-Account Resource Access**

**Scenario:** You need to create resources in Account A that reference resources in Account B. How do you handle this?

*Looking for:*
- Cross-account IAM roles
- Data sources to fetch remote resources
- Separate state files per account
- Provider aliases with assume_role
- Security considerations

**12. [Intermediate] Scenario: Plan Shows Unexpected Changes**

**Scenario:** `terraform plan` shows changes to resources you didn't modify. What could cause this?

*Looking for:*
- Provider version change
- API changes from cloud provider
- Computed attributes
- State drift from manual changes
- Default value changes in newer provider versions

**13. [Advanced] Scenario: Terraform in CI/CD**

**Scenario:** Design a CI/CD pipeline for Terraform that ensures safety and compliance.

*Looking for:*
- `terraform plan` on PR
- Manual approval for apply
- Automated testing (terratest)
- Security scanning (checkov, tfsec)
- State locking and backend configuration
- Separate pipelines per environment

**14. [Intermediate] Scenario: Resource Replacement**

**Scenario:** Changing an EC2 instance type forces replacement. How do you minimize downtime?

*Looking for:*
- `create_before_destroy` lifecycle
- Blue-green deployment
- Use Auto Scaling Groups instead
- Understanding of force-new attributes
- Backup/snapshot before change

**15. [Advanced] Scenario: Terraform Performance**

**Scenario:** `terraform plan` takes 30+ minutes for your infrastructure. How do you optimize?

*Looking for:*
- Split into smaller state files
- Use `-target` for specific resources (carefully)
- Reduce data source queries
- Parallelize with `-parallelism` flag
- Module optimization
- Consider Terraform Cloud for remote operations

---

## Category 3: Production-Level Questions

### Enterprise & Scale (Architecture Round: 60+ min)

**1. [Advanced] How do you design a Terraform module structure for a large organization with multiple teams?**

*Looking for:* Module hierarchy, versioning, registry, documentation, testing

**2. [Advanced] Explain your strategy for managing Terraform state at enterprise scale.**

*Looking for:* Separate states per environment/team, S3 + DynamoDB, encryption, access control, backup/recovery

**3. [Advanced] How do you implement policy as code with Terraform?**

*Looking for:* Sentinel (Terraform Enterprise), OPA, pre-apply checks, cost policies, security policies

**4. [Advanced] Describe your approach to Terraform security in production.**

*Looking for:* Least privilege IAM, state encryption, secrets management, audit logging, RBAC in Terraform Cloud

**5. [Advanced] How do you handle Terraform upgrades in production?**

*Looking for:* Test in lower environments, version constraints, state backup, rollback plan, upgrade guides

**6. [Advanced] What's your strategy for Terraform code review and approval?**

*Looking for:* PR process, automated plan, security scanning, cost estimation, manual approval gates

**7. [Advanced] How do you implement disaster recovery for Terraform-managed infrastructure?**

*Looking for:* State backups, multi-region, infrastructure as code in version control, runbooks, testing DR procedures

**8. [Advanced] Explain how you would implement compliance (PCI-DSS, SOC2) with Terraform.**

*Looking for:* Policy enforcement, audit trails, encryption, tagging, automated compliance checks

**9. [Advanced] How do you manage Terraform drift at scale?**

*Looking for:* Scheduled drift detection, automated remediation, alerts, prevention through IAM policies

**10. [Advanced] Describe your Terraform testing strategy.**

*Looking for:* Unit tests (terratest), integration tests, policy tests, cost tests, security scans

**11. [Advanced] How do you handle Terraform in a multi-cloud environment?**

*Looking for:* Provider management, module abstraction, separate states, cloud-agnostic patterns where possible

**12. [Advanced] What's your approach to Terraform documentation and knowledge sharing?**

*Looking for:* README per module, architecture diagrams, runbooks, wiki, training sessions

**13. [Advanced] How do you implement cost optimization with Terraform?**

*Looking for:* Tagging strategy, cost estimation tools, right-sizing, scheduled resources, budget alerts

**14. [Advanced] Explain your Terraform workspace strategy for large organizations.**

*Looking for:* When to use workspaces vs separate directories, limitations, naming conventions

**15. [Advanced] How do you handle Terraform in a regulated industry?**

*Looking for:* Audit logging, change approval, compliance automation, immutable infrastructure, evidence collection

**16. [Advanced] Describe your approach to Terraform module versioning and releases.**

*Looking for:* Semantic versioning, changelog, breaking change communication, deprecation policy

**17. [Advanced] How do you implement blue-green deployments with Terraform?**

*Looking for:* Duplicate infrastructure, traffic switching, rollback strategy, cost considerations

**18. [Advanced] What's your strategy for managing Terraform provider credentials?**

*Looking for:* Environment variables, assume role, Vault integration, credential rotation, least privilege

**19. [Advanced] How do you handle Terraform in a microservices architecture?**

*Looking for:* Separate states per service, shared modules, service mesh integration, coordination

**20. [Advanced] Explain your approach to Terraform observability and monitoring.**

*Looking for:* CloudWatch/Datadog for resources, Terraform Cloud runs, state change notifications, drift alerts

---

## Category 4: Advanced Technical Questions

### Internals & Deep Dive (Senior/Expert Level)

**1. [Advanced] Explain how Terraform builds its dependency graph.**

*Looking for:* Resource references, depends_on, parallel execution, topological sort

**2. [Advanced] What is the Terraform plugin protocol and how do providers work?**

*Looking for:* gRPC protocol, provider SDK, CRUD operations, schema definition

**3. [Advanced] How does Terraform handle resource updates (in-place vs replacement)?**

*Looking for:* ForceNew attributes, update methods, lifecycle rules, provider implementation

**4. [Advanced] Explain the difference between Terraform workspaces and multiple state files.**

*Looking for:* Use cases, limitations, isolation, when to use each

**5. [Advanced] How does Terraform Cloud's remote execution differ from local execution?**

*Looking for:* Remote backend, Sentinel policies, VCS integration, cost estimation, private registry

**6. [Advanced] What are Terraform's refresh-only mode and replace flag? (Terraform 1.5+)**

*Looking for:* `terraform apply -refresh-only`, `terraform apply -replace`, use cases

**7. [Advanced] Explain how Terraform handles provider configuration inheritance in modules.**

*Looking for:* Provider passing, aliases, configuration_aliases

**8. [Advanced] What is the purpose of Terraform's `moved` block? (Terraform 1.1+)**

*Looking for:* Refactoring without state commands, resource renaming, module restructuring

**9. [Advanced] How does Terraform's parallelism work and when would you adjust it?**

*Looking for:* Default 10, API rate limits, performance tuning, `-parallelism` flag

**10. [Advanced] Explain Terraform's type system and type constraints.**

*Looking for:* Primitive types, complex types (list, map, object), validation, type conversion

**11. [Advanced] What are Terraform's dynamic blocks and when should you use them?**

*Looking for:* Generating repeated nested blocks, for_each within resource, readability concerns

**12. [Advanced] How does Terraform handle provider plugin caching?**

*Looking for:* `.terraform` directory, plugin cache dir, network optimization

**13. [Advanced] Explain Terraform's expression evaluation and function usage.**

*Looking for:* Built-in functions, conditionals, string interpolation, for expressions

**14. [Advanced] What is the Terraform Registry API and how can you use it?**

*Looking for:* Module discovery, version constraints, private registry, API integration

**15. [Advanced] How does Terraform handle partial failures during apply?**

*Looking for:* State updates, tainted resources, error handling, recovery

**16. [Advanced] Explain Terraform's backend configuration and initialization.**

*Looking for:* Backend types, partial configuration, migration, reconfiguration

**17. [Advanced] What are Terraform's preconditions and postconditions? (Terraform 1.2+)**

*Looking for:* Validation, lifecycle checks, error messages, use cases

**18. [Advanced] How does Terraform integrate with HashiCorp Vault?**

*Looking for:* Vault provider, dynamic secrets, authentication methods, secret rotation

**19. [Advanced] Explain Terraform's override files and when to use them.**

*Looking for:* `override.tf`, `override.tf.json`, local development, testing

**20. [Advanced] What is Terraform's `-target` flag and why should it be used carefully?**

*Looking for:* Selective apply, dependency issues, state inconsistency, emergency use only

---

## Interview Round Recommendations

### Phone Screening (15-30 min)
- Questions 1-10 from Category 1 (Most Frequently Asked)
- Focus on basic concepts and terminology
- Assess foundational knowledge

### Technical Round (45-60 min)
- Questions 11-20 from Category 1
- Questions 1-10 from Category 2 (Scenarios)
- Mix of theory and practical problem-solving
- Code review exercise (provide sample Terraform code)

### Architecture/Design Round (60+ min)
- Questions from Category 3 (Production-Level)
- Questions 11-15 from Category 2 (Complex Scenarios)
- Design exercise: "Design Terraform structure for [specific use case]"
- Whiteboard architecture discussion

### Senior/Expert Round (60+ min)
- Questions from Category 4 (Advanced Technical)
- Selected questions from Category 3
- Deep dive into specific areas based on role requirements
- Custom provider development discussion (if relevant)

---

## Key Topics to Assess

**Must-Know (2-5 years experience):**
- ✅ State management and remote backends
- ✅ Module design and usage
- ✅ Variable and output handling
- ✅ Resource lifecycle and dependencies
- ✅ Multi-environment management
- ✅ Basic security practices

**Should-Know (3-5 years experience):**
- ✅ CI/CD integration
- ✅ Drift detection and remediation
- ✅ Advanced module patterns
- ✅ Terraform Cloud/Enterprise features
- ✅ Policy as code (Sentinel/OPA)
- ✅ Testing strategies

**Nice-to-Have (4-5 years experience):**
- ✅ Provider development
- ✅ Complex state management scenarios
- ✅ Performance optimization
- ✅ Multi-cloud strategies
- ✅ Custom tooling around Terraform

---

## Red Flags to Watch For

❌ Doesn't understand state management  
❌ Hardcodes credentials in code  
❌ Never used remote backends  
❌ Doesn't know the difference between count and for_each  
❌ Has never written a module  
❌ Doesn't understand provider versioning  
❌ Never used terraform import  
❌ Doesn't review terraform plan output  
❌ Uses provisioners for everything  
❌ No experience with CI/CD integration  

---

## Positive Indicators

✅ Mentions state locking and concurrent access  
✅ Discusses module versioning and testing  
✅ Understands security best practices  
✅ Has experience with Terraform in production  
✅ Knows when NOT to use Terraform  
✅ Familiar with recent Terraform features (1.5+)  
✅ Can explain trade-offs in design decisions  
✅ Has contributed to or maintains shared modules  
✅ Understands cost implications of infrastructure  
✅ Practices infrastructure testing  

---

**Document Version:** 1.0  
**Last Updated:** January 2026  
**Target Audience:** Hiring Managers, Technical Interviewers  
**Candidate Experience Level:** 2-5 years with Terraform
