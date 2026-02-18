import { useCallback } from "react";

import { useStreamingAvatarContext } from "./context";

export const useVoiceChat = () => {
  const {
    avatarRef,
    isMuted,
    setIsMuted,
    isVoiceChatActive,
    setIsVoiceChatActive,
    isVoiceChatLoading,
    setIsVoiceChatLoading,
  } = useStreamingAvatarContext();

  const startVoiceChat = useCallback(
    async (isInputAudioMuted?: boolean, deviceId?: string) => {
      if (!avatarRef.current) {
        console.error('Avatar ref not available');
        return;
      }
      
      try {
        // First, enumerate all available audio devices
        const devices = await navigator.mediaDevices.enumerateDevices();
        const audioInputs = devices.filter(device => device.kind === 'audioinput');
        
        // Detect clamshell mode issues
        const hasExternalMic = audioInputs.some(d => d.label.toLowerCase().includes('external'));
        const hasAirPods = audioInputs.some(d => d.label.toLowerCase().includes('airpods'));
        const hasBuiltIn = audioInputs.some(d => d.label.toLowerCase().includes('built-in'));
        
        if (hasExternalMic && hasAirPods) {
          console.warn('CLAMSHELL MODE DETECTED: External mic + AirPods found - this causes audio routing conflicts');
        }
        
        // Force the website to use system default instead of built-in
        let stream: MediaStream | null = null;
        
        // Strategy 1: Force use non-built-in devices first, prioritize AirPods in clamshell mode
        const nonBuiltInDevices = audioInputs.filter(device => 
          !device.label.toLowerCase().includes('built-in') &&
          !device.label.toLowerCase().includes('internal')
        );
        
        // In clamshell mode, prioritize AirPods over external monitor microphones
        if (hasExternalMic && hasAirPods) {
          nonBuiltInDevices.sort((a, b) => {
            const aIsAirPods = a.label.toLowerCase().includes('airpods');
            const bIsAirPods = b.label.toLowerCase().includes('airpods');
            if (aIsAirPods && !bIsAirPods) return -1; // AirPods first
            if (bIsAirPods && !aIsAirPods) return 1;
            return 0;
          });
        }
        
        // Try selected device first if it's not built-in
        if (deviceId) {
          const selectedDeviceInfo = audioInputs.find(d => d.deviceId === deviceId);
          if (selectedDeviceInfo && !selectedDeviceInfo.label.toLowerCase().includes('built-in')) {
            try {
              stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                  deviceId: { exact: deviceId },
                  echoCancellation: true,
                  noiseSuppression: true,
                  autoGainControl: true
                }
              });
            } catch (error) {
              // Selected non-built-in device failed, will try next strategy
            }
          }
        }
        
        // Strategy 2: Try all non-built-in devices
        if (!stream && nonBuiltInDevices.length > 0) {
          for (const device of nonBuiltInDevices) {
            try {
              stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                  deviceId: { exact: device.deviceId },
                  echoCancellation: true,
                  noiseSuppression: true,
                  autoGainControl: true
                }
              });
              break;
            } catch (error) {
              // Device failed, try next one
            }
          }
        }
        
        // Strategy 3: If we still don't have stream, try selected device even if built-in
        if (!stream && deviceId) {
          try {
            stream = await navigator.mediaDevices.getUserMedia({
              audio: {
                deviceId: { exact: deviceId },
                echoCancellation: false,
                noiseSuppression: false,
                autoGainControl: false
              }
            });
          } catch (error) {
            // Selected device (any) failed, will try system default
          }
        }
        
        // Strategy 4: Last resort - try system default (no device ID)
        if (!stream) {
          try {
            stream = await navigator.mediaDevices.getUserMedia({
              audio: true
            });
          } catch (error) {
            // System default failed
          }
        }
        
        if (!stream) {
          throw new Error('Could not access any microphone device');
        }
        
        setIsVoiceChatLoading(true);
        await avatarRef.current?.startVoiceChat({
          isInputAudioMuted: false, // Always start unmuted for voice input
        });
        setIsVoiceChatLoading(false);
        setIsVoiceChatActive(true);
        setIsMuted(false); // Start unmuted so user can speak immediately
      } catch (error) {
        console.error('Voice chat error:', error);
        setIsVoiceChatLoading(false);
      }
    },
    [avatarRef, setIsMuted, setIsVoiceChatActive, setIsVoiceChatLoading],
  );

  const stopVoiceChat = useCallback(() => {
    if (!avatarRef.current) return;
    avatarRef.current?.closeVoiceChat();
    setIsVoiceChatActive(false);
    setIsMuted(true);
  }, [avatarRef, setIsMuted, setIsVoiceChatActive]);

  const muteInputAudio = useCallback(() => {
    if (!avatarRef.current) return;
    avatarRef.current?.muteInputAudio();
    setIsMuted(true);
  }, [avatarRef, setIsMuted]);

  const unmuteInputAudio = useCallback(() => {
    if (!avatarRef.current) return;
    avatarRef.current?.unmuteInputAudio();
    setIsMuted(false);
  }, [avatarRef, setIsMuted]);

  return {
    startVoiceChat,
    stopVoiceChat,
    muteInputAudio,
    unmuteInputAudio,
    isMuted,
    isVoiceChatActive,
    isVoiceChatLoading,
  };
};
