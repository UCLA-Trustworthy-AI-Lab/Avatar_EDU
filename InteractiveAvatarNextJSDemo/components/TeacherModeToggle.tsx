import { useStreamingAvatarContext } from "./logic/context";
import { useEnglishTeacher } from "./logic/useEnglishTeacher";
import { Button } from "./Button";

export const TeacherModeToggle: React.FC = () => {
  const { isTeacherMode, setIsTeacherMode } = useStreamingAvatarContext();
  const { startTeachingSession, endTeachingSession } = useEnglishTeacher();

  const toggleTeacherMode = async () => {
    const newMode = !isTeacherMode;
    setIsTeacherMode(newMode);
    
    if (newMode) {
      // Start teaching session when entering teacher mode
      await startTeachingSession();
    } else {
      // End teaching session when exiting teacher mode
      await endTeachingSession();
    }
  };

  return (
    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
      <div>
        <h3 className="font-medium text-gray-800">
          {isTeacherMode ? "Ms. Sarah - English Teacher" : "Regular Chat Mode"}
        </h3>
        <p className="text-sm text-gray-600">
          {isTeacherMode 
            ? "Having a natural conversation to help you practice English"
            : "Switch to teacher mode for English practice"
          }
        </p>
      </div>
      
      <Button
        onClick={toggleTeacherMode}
        className={`px-4 py-2 rounded-lg font-medium transition-colors ${
          isTeacherMode
            ? "bg-green-600 hover:bg-green-700 text-white"
            : "bg-blue-600 hover:bg-blue-700 text-white"
        }`}
      >
        {isTeacherMode ? "Exit Teacher Mode" : "Start Teacher Mode"}
      </Button>
    </div>
  );
};