import React, { useEffect, useState } from 'react';
import { Download, MonitorDown, Smartphone, X } from 'lucide-react';

export default function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showPrompt, setShowPrompt] = useState(false);
  const [showInstructions, setShowInstructions] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    const standalone =
      window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;
    setIsStandalone(Boolean(standalone));

    const handler = (event) => {
      event.preventDefault();
      setDeferredPrompt(event);
      setShowPrompt(true);
    };

    window.addEventListener('beforeinstallprompt', handler);
    const timer = window.setTimeout(() => {
      if (!standalone) setShowPrompt(true);
    }, 900);

    return () => {
      window.clearTimeout(timer);
      window.removeEventListener('beforeinstallprompt', handler);
    };
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) {
      setShowInstructions(true);
      return;
    }

    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    setDeferredPrompt(null);
    setShowPrompt(false);
  };

  if (!showPrompt || isStandalone) return null;

  return (
    <div className="fixed bottom-24 left-4 right-4 z-[9999] rounded-2xl border border-orange-500/70 bg-black/85 p-4 shadow-[0_24px_80px_rgba(0,0,0,0.55)] backdrop-blur-xl sm:left-auto sm:bottom-6 sm:right-6 sm:w-96">
      <button
        type="button"
        onClick={() => setShowPrompt(false)}
        className="absolute right-2 top-2 text-zinc-400 hover:text-white"
        aria-label="Dismiss install prompt"
      >
        <X className="h-5 w-5" />
      </button>

      <div className="flex items-start gap-3">
        <div className="rounded-xl bg-orange-500/20 p-3">
          <Download className="h-6 w-6 text-orange-400" />
        </div>
        <div className="flex-1">
          <h3 className="mb-1 font-semibold text-white">Install Time Tracker⚡</h3>
          <p className="mb-3 text-sm text-zinc-400">
            Add it to your home screen for faster launch and offline-ready clock actions.
          </p>

          {showInstructions && (
            <div className="mb-3 space-y-2 rounded-xl bg-zinc-950/70 p-3 text-xs text-zinc-300">
              <div className="flex gap-2">
                <MonitorDown className="mt-0.5 h-4 w-4 text-orange-400" />
                <span>Desktop Chrome: use the address bar install icon or browser menu.</span>
              </div>
              <div className="flex gap-2">
                <Smartphone className="mt-0.5 h-4 w-4 text-orange-400" />
                <span>Mobile: open the browser menu, then choose Add to Home screen.</span>
              </div>
            </div>
          )}

          <button
            type="button"
            onClick={handleInstall}
            className="w-full rounded-xl bg-orange-500 px-4 py-2 font-medium text-white hover:bg-orange-600"
          >
            {deferredPrompt ? 'Install App' : showInstructions ? 'Keep Visible' : 'Install App'}
          </button>
        </div>
      </div>
    </div>
  );
}
