import { MAX_MESSAGE_LENGTH } from '../../utils/messageValidation';

interface CharacterCounterProps {
  count: number;
  isApproachingLimit: boolean;
  isOverLimit: boolean;
}

export const CharacterCounter = ({
  count,
  isApproachingLimit,
  isOverLimit
}: CharacterCounterProps) => {
  if (count === 0) return null;

  return (
    <div
      className={`absolute bottom-2 right-2 text-xs transition-colors ${
        isOverLimit
          ? 'text-red-500 font-semibold'
          : isApproachingLimit
          ? 'text-yellow-500'
          : 'text-gray-400'
      }`}
      aria-live="polite"
    >
      {count}/{MAX_MESSAGE_LENGTH}
    </div>
  );
};