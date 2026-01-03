import { Box, Typography, Stack, Paper, Chip, Alert, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import { 
  Error, 
  Warning, 
  Info, 
  CheckCircle, 
  ExpandMore,
  Description,
  Visibility,
  Assignment 
} from '@mui/icons-material';

interface ValidationFinding {
  rule_id: string;
  title: string;
  status: string;
  severity: string;
  message: string;
  evidence?: any[];
  evidence_details?: any[];
  candidate_documents?: any[];
  document_name?: string;
}

interface ValidationFindingsDisplayProps {
  findings: ValidationFinding[];
  onViewDocument?: (documentId: number, evidenceDetails?: any) => void;
}

// Clear category labels with descriptions
const SEVERITY_CONFIG = {
  critical: {
    label: 'Critical Issues',
    description: 'These issues must be resolved before the application can be approved',
    icon: <Error />,
    color: 'error' as const,
  },
  high: {
    label: 'High Priority',
    description: 'Significant issues that require attention',
    icon: <Warning />,
    color: 'warning' as const,
  },
  medium: {
    label: 'Medium Priority',
    description: 'Issues that should be reviewed',
    icon: <Warning />,
    color: 'warning' as const,
  },
  low: {
    label: 'Low Priority',
    description: 'Minor issues for consideration',
    icon: <Info />,
    color: 'info' as const,
  },
  info: {
    label: 'Informational',
    description: 'Observations and notes - no action required',
    icon: <Info />,
    color: 'info' as const,
  },
};

// Better status labels
const STATUS_LABELS: Record<string, { label: string; description: string }> = {
  missing: {
    label: 'Missing Information',
    description: 'Required information was not found in the documents',
  },
  incomplete: {
    label: 'Incomplete',
    description: 'Information is present but incomplete or unclear',
  },
  needs_review: {
    label: 'Needs Human Review',
    description: 'Human verification is required to confirm this information',
  },
  not_found: {
    label: 'Not Found',
    description: 'Expected information could not be located',
  },
  found: {
    label: 'Found',
    description: 'Information has been located',
  },
  passed: {
    label: 'Passed',
    description: 'This check has passed successfully',
  },
  failed: {
    label: 'Failed',
    description: 'This check has failed',
  },
};

// Parse rule_id to human-readable format
const formatRuleId = (ruleId: string): string => {
  // Convert R5 -> Rule 5, CERT_TYPE -> Certificate Type, etc.
  if (ruleId.startsWith('R') && /^\d+$/.test(ruleId.slice(1))) {
    return `Rule ${ruleId.slice(1)}`;
  }
  return ruleId
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
};

export default function ValidationFindingsDisplay({ findings, onViewDocument }: ValidationFindingsDisplayProps) {
  // Group by severity
  const groupedFindings = findings.reduce((acc, finding) => {
    const severity = finding.severity.toLowerCase();
    if (!acc[severity]) {
      acc[severity] = [];
    }
    acc[severity].push(finding);
    return acc;
  }, {} as Record<string, ValidationFinding[]>);

  // Remove duplicates based on rule_id + message
  const deduplicateFindings = (findings: ValidationFinding[]): ValidationFinding[] => {
    const seen = new Set<string>();
    return findings.filter(finding => {
      const key = `${finding.rule_id}:${finding.message}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  };

  if (findings.length === 0) {
    return (
      <Alert severity="success" icon={<CheckCircle />} sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>✅ All Checks Passed</Typography>
        <Typography variant="body2">
          No issues found - all validation checks have passed successfully!
        </Typography>
      </Alert>
    );
  }

  return (
    <Stack spacing={3}>
      {Object.entries(SEVERITY_CONFIG).map(([severity, config]) => {
        const severityFindings = deduplicateFindings(groupedFindings[severity] || []);
        if (severityFindings.length === 0) return null;

        return (
          <Paper key={severity} elevation={2} sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              {config.icon}
              <Typography variant="h6" color={`${config.color}.main`}>
                {config.label}
              </Typography>
              <Chip 
                label={severityFindings.length} 
                color={config.color} 
                size="small" 
              />
            </Box>
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontStyle: 'italic' }}>
              {config.description}
            </Typography>

            <Stack spacing={2}>
              {severityFindings.map((finding, index) => {
                const statusInfo = STATUS_LABELS[finding.status] || { 
                  label: finding.status, 
                  description: '' 
                };

                return (
                  <Box
                    key={`${finding.rule_id}-${index}`}
                    sx={{
                      p: 2.5,
                      border: '1px solid',
                      borderColor: `${config.color}.main`,
                      borderRadius: 1,
                      borderLeft: '4px solid',
                      borderLeftColor: `${config.color}.main`,
                      backgroundColor: `${config.color}.lighter`,
                    }}
                  >
                    <Box sx={{ display: 'flex', gap: 1, mb: 1.5, alignItems: 'center', flexWrap: 'wrap' }}>
                      <Chip 
                        label={formatRuleId(finding.rule_id)}
                        size="small" 
                        variant="outlined"
                        icon={<Assignment />}
                      />
                      <Chip 
                        label={statusInfo.label}
                        color={config.color} 
                        size="small" 
                      />
                      {finding.document_name && (
                        <Chip 
                          label={finding.document_name} 
                          size="small" 
                          icon={<Description />}
                          variant="outlined"
                        />
                      )}
                    </Box>

                    <Typography variant="h6" gutterBottom sx={{ fontSize: '1rem', fontWeight: 600 }}>
                      {finding.title || statusInfo.label}
                    </Typography>

                    <Typography variant="body1" sx={{ mb: 1 }}>
                      {finding.message}
                    </Typography>

                    {statusInfo.description && (
                      <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', mb: 1 }}>
                        {statusInfo.description}
                      </Typography>
                    )}

                    {/* Evidence Details */}
                    {finding.evidence_details && finding.evidence_details.length > 0 && (
                      <Accordion sx={{ mt: 2, backgroundColor: 'rgba(255,255,255,0.7)' }}>
                        <AccordionSummary expandIcon={<ExpandMore />}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Visibility fontSize="small" />
                            <Typography variant="body2" fontWeight="medium">
                              View Evidence ({finding.evidence_details.length} {finding.evidence_details.length === 1 ? 'source' : 'sources'})
                            </Typography>
                          </Box>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Stack spacing={1.5}>
                            {finding.evidence_details.map((evidence: any, idx: number) => (
                              <Box
                                key={idx}
                                sx={{
                                  p: 2,
                                  backgroundColor: 'background.paper',
                                  borderRadius: 1,
                                  border: '1px solid',
                                  borderColor: 'divider',
                                }}
                              >
                                {evidence.document_name && (
                                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                                    <Description fontSize="small" sx={{ mr: 0.5, verticalAlign: 'middle' }} />
                                    {evidence.document_name} - Page {evidence.page}
                                  </Typography>
                                )}
                                <Typography variant="body2" sx={{ fontStyle: 'italic', color: 'text.secondary' }}>
                                  "{evidence.snippet}"
                                </Typography>
                              </Box>
                            ))}
                          </Stack>
                        </AccordionDetails>
                      </Accordion>
                    )}

                    {/* Candidate Documents */}
                    {finding.candidate_documents && finding.candidate_documents.length > 0 && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                          Suggested documents to review:
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          {finding.candidate_documents.map((doc: any, idx: number) => (
                            <Chip
                              key={idx}
                              label={`${doc.document_name} (${(doc.confidence * 100).toFixed(0)}%)`}
                              size="small"
                              icon={<Description />}
                              onClick={() => onViewDocument && onViewDocument(doc.document_id)}
                              sx={{ cursor: 'pointer' }}
                            />
                          ))}
                        </Box>
                      </Box>
                    )}
                  </Box>
                );
              })}
            </Stack>
          </Paper>
        );
      })}
    </Stack>
  );
}
