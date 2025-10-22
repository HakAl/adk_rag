import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, Navigate, Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Loader2, Eye, EyeOff, AlertCircle } from 'lucide-react';
import HCaptcha from '@hcaptcha/react-hcaptcha';
import { getApiUrl } from '../api/config';


const HCAPTCHA_SITEKEY = import.meta.env.VITE_HCAPTCHA_SITEKEY;

if (!HCAPTCHA_SITEKEY) {
  console.error('hCaptcha sitekey not configured');
}

export const RegisterPage = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [captchaToken, setCaptchaToken] = useState<string | null>(null);
  const [requireVisibleCaptcha, setRequireVisibleCaptcha] = useState(false);
  const [checkingCaptchaStatus, setCheckingCaptchaStatus] = useState(true);

  const { user } = useAuth();
  const navigate = useNavigate();
  const hcaptchaRef = useRef<HCaptcha>(null);

  // Check if visible CAPTCHA is required on mount
  useEffect(() => {
    const checkCaptchaStatus = async () => {
      try {
        const response = await fetch(getApiUrl('/register/captcha-status'));
        if (response.ok) {
          const data = await response.json();
          setRequireVisibleCaptcha(data.captcha_required);
        }
      } catch (err) {
        console.error('Failed to check captcha status:', err);
      } finally {
        setCheckingCaptchaStatus(false);
      }
    };

    checkCaptchaStatus();
  }, []);

  // Redirect if already logged in
  if (user && !loading) {
    return <Navigate to="/chat" replace />;
  }

  const handleCaptchaVerify = (token: string) => {
    setCaptchaToken(token);
    setError(''); // Clear any CAPTCHA errors
  };

  const handleCaptchaExpire = () => {
    setCaptchaToken(null);
  };

  const handleCaptchaError = (err: string) => {
    console.error('hCaptcha error:', err);
    setCaptchaToken(null);
    setError('CAPTCHA verification failed. Please try again.');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate passwords match
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    // Validate username format
    if (!/^[a-zA-Z0-9]+$/.test(username)) {
      setError('Username must contain only letters and numbers');
      return;
    }

    if (username.length < 3 || username.length > 30) {
      setError('Username must be 3-30 characters');
      return;
    }

    // Validate password length
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    // Check CAPTCHA if required
    if (requireVisibleCaptcha && !captchaToken) {
      setError('Please complete the CAPTCHA');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(getApiUrl('/register'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          username,
          email,
          password,
          captcha_token: captchaToken
        })
      });

      // Check if visible CAPTCHA is now required
      const requireCaptchaHeader = response.headers.get('X-Require-Visible-Captcha');
      if (requireCaptchaHeader === 'true') {
        setRequireVisibleCaptcha(true);
        setCaptchaToken(null);
        if (hcaptchaRef.current) {
          hcaptchaRef.current.resetCaptcha();
        }
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Registration failed');
      }

      const result = await response.json();
      // Navigate to verification page
      navigate('/verify-email-sent', { state: { email: result.email } });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');

      // Reset CAPTCHA on error
      if (hcaptchaRef.current) {
        hcaptchaRef.current.resetCaptcha();
      }
      setCaptchaToken(null);
    } finally {
      setLoading(false);
    }
  };

  if (checkingCaptchaStatus) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="glass-card w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="gradient-text text-2xl sm:text-3xl text-center">
            Create Account
          </CardTitle>
          <p className="text-center text-muted-foreground text-sm">
            Join VIBE Code
          </p>
        </CardHeader>

        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit}>
            {error && (
              <Card className="glass-card border-red-500/50">
                <CardContent className="p-3 flex items-start gap-2">
                  <AlertCircle className="h-4 w-4 text-red-500 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-500">{error}</p>
                </CardContent>
              </Card>
            )}

            <div className="space-y-2">
              <label htmlFor="username" className="block text-sm font-medium">
                Username
              </label>
              <Input
                id="username"
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Letters and numbers only"
                className="glass-input"
                disabled={loading}
              />
              <p className="text-xs text-muted-foreground">
                3-30 characters, letters and numbers only
              </p>
            </div>

            <div className="space-y-2">
              <label htmlFor="email" className="block text-sm font-medium">
                Email
              </label>
              <Input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="glass-input"
                disabled={loading}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="block text-sm font-medium">
                Password
              </label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="glass-input pr-10"
                  disabled={loading}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={loading}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Minimum 8 characters
              </p>
            </div>

            <div className="space-y-2">
              <label htmlFor="confirmPassword" className="block text-sm font-medium">
                Confirm Password
              </label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="glass-input pr-10"
                  disabled={loading}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  disabled={loading}
                  aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            {/* hCaptcha - invisible or visible based on failed attempts */}
            <div className="flex justify-center">
              <HCaptcha
                ref={hcaptchaRef}
                sitekey={HCAPTCHA_SITEKEY}
                onVerify={handleCaptchaVerify}
                onExpire={handleCaptchaExpire}
                onError={handleCaptchaError}
                size={requireVisibleCaptcha ? 'normal' : 'invisible'}
              />
            </div>

            {requireVisibleCaptcha && (
              <p className="text-xs text-yellow-600 text-center">
                ⚠️ Multiple failed attempts detected. Please complete the CAPTCHA.
              </p>
            )}

            <Button
              type="submit"
              disabled={loading || (requireVisibleCaptcha && !captchaToken)}
              className="w-full glass-button"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                'Create account'
              )}
            </Button>

            <div className="text-center">
              <Link
                to="/sign-in"
                className="text-sm text-primary hover:underline"
                tabIndex={loading ? -1 : 0}
              >
                Already have an account? Sign in
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};