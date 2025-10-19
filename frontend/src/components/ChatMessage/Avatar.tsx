import { LucideIcon } from 'lucide-react';

interface AvatarProps {
  icon: LucideIcon;
  variant: 'user' | 'bot';
}

export const Avatar = ({ icon: Icon, variant }: AvatarProps) => {
  const variantStyles = {
    user: 'bg-gradient-to-br from-sky-400 to-cyan-500 text-white',
    bot: 'bg-gradient-to-br from-primary to-accent text-primary-foreground',
  };

  return (
    <div
      className={`glass-avatar ${variantStyles[variant]} rounded-full p-1.5 sm:p-2 h-7 w-7 sm:h-8 sm:w-8 flex items-center justify-center flex-shrink-0`}
      aria-hidden="true"
    >
      <Icon className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
    </div>
  );
};