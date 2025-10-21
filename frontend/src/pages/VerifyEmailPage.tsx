import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Loader2, CheckCircle, XCircle, Mail } from 'lucide-react';

export const VerifyEmailPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [status, setStatus] = useState<'loading' | 'success' | 'error' | 'input'>('loading');
  const [email, setEmail] = useState('');
  const [resendLoading, setResendLoading] = useState(false);
  const [resendError, setResendError] = useState('');

  useEffect(() => {
    if (token) {
      verifyToken(token);
    } else {
      setStatus('input');
    }
  }, [token]);

  const verifyToken = async (verificationToken: string) => {
    try {
      const response = await fetch(`/verify-email?token=${encodeURIComponent(verificationToken)}`, {
        credentials: 'include'
      });

      if (response.ok) {
        setStatus('success');
        // Redirect to login after 3 seconds
        setTimeout(() => {
          navigate('/sign-in', {
            state: { message: 'Email verified! Please sign in.' }
          });
        }, 3000);
      } else {
        setStatus('error');
      }
    } catch (error) {
      console.error('Verification error:', error);
      setStatus('error');
    }
  };

  const handleResend = async () => {
    if (!email) {
      setResendError('Please enter your email address');
      return;
    }

    setResendError('');
    setResendLoading(true);

    try {
      const response = await fetch('/resend-verification', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to resend verification email');
      }

      navigate('/verify-email-sent', { state: { email } });
    } catch (err) {
      setResendError(err instanceof Error ? err.message : 'Failed to resend email');
    } finally {
      setResendLoading(false);
    }
  };

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="glass-card w-full max-w-md">
          <CardContent className="p-8 text-center">
            <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary mb-4" />
            <p className="text-muted-foreground">Verifying your email...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="glass-card w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto w-12 h-12 rounded-full bg-green-500/10 flex items-center justify-center mb-4">
              <CheckCircle className="h-6 w-6 text-green-500" />
            </div>
            <CardTitle className="gradient-text text-2xl sm:text-3xl">
              Email Verified!
            </CardTitle>
          </CardHeader>
          <CardContent className="text-center space-y-4">
            <p className="text-muted-foreground">
              Your email has been successfully verified. You can now sign in to your account.
            </p>
            <p className="text-sm text-muted-foreground">
              Redirecting to login...
            </p>
            <Link to="/sign-in">
              <Button className="glass-button">
                Go to Login
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (status === 'error' || status === 'input') {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="glass-card w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center mb-4">
              {status === 'error' ? (
                <XCircle className="h-6 w-6 text-red-500" />
              ) : (
                <Mail className="h-6 w-6 text-primary" />
              )}
            </div>
            <CardTitle className="gradient-text text-2xl sm:text-3xl">
              {status === 'error' ? 'Verification Failed' : 'Verify Your Email'}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-center text-muted-foreground text-sm">
              {status === 'error'
                ? 'The verification link is invalid or has expired. Please request a new one.'
                : 'Enter your email to receive a new verification link.'}
            </p>

            {resendError && (
              <Card className="glass-card border-red-500/50">
                <CardContent className="p-3">
                  <p className="text-sm text-red-500">{resendError}</p>
                </CardContent>
              </Card>
            )}

            <div className="space-y-2">
              <label htmlFor="email" className="block text-sm font-medium">
                Email Address
              </label>
              <Input
                id="email"
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="glass-input"
                disabled={resendLoading}
              />
            </div>

            <Button
              onClick={handleResend}
              disabled={resendLoading || !email}
              className="w-full glass-button"
            >
              {resendLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Sending...
                </>
              ) : (
                'Send verification email'
              )}
            </Button>

            <div className="text-center pt-4">
              <Link
                to="/sign-in"
                className="text-sm text-primary hover:underline"
              >
                Back to login
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return null;
};