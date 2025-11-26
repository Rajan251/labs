# Merge Request Checklist

Use this checklist before merging any merge request to ensure quality and compliance.

## Code Quality

- [ ] Code follows project style guide and conventions
- [ ] No linting errors or warnings
- [ ] Code is properly commented and documented
- [ ] No commented-out code or debug statements
- [ ] Unit tests added or updated for new/changed functionality
- [ ] Integration tests pass
- [ ] Code coverage >= 80% (or project threshold)
- [ ] No duplicate code (DRY principle followed)

## Security

- [ ] SAST scan passed (no critical or high severity issues)
- [ ] Dependency scan passed (no critical or high severity vulnerabilities)
- [ ] Container scan passed (if applicable)
- [ ] No secrets or credentials committed to repository
- [ ] Security review completed (if required by policy)
- [ ] Input validation implemented for user-facing features
- [ ] SQL injection and XSS vulnerabilities addressed
- [ ] Authentication and authorization properly implemented

## Pipeline

- [ ] Pipeline passed all stages successfully
- [ ] Build completed without errors
- [ ] All tests passed (unit, integration, E2E)
- [ ] Container image built successfully
- [ ] Container image scanned for vulnerabilities
- [ ] No critical vulnerabilities in final image
- [ ] Pipeline duration is acceptable (< 30 minutes recommended)

## Deployment

- [ ] Review app deployed successfully
- [ ] Manual testing completed on review app
- [ ] Database migrations tested (if applicable)
- [ ] Database rollback plan documented (if schema changes)
- [ ] Environment variables documented in README or .env.example
- [ ] Configuration changes documented
- [ ] Feature flags configured (if applicable)

## Documentation

- [ ] README updated (if needed)
- [ ] API documentation updated (if API changes)
- [ ] Changelog updated with user-facing changes
- [ ] Deployment notes added (if special deployment steps required)
- [ ] Architecture diagrams updated (if architecture changed)
- [ ] Runbook updated (if operational procedures changed)

## Approvals

- [ ] Code review approved by at least 2 reviewers
- [ ] Security team approved (if security-sensitive changes)
- [ ] Product owner approved (if feature changes)
- [ ] Architecture review completed (if architectural changes)
- [ ] Database team approved (if schema changes)

## Pre-Merge

- [ ] Rebased on latest main/develop branch
- [ ] No merge conflicts
- [ ] Commits squashed (if required by project policy)
- [ ] Commit messages are descriptive and follow conventions
- [ ] Branch name follows naming convention
- [ ] All review comments addressed
- [ ] CI/CD pipeline green
- [ ] No breaking changes (or properly documented and communicated)

## Post-Merge Actions

- [ ] Monitor deployment to staging
- [ ] Verify functionality in staging environment
- [ ] Check application logs for errors
- [ ] Monitor performance metrics
- [ ] Update project board/issue tracker
- [ ] Notify stakeholders of deployment
- [ ] Delete feature branch (if applicable)

---

## Severity Thresholds

### Security Vulnerabilities

| Severity | Action |
|----------|--------|
| **Critical** | Must fix before merge |
| **High** | Must fix before merge |
| **Medium** | Should fix or document exception |
| **Low** | Can be addressed in future MR |

### Code Coverage

- Minimum: 80%
- Target: 90%
- New code: 100% (all new code should be tested)

---

## Notes

- This checklist can be customized per project
- Some items may not apply to all merge requests
- Use judgment to determine which items are relevant
- Document any exceptions or deviations
- Keep this checklist in `.gitlab/merge_request_templates/default.md` for automatic inclusion

---

## Example MR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Related Issues
Closes #123
Relates to #456

## Testing
- Unit tests: ✅
- Integration tests: ✅
- Manual testing: ✅

## Screenshots (if applicable)
[Add screenshots here]

## Deployment Notes
[Any special deployment instructions]

## Checklist
[Use checklist above]
```
