import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface ErrorAlertProps {
  title?: string;
  message: string;
  className?: string;
}

export const ErrorAlert = ({
  title = 'Error',
  message,
  className = ''
}: ErrorAlertProps) => {
  return (
    <Card
      className={`border-red-500 bg-red-950/20 ${className}`}
      role="alert"
    >
      <CardHeader className="p-3 sm:p-6">
        <CardTitle className="text-red-500 text-base sm:text-lg">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-3 sm:p-6 pt-0">
        <p className="text-red-400 text-sm">{message}</p>
      </CardContent>
    </Card>
  );
};