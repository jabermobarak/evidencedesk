# Northstar Labs — Security Standard

This is fictional demonstration data, written for EvidenceDesk. It is not a security standard for real deployment.

## Account access

Multi-factor authentication is required for all production systems. Production access requests require approval from the service owner and the security team. Access permissions are reviewed every 90 days. Access for departing employees is revoked within 4 hours of notification.

## Credentials

API keys must be stored in the approved secrets manager. API keys must never be committed to Git repositories or included in application logs. Service credentials are rotated every 60 days.

## Data handling

Customer personal data must be encrypted in transit and at rest. Customer data must not be sent to external AI providers without a documented processing agreement. Security incidents must be reported to the security team immediately.
