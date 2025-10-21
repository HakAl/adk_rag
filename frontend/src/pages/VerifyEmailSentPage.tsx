/**
 * Email verification sent page
 * Create as: src/pages/VerifyEmailSentPage.tsx
 */
import { useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Mail, Loader2, AlertCircle, CheckCircle } from 'lucide-react';

export const VerifyEmailSentPage = () => {
  const location = useLocation();
  const emailFromState = location.state?.email || '';

  const [email, setEmail] = useState(emailFromState);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleResend = async () => {
    if (!email) {
      setError('Please enter your email address');
      return;
    }

    setError('');
    setSuccess(false);
    setLoading(true);

    try {
      const response = await fetch('/resend-verification', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email })
      });

      if (!response.ok) {
        const errorData = await response.json();

        if (response.status === 429) {
          throw new Error('Too many requests. Please try again later.');
        }

        throw new Error(errorData.detail || 'Failed to resend verification email');
      }

      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resend email');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="glass-card w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
            <Mail className="h-6 w-6 text-primary" />
          </div>
          <CardTitle className="gradient-text text-2xl sm:text-3xl">
            Check Your Email
          </CardTitle>
          <p className="text-muted-foreground text-sm">
            We've sent a verification link to verify your account
          </p>
        </CardHeader>

        <CardContent className="space-y-4">
          {success && (
            <Card className="glass-card border-green-500/50">
              <CardContent className="p-3 flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-green-500">
                  Verification email sent! Please check your inbox and SPAM folder.
                </p>
              </CardContent>
            </Card>
          )}

          {error && (
            <Card className="glass-card border-red-500/50">
              <CardContent className="p-3 flex items-start gap-2">
                <AlertCircle className="h-4 w-4 text-red-500 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-500">{error}</p>
              </CardContent>
            </Card>
          )}

          <Card className="glass-card border-yellow-500/30">
            <CardContent className="p-3 space-y-2">
              <p className="text-sm font-medium">Important:</p>
              <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                <li>Check your SPAM/Junk folder if you don't see the email</li>
                <li>The verification link expires in 24 hours</li>
                <li>Click the link in the email to activate your account</li>
              </ul>
            </CardContent>
          </Card>

          <div className="space-y-2">
            <p className="text-sm text-center text-muted-foreground">
              Didn't receive the email?
            </p>

            <div className="space-y-2">
              <Input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="glass-input"
                disabled={loading}
              />

              <Button
                onClick={handleResend}
                disabled={loading || !email}
                className="w-full glass-button"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Sending...
                  </>
                ) : (
                  'Resend verification email'
                )}
              </Button>
            </div>
          </div>

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
};