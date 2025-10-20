import { Message } from '../api/backend/chat.ts';

export const useEasterEggs = () => {
  const checkEasterEgg = (input: string): Message | null => {
    const trimmedInput = input.trim().toLowerCase();

    if (trimmedInput === 'yabadabadoo!') {
      return {
        id: `easter-${Date.now()}`,
        question: input.trim(),
        answer: "🦴 Yabba-Dabba-Doo! Fred Flintstone here! I'm an AI now because the stone tablet upgrade finally came through. Wilma says hi! 🦕",
        timestamp: Date.now()
      };
    }

    if (trimmedInput === 'giggity') {
      return {
        id: `easter-${Date.now()}`,
        question: input.trim(),
        answer: `# 🎉 Giggity Giggity Goo!

**Congratulations!** You've unlocked the *secret giggity counter*.

## Current Stats:
- **Giggities given**: ∞
- **Alright level**: Maximum
- **Coolness factor**: Off the charts

\`Warning: Excessive giggity may cause spontaneous laughter\`

> "Who else but Quagmire?" - Everyone`,
        timestamp: Date.now()
      };
    }

    return null;
  };

  return { checkEasterEgg };
};