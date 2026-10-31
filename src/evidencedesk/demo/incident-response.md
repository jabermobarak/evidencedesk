# Northstar Labs — Incident Response

This is fictional demonstration data, written for EvidenceDesk. It is not a real company's policy.

## Severity and response

A critical incident (SEV-1) must be acknowledged by the on-call engineer within 15 minutes. The incident commander posts status updates every 30 minutes until service is restored. SEV-2 incidents must be acknowledged within 60 minutes.

## Recovery

Production database backups run every 6 hours. Encrypted backups are retained for 30 days. The recovery time objective is 4 hours and the recovery point objective is 6 hours. A restore drill is performed once per quarter.

## Review

The incident commander completes a blameless postmortem within 5 business days after a SEV-1 incident. Follow-up actions must have an owner and a due date.
