import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Container,
  Paper,
} from '@mui/material';
import { Login as LoginIcon } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!username || !password) {
      setError('Please enter both username and password');
      return;
    }

    setLoading(true);

    try {
      await login(username, password);

      // Redirect to dashboard or previous page
      const redirectTo = new URLSearchParams(window.location.search).get('redirect') || '/new-application';
      navigate(redirectTo);
    } catch (err: any) {
      console.error('Login failed:', err);
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          py: 4,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        }}
      >
        <Card sx={{ width: '100%', maxWidth: 450, boxShadow: 6 }}>
          <CardContent sx={{ p: 4 }}>
            {/* Header */}
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <Box
                sx={{
                  display: 'inline-flex',
                  p: 2,
                  borderRadius: '50%',
                  bgcolor: 'primary.main',
                  mb: 2,
                }}
              >
                <LoginIcon sx={{ fontSize: 40, color: 'white' }} />
              </Box>
              <Typography variant="h4" component="h1" gutterBottom fontWeight="600">
                Welcome Back
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Sign in to access the planning validation system
              </Typography>
            </Box>

            {/* Error Alert */}
            {error && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {error}
              </Alert>
            )}

            {/* Login Form */}
            <form onSubmit={handleSubmit}>
              <TextField
                fullWidth
                label="Username"
                variant="outlined"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading}
                autoComplete="username"
                autoFocus
                sx={{ mb: 2.5 }}
                inputProps={{ 'aria-label': 'Username' }}
              />

              <TextField
                fullWidth
                label="Password"
                type="password"
                variant="outlined"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                autoComplete="current-password"
                sx={{ mb: 3 }}
                inputProps={{ 'aria-label': 'Password' }}
              />

              <Button
                fullWidth
                type="submit"
                variant="contained"
                size="large"
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <LoginIcon />}
                sx={{ py: 1.5, fontWeight: 600 }}
                aria-label="Sign in button"
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>

            {/* Demo Credentials Info */}
            <Paper
              elevation={0}
              sx={{
                mt: 4,
                p: 3,
                bgcolor: 'info.lighter',
                borderRadius: 2,
                border: '1px solid',
                borderColor: 'info.light',
              }}
            >
              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, color: 'info.dark' }}>
                Demo Credentials
              </Typography>
              <Typography variant="body2" color="text.secondary" component="div" sx={{ mt: 1.5 }}>
                <Box component="ul" sx={{ pl: 2.5, m: 0, '& li': { mb: 0.5 } }}>
                  <li>
                    <strong>Officer:</strong> officer / demo123
                  </li>
                  <li>
                    <strong>Admin:</strong> admin / admin123
                  </li>
                  <li>
                    <strong>Planner:</strong> planner / planner123
                  </li>
                  <li>
                    <strong>Reviewer:</strong> reviewer / reviewer123
                  </li>
                  <li>
                    <strong>Guest:</strong> guest / guest123
                  </li>
                </Box>
              </Typography>
            </Paper>
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
};

export default Login;
