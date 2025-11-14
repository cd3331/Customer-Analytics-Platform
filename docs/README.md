# Documentation Index

Welcome to the Customer Analytics Platform documentation. This directory contains comprehensive guides for setting up, using, and maintaining the platform.

## Quick Start

New to the project? Start here:

1. **[Main README](../README.md)** - Project overview and quick start guide
2. **[Architecture](architecture/architecture.md)** - Understand the system design
3. **[Alteryx Setup](alteryx_workflow_instructions.md)** - Configure ETL workflows
4. **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

## Documentation Structure

### 📐 Architecture & Design

- **[architecture/architecture.md](architecture/architecture.md)**
  - Complete system architecture documentation
  - Component details and data flow
  - Technology stack overview
  - Design decisions and rationale
  - Scalability considerations

### 🚀 Deployment & Operations

- **[deployment/deployment_guide.md](deployment/deployment_guide.md)**
  - Production deployment checklist
  - Security hardening procedures
  - Monitoring and alerting setup
  - Backup and disaster recovery
  - Performance optimization
  - Cost estimates and management

### 🔧 Development Guides

- **[api/lambda_development.md](api/lambda_development.md)**
  - Lambda function development guide
  - Local development setup
  - Testing strategies (unit, integration)
  - Deployment procedures
  - Performance optimization
  - Security best practices

### 📊 ETL & Data Processing

- **[alteryx_workflow_instructions.md](alteryx_workflow_instructions.md)**
  - Step-by-step Alteryx setup
  - Workflow creation guide
  - Data connection configuration
  - Formula reference
  - Expected outputs

- **[alteryx_formulas.txt](alteryx_formulas.txt)**
  - Customer Lifetime Value (CLV) calculations
  - Churn prediction formulas
  - Risk score generation
  - Segmentation logic

### 🔍 API Reference

- **[api_reference.md](api_reference.md)**
  - Complete REST API documentation
  - Endpoint descriptions and parameters
  - Request/response examples
  - Error codes and handling
  - Code examples (Python, JavaScript, cURL)
  - Rate limits and authentication

### 🆘 Support & Troubleshooting

- **[troubleshooting.md](troubleshooting.md)**
  - Installation issues
  - AWS connection problems
  - Data generation errors
  - Alteryx workflow issues
  - Lambda function errors
  - Database connection problems
  - Cost and billing issues
  - General debugging tips

## Documentation by User Role

### For Developers

Essential reading:
1. [Architecture](architecture/architecture.md) - Understand the system
2. [Lambda Development Guide](api/lambda_development.md) - Write and deploy code
3. [API Reference](api_reference.md) - Integrate with the platform
4. [Troubleshooting](troubleshooting.md) - Debug issues

### For Data Engineers

Essential reading:
1. [Alteryx Workflow Instructions](alteryx_workflow_instructions.md) - Set up ETL
2. [Architecture](architecture/architecture.md) - Data flow understanding
3. [Alteryx Formulas](alteryx_formulas.txt) - Analytics calculations
4. [Troubleshooting](troubleshooting.md) - ETL debugging

### For DevOps/SRE

Essential reading:
1. [Deployment Guide](deployment/deployment_guide.md) - Production deployment
2. [Architecture](architecture/architecture.md) - Infrastructure overview
3. [Troubleshooting](troubleshooting.md) - Operational issues
4. [API Reference](api_reference.md) - Monitoring endpoints

### For Business Analysts

Essential reading:
1. [Main README](../README.md) - Project capabilities
2. [Alteryx Formulas](alteryx_formulas.txt) - Metric definitions
3. [Architecture](architecture/architecture.md) - Data sources and outputs

## Common Tasks

### Setting Up the Platform

1. Follow [Main README Quick Start](../README.md#quick-start)
2. Configure [Alteryx Workflows](alteryx_workflow_instructions.md)
3. Deploy to production using [Deployment Guide](deployment/deployment_guide.md)

### Developing New Features

1. Review [Architecture](architecture/architecture.md)
2. Set up local development per [Lambda Development Guide](api/lambda_development.md)
3. Write tests and deploy
4. Update [API Reference](api_reference.md) if adding endpoints

### Troubleshooting Issues

1. Check [Troubleshooting Guide](troubleshooting.md) for your specific issue
2. Review CloudWatch logs (see [Lambda Development Guide](api/lambda_development.md#monitoring--debugging))
3. Verify configuration in [Architecture docs](architecture/architecture.md)

### Monitoring Production

1. Set up alerts per [Deployment Guide](deployment/deployment_guide.md#phase-4-monitoring--alerting)
2. Monitor costs (see [Deployment Guide - Cost Estimates](deployment/deployment_guide.md#cost-estimates))
3. Review performance metrics

## Additional Resources

### External Documentation

- **AWS Services:**
  - [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
  - [Amazon S3 Documentation](https://docs.aws.amazon.com/s3/)
  - [Amazon RDS Documentation](https://docs.aws.amazon.com/rds/)
  - [Amazon DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)

- **Alteryx:**
  - [Alteryx Designer Cloud Documentation](https://help.alteryx.com/cloud)
  - [Alteryx Community Forums](https://community.alteryx.com/)

- **Power BI:**
  - [Power BI Documentation](https://docs.microsoft.com/en-us/power-bi/)
  - [Power BI Community](https://community.powerbi.com/)

### Project Resources

- **Repository:** [GitHub Repository](https://github.com/cd3331/customer-analytics-platform)
- **Issues:** [GitHub Issues](https://github.com/cd3331/customer-analytics-platform/issues)
- **Contact:** cd3331github@gmail.com

## Screenshots & Diagrams

Additional visual documentation available in:
- `docs/screenshots/` - Dashboard screenshots and UI examples
- `docs/architecture/` - Architecture diagrams

## Contributing to Documentation

Documentation contributions are welcome! Please:

1. Use Markdown format
2. Include code examples where applicable
3. Update this index when adding new docs
4. Test all code examples before committing
5. Use clear, concise language

### Documentation Standards

- **File naming:** Use lowercase with underscores (e.g., `deployment_guide.md`)
- **Headers:** Use descriptive, hierarchical headers
- **Code blocks:** Always specify language for syntax highlighting
- **Links:** Use relative paths for internal links
- **Examples:** Provide working examples for all code snippets

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-01-15 | Initial comprehensive documentation |
| 0.2 | 2024-09-30 | Added Alteryx instructions |
| 0.1 | 2024-09-16 | Initial project setup |

## Support

For questions or clarifications about the documentation:

1. **Check [Troubleshooting Guide](troubleshooting.md)** first
2. **Search [GitHub Issues](https://github.com/cd3331/customer-analytics-platform/issues)**
3. **Create new issue** with tag `documentation`
4. **Email:** cd3331github@gmail.com

---

**Documentation Status:** ✅ Complete and up-to-date
**Last Review:** 2024-01-15
**Maintained by:** Chandra Dunn
