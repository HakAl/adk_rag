/**
 * Login page component
 * Create as: src/pages/LoginPage.tsx
 */
import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, Navigate, Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Loader2, Eye, EyeOff, AlertCircle } from 'lucide-react';

export const LoginPage = () => {
  const [usernameOrEmail, setUsernameOrEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { user, login } = useAuth();
  const navigate = useNavigate();

  // Redirect if already logged in
  if (user && !loading) {
    return <Navigate to="/chat" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(usernameOrEmail, password);
      navigate('/chat');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="glass-card w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="gradient-text text-2xl sm:text-3xl text-center">
            Sign in
          </CardTitle>
          <p className="text-center text-muted-foreground text-sm">
            Access your VIBE Agent
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
              <label htmlFor="usernameOrEmail" className="block text-sm font-medium">
                Username or Email
              </label>
              <Input
                id="usernameOrEmail"
                type="text"
                required
                value={usernameOrEmail}
                onChange={(e) => setUsernameOrEmail(e.target.value)}
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
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full glass-button"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign in'
              )}
            </Button>

            <div className="text-center">
              <Link
                to="/register"
                className="text-sm text-primary hover:underline"
                tabIndex={loading ? -1 : 0}
              >
                Don't have an account? Register
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};