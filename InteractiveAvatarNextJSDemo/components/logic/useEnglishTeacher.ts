import { useCallback } from "react";

export const useEnglishTeacher = () => {
  const startTeachingSession = useCallback(async () => {
    // Teacher mode is now handled by the avatar configuration
    // No separate session management needed
  }, []);

  const endTeachingSession = useCallback(async () => {
    // Teacher mode is handled by avatar configuration
  }, []);

  return {
    startTeachingSession,
    endTeachingSession,
  };
};