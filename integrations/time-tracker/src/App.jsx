import { initialSeats, checkoutAttempt, billingMessage } from './billing-selection.mjs';

import React, { useEffect, useMemo, useState } from 'react';
import {
  Clock,
  CalendarDays,
  MapPin,
  Play,
  Square,
  Coffee,
  ChevronLeft,
  ChevronRight,
  Calendar,
  Flag,
  Settings,
  Truck,
  Navigation,
  MoreHorizontal,
  Plus,
  Building2,
  TrendingUp,
  Edit3,
  Trash2,
  X,
  WifiOff,
  RefreshCw,
} from 'lucide-react';
import InstallPrompt from './components/InstallPrompt';
import { isSupabaseConfigured, supabase } from './supabaseClient';

const defaultWorkTypes = [
  { id: 'job_site', code: 'job_site', label: 'Job Site', icon: Flag, color: 'orange' },
  { id: 'setup', code: 'setup', label: 'Setup', icon: Settings, color: 'blue' },
  { id: 'teardown', code: 'teardown', label: 'Teardown', icon: Truck, color: 'purple' },
  { id: 'travel', code: 'travel', label: 'Travel Time', icon: Navigation, color: 'green' },
  { id: 'other', code: 'other', label: 'Other', icon: MoreHorizontal, color: 'slate' },
];

const APP_NAME = 'Time Tracker⚡';

const workTypeIconMap = {
  job_site: Flag,
  flagging: Flag,
  setup: Settings,
  teardown: Truck,
  travel: Navigation,
  other: MoreHorizontal,
};

const workTypeColorFallback = {
  job_site: 'orange',
  flagging: 'orange',
  setup: 'blue',
  teardown: 'purple',
  travel: 'green',
  other: 'slate',
};

const formatDuration = (ms) => {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const hours = String(Math.floor(totalSeconds / 3600)).padStart(2, '0');
  const minutes = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, '0');
  const seconds = String(totalSeconds % 60).padStart(2, '0');
  return `${hours}:${minutes}:${seconds}`;
};

const formatTime = (value) =>
  new Date(value).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });

const formatDate = (value) =>
  new Date(value).toLocaleDateString([], {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

const formatShortDate = (value) =>
  new Date(value).toLocaleDateString([], { month: 'short', day: 'numeric' });

const formatSegmentDuration = (segment, fallbackEnd) =>
  formatDuration(new Date(segment.ended_at ?? fallbackEnd ?? new Date()) - new Date(segment.started_at));

const QUEUE_STORAGE_PREFIX = 'work-zone-offline-queue-v2';
const OFFLINE_ENTRY_STORAGE_PREFIX = 'work-zone-offline-active-entry-v2';
const OFFLINE_SEGMENT_STORAGE_PREFIX = 'work-zone-offline-active-segment-v1';

const emptySiteForm = {
  name: '',
  client: '',
  address: '',
  status: 'active',
};

const readStoredJson = (key, fallback) => {
  if (typeof window === 'undefined') return fallback;

  try {
    const stored = window.localStorage.getItem(key);
    return stored ? JSON.parse(stored) : fallback;
  } catch {
    return fallback;
  }
};

const writeStoredJson = (key, value) => {
  if (typeof window === 'undefined') return;

  if (value === null || value === undefined) {
    window.localStorage.removeItem(key);
    return;
  }

  window.localStorage.setItem(key, JSON.stringify(value));
};

const createQueuedAction = (type, payload) => ({
  id: `${type}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
  type,
  payload,
  createdAt: new Date().toISOString(),
});

const getCompanyStorageKey = (prefix, userId, companyId) => {
  if (!userId || !companyId) return '';
  return `${prefix}:${userId}:${companyId}`;
};

export default function App() {
  const [currentView, setCurrentView] = useState('clock');
  const [session, setSession] = useState(null);
  const [profile, setProfile] = useState(null);
  const [memberships, setMemberships] = useState([]);
  const [activeCompanyId, setActiveCompanyId] = useState('');
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authMode, setAuthMode] = useState('signin');
  const [authError, setAuthError] = useState('');
  const [authInfo, setAuthInfo] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [jobSites, setJobSites] = useState([]);
  const [jobTypes, setJobTypes] = useState(defaultWorkTypes);
  const [selectedSite, setSelectedSite] = useState('');
  const [workType, setWorkType] = useState(defaultWorkTypes[0].id);
  const [timeEntries, setTimeEntries] = useState([]);
  const [activeEntry, setActiveEntry] = useState(null);
  const [activeSegment, setActiveSegment] = useState(null);
  const [elapsedTime, setElapsedTime] = useState('00:00:00');
  const [taskElapsedTime, setTaskElapsedTime] = useState('00:00:00');
  const [statusMessage, setStatusMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);
  const [isOnline, setIsOnline] = useState(() =>
    typeof navigator === 'undefined' ? true : navigator.onLine
  );
  const [offlineQueue, setOfflineQueue] = useState([]);
  const [isSyncingQueue, setIsSyncingQueue] = useState(false);
  const [siteForm, setSiteForm] = useState(emptySiteForm);
  const [editingSiteId, setEditingSiteId] = useState('');
  const [isSiteFormOpen, setIsSiteFormOpen] = useState(false);
  const [isSwitchingTask, setIsSwitchingTask] = useState(false);
  const [pendingTaskId, setPendingTaskId] = useState('');
  const [switchFeedback, setSwitchFeedback] = useState('');
  const [isSwitchBusy, setIsSwitchBusy] = useState(false);
  const [billingStatus, setBillingStatus] = useState(null);
  const [isBillingLoading, setIsBillingLoading] = useState(false);
  const [isCheckoutLoading, setIsCheckoutLoading] = useState(false);
  const [checkoutSeats, setCheckoutSeats] = useState(() => initialSeats(window.location.search));

  const isClockedIn = Boolean(activeEntry);
  const isOnBreak = Boolean(activeEntry?.break_started_at);
  const hasQueuedActions = offlineQueue.length > 0;
  const hasActiveBilling = billingStatus?.status === 'active' || billingStatus?.status === 'trialing';
  const currentUserId = session?.user?.id ?? '';
  const queueStorageKey = useMemo(
    () => getCompanyStorageKey(QUEUE_STORAGE_PREFIX, currentUserId, activeCompanyId),
    [currentUserId, activeCompanyId]
  );
  const offlineEntryStorageKey = useMemo(
    () => getCompanyStorageKey(OFFLINE_ENTRY_STORAGE_PREFIX, currentUserId, activeCompanyId),
    [currentUserId, activeCompanyId]
  );
  const offlineSegmentStorageKey = useMemo(
    () => getCompanyStorageKey(OFFLINE_SEGMENT_STORAGE_PREFIX, currentUserId, activeCompanyId),
    [currentUserId, activeCompanyId]
  );

  const activeMembership = useMemo(
    () => memberships.find((membership) => membership.company_id === activeCompanyId),
    [memberships, activeCompanyId]
  );

  const activeCompanyName = activeMembership?.companies?.name ?? 'Company';
  const activeRole = activeMembership?.role ?? 'worker';
  const isAdmin = activeRole === 'admin' || activeRole === 'owner';

  const activeSiteName = useMemo(() => {
    if (!activeEntry?.job_site_id || jobSites.length === 0) return 'Unknown site';
    return jobSites.find((site) => site.id === activeEntry.job_site_id)?.name ?? 'Unknown site';
  }, [activeEntry, jobSites]);

  const activeTask = useMemo(() => {
    const activeWorkTypeId = activeSegment?.work_type_id ?? activeEntry?.work_type_id ?? workType;
    return jobTypes.find((type) => type.id === activeWorkTypeId) ?? jobTypes[0] ?? defaultWorkTypes[0];
  }, [activeEntry, activeSegment, jobTypes, workType]);

  const showStatus = (message) => {
    setStatusMessage(message);
    setErrorMessage('');
  };

  const showError = (message) => {
    setErrorMessage(message);
    setStatusMessage('');
  };

  const replaceOfflineQueue = (nextQueue) => {
    setOfflineQueue(nextQueue);
    if (queueStorageKey) {
      writeStoredJson(queueStorageKey, nextQueue);
    }
  };

  const enqueueOfflineAction = (action) => {
    const nextQueue = [...offlineQueue, action];
    replaceOfflineQueue(nextQueue);
    return nextQueue;
  };

  useEffect(() => {
    let mounted = true;

    if (!isSupabaseConfigured) {
      setIsLoading(false);
      return undefined;
    }

    const initSession = async () => {
      const { data } = await supabase.auth.getSession();
      if (!mounted) return;
      setSession(data.session ?? null);
      setIsLoading(false);
    };

    initSession();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      if (!nextSession) {
        setProfile(null);
        setMemberships([]);
        setActiveCompanyId('');
        setJobSites([]);
        setJobTypes(defaultWorkTypes);
        setTimeEntries([]);
        setActiveEntry(null);
        setActiveSegment(null);
        setOfflineQueue([]);
      }
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  useEffect(() => {
    if (!queueStorageKey || !offlineEntryStorageKey || !offlineSegmentStorageKey) {
      setOfflineQueue([]);
      return;
    }

    setOfflineQueue(readStoredJson(queueStorageKey, []));
    const storedActiveEntry = readStoredJson(offlineEntryStorageKey, null);
    const storedActiveSegment = readStoredJson(offlineSegmentStorageKey, null);
    setActiveEntry((currentEntry) => {
      if (currentEntry && !currentEntry.isOffline) return currentEntry;
      return storedActiveEntry;
    });
    setActiveSegment((currentSegment) => {
      if (currentSegment && !currentSegment.isOffline) return currentSegment;
      return storedActiveSegment;
    });
  }, [queueStorageKey, offlineEntryStorageKey, offlineSegmentStorageKey]);

  useEffect(() => {
    if (!offlineEntryStorageKey) return;

    if (
      activeEntry?.isOffline &&
      activeEntry.user_id === currentUserId &&
      activeEntry.company_id === activeCompanyId
    ) {
      writeStoredJson(offlineEntryStorageKey, activeEntry);
      return;
    }

    writeStoredJson(offlineEntryStorageKey, null);
  }, [activeEntry, offlineEntryStorageKey, currentUserId, activeCompanyId]);

  useEffect(() => {
    if (!offlineSegmentStorageKey) return;

    if (
      activeSegment?.isOffline &&
      activeSegment.user_id === currentUserId &&
      activeSegment.company_id === activeCompanyId
    ) {
      writeStoredJson(offlineSegmentStorageKey, activeSegment);
      return;
    }

    writeStoredJson(offlineSegmentStorageKey, null);
  }, [activeSegment, offlineSegmentStorageKey, currentUserId, activeCompanyId]);

  useEffect(() => {
    if (activeEntry && activeCompanyId && activeEntry.company_id !== activeCompanyId) {
      setActiveEntry(null);
    }
  }, [activeEntry, activeCompanyId]);

  const loadMemberships = async () => {
    if (!session?.user) return [];

    const { data, error } = await supabase
      .from('memberships_2')
      .select('company_id, role, companies:companies_2 (id, name)')
      .eq('user_id', session.user.id)
      .order('created_at', { ascending: true });

    if (error) {
      showError(error.message);
      return [];
    }

    const nextMemberships = data ?? [];
    setMemberships(nextMemberships);

    const membershipIds = new Set(nextMemberships.map((membership) => membership.company_id));
    if (!activeCompanyId || !membershipIds.has(activeCompanyId)) {
      setActiveCompanyId(nextMemberships[0]?.company_id ?? '');
    }

    return data ?? [];
  };

  useEffect(() => {
    if (!session?.user) return;

    const loadBaseData = async () => {
      setIsLoading(true);
      setStatusMessage('');
      setErrorMessage('');

      const { data: profileData, error: profileError } = await supabase
        .from('profiles_2')
        .select('*')
        .eq('user_id', session.user.id)
        .maybeSingle();

      if (profileError) {
        showError(profileError.message);
      }

      setProfile(profileData ?? null);
      await loadMemberships();
      setIsLoading(false);
    };

    loadBaseData();
  }, [session?.user?.id]);

  const loadTimeEntries = async () => {
    if (!session?.user || !activeCompanyId) return;
    const { data, error } = await supabase
      .from('time_entries_2')
      .select(
        `
          id,
          clock_in,
          clock_out,
          break_minutes,
          job_site_id,
          work_type_id,
          job_sites:job_sites_2(name),
          work_types:work_types_2(code,label,color),
          segments:time_entry_segments_2(
            id,
            started_at,
            ended_at,
            work_type_id,
            work_types:work_types_2(code,label,color)
          )
        `
      )
      .eq('user_id', session.user.id)
      .eq('company_id', activeCompanyId)
      .order('clock_in', { ascending: false })
      .limit(10);

    if (error) {
      showError(error.message);
      return;
    }

    setTimeEntries(data ?? []);
  };

  const loadBillingStatus = async () => {
    if (!activeCompanyId) return null;

    setIsBillingLoading(true);
    const { data, error } = await supabase
      .from('company_billing_2')
      .select('*')
      .eq('company_id', activeCompanyId)
      .maybeSingle();

    setIsBillingLoading(false);

    if (error) {
      showError(error.message);
      return null;
    }

    setBillingStatus(data);
    return data;
  };

  useEffect(() => {
    if (!session?.user || !activeCompanyId) {
      setJobSites([]);
      setJobTypes(defaultWorkTypes);
      setSelectedSite('');
      setWorkType(defaultWorkTypes[0].id);
      setTimeEntries([]);
      setActiveEntry(null);
      setActiveSegment(null);
      return;
    }

    const loadCompanyData = async () => {
      setIsLoading(true);
      setStatusMessage('');
      setErrorMessage('');
      setSelectedSite('');

      const [jobSitesResponse, jobTypesResponse, activeEntryResponse] = await Promise.all([
        supabase.from('job_sites_2').select('*').eq('company_id', activeCompanyId).order('name'),
        supabase.from('work_types_2').select('*').eq('company_id', activeCompanyId).order('label'),
        supabase
          .from('time_entries_2')
          .select('*')
          .eq('user_id', session.user.id)
          .eq('company_id', activeCompanyId)
          .is('clock_out', null)
          .order('clock_in', { ascending: false })
          .limit(1)
          .maybeSingle(),
      ]);

      if (jobSitesResponse.error) {
        showError(jobSitesResponse.error.message);
      }

      const sites = jobSitesResponse.data ?? [];
      setJobSites(sites);

      if (jobTypesResponse.error) {
        showError(jobTypesResponse.error.message);
        setJobTypes(defaultWorkTypes);
        setWorkType(defaultWorkTypes[0].id);
      } else if (jobTypesResponse.data?.length) {
        const mapped = jobTypesResponse.data.map((type) => {
          const icon = workTypeIconMap[type.code] ?? MoreHorizontal;
          return {
            id: type.id,
            code: type.code,
            label: type.label,
            icon,
            color: type.color ?? workTypeColorFallback[type.code] ?? 'slate',
          };
        });
        setJobTypes(mapped);
        setWorkType((prev) => mapped.find((type) => type.id === prev)?.id ?? mapped[0].id);
      } else {
        setJobTypes(defaultWorkTypes);
        setWorkType(defaultWorkTypes[0].id);
      }

      setActiveEntry((currentEntry) => {
        if (currentEntry?.isOffline && offlineQueue.length > 0) return currentEntry;
        return activeEntryResponse.data ?? null;
      });
      if (activeEntryResponse.error) {
        showError(activeEntryResponse.error.message);
      }
      if (activeEntryResponse.data?.id) {
        const { data: segmentData, error: segmentError } = await supabase
          .from('time_entry_segments_2')
          .select('*')
          .eq('time_entry_id', activeEntryResponse.data.id)
          .is('ended_at', null)
          .maybeSingle();

        if (segmentError) {
          showError(segmentError.message);
        }

        setActiveSegment(segmentData ?? null);
      } else {
        setActiveSegment(null);
      }
      await loadTimeEntries();
      await loadBillingStatus();
      setIsLoading(false);
    };

    loadCompanyData();
  }, [session?.user?.id, activeCompanyId]);

  useEffect(() => {
    if (!activeEntry) {
      setElapsedTime('00:00:00');
      return;
    }

    const updateElapsed = () => {
      const now = new Date();
      const clockIn = new Date(activeEntry.clock_in);
      let breakMinutes = activeEntry.break_minutes ?? 0;
      if (activeEntry.break_started_at) {
        breakMinutes += (now - new Date(activeEntry.break_started_at)) / 60000;
      }
      const elapsedMs = now - clockIn - breakMinutes * 60000;
      setElapsedTime(formatDuration(elapsedMs));
    };

    updateElapsed();

    if (!activeEntry.break_started_at) {
      const interval = setInterval(updateElapsed, 1000);
      return () => clearInterval(interval);
    }
    return undefined;
  }, [activeEntry]);

  useEffect(() => {
    if (!activeSegment) {
      setTaskElapsedTime('00:00:00');
      return;
    }

    const updateTaskElapsed = () => {
      setTaskElapsedTime(formatDuration(new Date() - new Date(activeSegment.started_at)));
    };

    updateTaskElapsed();
    const interval = setInterval(updateTaskElapsed, 1000);
    return () => clearInterval(interval);
  }, [activeSegment]);

  const getLocationSnapshot = async () => {
    if (!navigator.geolocation) return null;

    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
          });
        },
        () => resolve(null),
        { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
      );
    });
  };

  const insertGpsMarker = async ({ timeEntryId, event, location, userId = session?.user?.id }) => {
    if (!location || !userId || !activeCompanyId) return;

    const { error } = await supabase.from('gps_markers_2').insert({
      company_id: activeCompanyId,
      user_id: userId,
      time_entry_id: timeEntryId,
      latitude: location.latitude,
      longitude: location.longitude,
      accuracy: location.accuracy,
      event,
    });

    if (error) {
      throw error;
    }
  };

  const captureLocation = async (timeEntryId, event) => {
    if (!session?.user || !activeCompanyId) return;

    const location = await getLocationSnapshot();
    if (!location) return;
    await insertGpsMarker({ timeEntryId, event, location });
  };

  const createTimeSegment = async ({
    timeEntryId,
    jobSiteId,
    workTypeId,
    startedAt,
    userId = session?.user?.id,
  }) => {
    const { data, error } = await supabase
      .from('time_entry_segments_2')
      .insert({
        company_id: activeCompanyId,
        user_id: userId,
        time_entry_id: timeEntryId,
        job_site_id: jobSiteId,
        work_type_id: workTypeId,
        started_at: startedAt,
      })
      .select()
      .single();

    if (error) throw error;
    return data;
  };

  const closeOpenTimeSegment = async (timeEntryId, endedAt) => {
    const { error } = await supabase
      .from('time_entry_segments_2')
      .update({ ended_at: endedAt })
      .eq('time_entry_id', timeEntryId)
      .is('ended_at', null);

    if (error) throw error;
  };

  const syncOfflineQueue = async () => {
    if (
      !isOnline ||
      !session?.user ||
      !activeCompanyId ||
      !queueStorageKey ||
      offlineQueue.length === 0 ||
      isSyncingQueue
    ) {
      return;
    }

    setIsSyncingQueue(true);
    const remaining = offlineQueue.filter(
      (action) =>
        action.payload.companyId === activeCompanyId &&
        (!action.payload.userId || action.payload.userId === session.user.id)
    );
    const entryIdMap = {};

    try {
      while (remaining.length > 0) {
        const action = remaining[0];
        const payload = action.payload;
        const serverEntryId = payload.entryId || entryIdMap[payload.clientEntryId];

        if (action.type === 'clock_in') {
          const { data, error } = await supabase
            .from('time_entries_2')
            .insert({
              company_id: payload.companyId,
              user_id: payload.userId,
              job_site_id: payload.jobSiteId,
              work_type_id: payload.workTypeId,
              clock_in: payload.clockIn,
            })
            .select()
            .single();

          if (error) throw error;

          entryIdMap[payload.clientEntryId] = data.id;
          for (let index = 1; index < remaining.length; index += 1) {
            if (remaining[index].payload.clientEntryId === payload.clientEntryId) {
              remaining[index] = {
                ...remaining[index],
                payload: {
                  ...remaining[index].payload,
                  entryId: data.id,
                },
              };
            }
          }

          await createTimeSegment({
            timeEntryId: data.id,
            jobSiteId: payload.jobSiteId,
            workTypeId: payload.workTypeId,
            startedAt: payload.clockIn,
            userId: payload.userId,
          });

          if (payload.location) {
            try {
              await insertGpsMarker({
                timeEntryId: data.id,
                event: 'clock_in',
                location: payload.location,
                userId: payload.userId,
              });
            } catch {
              // Keep time sync moving even if a GPS point is rejected.
            }
          }
        }

        if (action.type === 'break_start') {
          if (!serverEntryId) throw new Error('Queued break start is missing a time entry.');

          const { error } = await supabase
            .from('time_entries_2')
            .update({ break_started_at: payload.breakStartedAt })
            .eq('id', serverEntryId);

          if (error) throw error;
        }

        if (action.type === 'break_end') {
          if (!serverEntryId) throw new Error('Queued break end is missing a time entry.');

          const { error } = await supabase
            .from('time_entries_2')
            .update({
              break_started_at: null,
              break_minutes: payload.breakMinutes,
            })
            .eq('id', serverEntryId);

          if (error) throw error;
        }

        if (action.type === 'switch_task') {
          if (!serverEntryId) throw new Error('Queued task switch is missing a time entry.');

          await closeOpenTimeSegment(serverEntryId, payload.switchedAt);
          await createTimeSegment({
            timeEntryId: serverEntryId,
            jobSiteId: payload.jobSiteId,
            workTypeId: payload.workTypeId,
            startedAt: payload.switchedAt,
            userId: payload.userId,
          });

          const { error } = await supabase
            .from('time_entries_2')
            .update({ work_type_id: payload.workTypeId })
            .eq('id', serverEntryId);

          if (error) throw error;
        }

        if (action.type === 'clock_out') {
          if (!serverEntryId) throw new Error('Queued clock out is missing a time entry.');

          await closeOpenTimeSegment(serverEntryId, payload.clockOut);

          const { error } = await supabase
            .from('time_entries_2')
            .update({
              clock_out: payload.clockOut,
              break_minutes: payload.breakMinutes,
              break_started_at: null,
            })
            .eq('id', serverEntryId);

          if (error) throw error;

          if (payload.location) {
            try {
              await insertGpsMarker({
                timeEntryId: serverEntryId,
                event: 'clock_out',
                location: payload.location,
                userId: payload.userId,
              });
            } catch {
              // Keep time sync moving even if a GPS point is rejected.
            }
          }
        }

        remaining.shift();
        replaceOfflineQueue(remaining);
      }

      setActiveEntry(null);
      setActiveSegment(null);
      if (offlineEntryStorageKey) {
        writeStoredJson(offlineEntryStorageKey, null);
      }
      if (offlineSegmentStorageKey) {
        writeStoredJson(offlineSegmentStorageKey, null);
      }
      await loadTimeEntries();
      showStatus('Offline actions synced.');
    } catch (error) {
      replaceOfflineQueue(remaining);
      showError(`Sync paused: ${error.message}`);
    } finally {
      setIsSyncingQueue(false);
    }
  };

  useEffect(() => {
    if (isOnline && offlineQueue.length > 0) {
      syncOfflineQueue();
    }
  }, [isOnline, offlineQueue.length, session?.user?.id, activeCompanyId]);

  useEffect(() => {
    if (!session || !activeCompanyId) return;

    const params = new URLSearchParams(window.location.search);
    let cancelled = false;
    let timer;
    if (params.get('checkout') === 'success') {
      showStatus('Checking payment confirmation...');
      let attempts = 0;
      const check = async () => {
        const { data, error } = await supabase.from('company_billing_2')
          .select('*').eq('company_id', activeCompanyId).maybeSingle();
        if (cancelled) return;
        if (!error) {
          setBillingStatus(data);
          showStatus(billingMessage(data));
          if (['active', 'trialing'].includes(data?.status)) {
            window.history.replaceState({}, document.title, window.location.pathname);
            return;
          }
        }
        if (++attempts < 12) timer = setTimeout(() => check().catch(() => { if (!cancelled) showStatus('Could not check payment confirmation. Use Refresh billing status.'); }), 3000);
        else showStatus('Payment confirmation is taking longer. Use Refresh billing status; do not pay again.');
      };
      check().catch(() => { if (!cancelled) showStatus('Could not check payment confirmation. Use Refresh billing status.'); });
    }
    if (params.get('checkout') === 'cancelled') {
      showError('Checkout was cancelled.');
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    return () => { cancelled = true; clearTimeout(timer); };
  }, [session?.user?.id, activeCompanyId]);

  const handleAuthSubmit = async (event) => {
    event.preventDefault();
    setAuthError('');
    setAuthInfo('');

    if (!authEmail || !authPassword) {
      setAuthError('Enter an email and password to continue.');
      return;
    }

    if (authMode === 'signup') {
      const redirectTo =
        typeof window !== 'undefined' ? `${window.location.origin}/emailconfirm.html` : undefined;
      const { data, error } = await supabase.auth.signUp({
        email: authEmail,
        password: authPassword,
        options: redirectTo ? { emailRedirectTo: redirectTo } : undefined,
      });
      if (error) {
        setAuthError(error.message);
      } else if (data?.user && data.user.identities?.length === 0) {
        setAuthError('Account already exists. Please sign in instead.');
      } else {
        setAuthInfo('Check your email to confirm your account.');
      }
      return;
    }

    const { error } = await supabase.auth.signInWithPassword({
      email: authEmail,
      password: authPassword,
    });

    if (error) {
      setAuthError(error.message);
    }
  };

  const handleResendConfirmation = async () => {
    setAuthError('');
    setAuthInfo('');

    if (!authEmail) {
      setAuthError('Enter your email first.');
      return;
    }

    const redirectTo =
      typeof window !== 'undefined' ? `${window.location.origin}/emailconfirm.html` : undefined;

    const { error } = await supabase.auth.resend({
      type: 'signup',
      email: authEmail,
      options: redirectTo ? { emailRedirectTo: redirectTo } : undefined,
    });

    if (error) {
      setAuthError(error.message);
    } else {
      setAuthInfo('Confirmation email sent. Check your inbox.');
    }
  };

  const handleSignOut = async () => {
    if (offlineQueue.length > 0) {
      showError('Sync queued time actions before signing out.');
      return;
    }

    await supabase.auth.signOut();
  };

  const handleCreateCompany = async (event) => {
    event.preventDefault();

    if (!session?.user) return;

    const trimmedName = companyName.trim();
    if (!trimmedName) {
      showError('Enter a company name to continue.');
      return;
    }

    setIsBusy(true);
    setStatusMessage('');
    setErrorMessage('');

    const { error } = await supabase.from('companies_2').insert({
      name: trimmedName,
      created_by: session.user.id,
    });
    setIsBusy(false);

    if (error) {
      showError(error.message);
      return;
    }

    setCompanyName('');
    const nextMemberships = await loadMemberships();
    const nextCompanyId = nextMemberships[0]?.company_id ?? '';
    setActiveCompanyId(nextCompanyId);
    showStatus('Company created. Add job sites next.');
  };

  const handleStartCheckout = async () => {
    if (!session || !activeCompanyId || isCheckoutLoading) return;

    setIsCheckoutLoading(true);
    setErrorMessage('');

    try {
      const attempt = checkoutAttempt(window.sessionStorage, session.user.id, activeCompanyId, Number(checkoutSeats), () => crypto.randomUUID());
      const response = await fetch('/api/create-checkout-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ companyId: activeCompanyId, ...attempt }),
        signal: AbortSignal.timeout(30000),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.error ?? 'Unable to start checkout.');
      }

      if (new URL(data.url).origin !== 'https://checkout.stripe.com') throw new Error('Unable to open secure checkout.');
      window.location.href = data.url;
    } catch (error) {
      showError(error.message);
      setIsCheckoutLoading(false);
    }
  };

  const resetSiteForm = () => {
    setSiteForm(emptySiteForm);
    setEditingSiteId('');
    setIsSiteFormOpen(false);
  };

  const openNewSiteForm = () => {
    setSiteForm(emptySiteForm);
    setEditingSiteId('');
    setIsSiteFormOpen(true);
    setErrorMessage('');
  };

  const openEditSiteForm = (site) => {
    setSiteForm({
      name: site.name ?? '',
      client: site.client ?? '',
      address: site.address ?? '',
      status: site.status ?? 'active',
    });
    setEditingSiteId(site.id);
    setIsSiteFormOpen(true);
    setErrorMessage('');
  };

  const handleSiteFormSubmit = async (event) => {
    event.preventDefault();

    if (!isAdmin || !activeCompanyId) return;

    const payload = {
      company_id: activeCompanyId,
      name: siteForm.name.trim(),
      client: siteForm.client.trim() || null,
      address: siteForm.address.trim() || null,
      status: siteForm.status,
    };

    if (!payload.name) {
      showError('Enter a job site name.');
      return;
    }

    if (!isOnline) {
      showError('Job site changes need a connection. Reconnect and try again.');
      return;
    }

    setIsBusy(true);
    setErrorMessage('');

    const request = editingSiteId
      ? supabase.from('job_sites_2').update(payload).eq('id', editingSiteId).select().single()
      : supabase.from('job_sites_2').insert(payload).select().single();

    const { data, error } = await request;
    setIsBusy(false);

    if (error) {
      showError(error.message);
      return;
    }

    if (editingSiteId) {
      setJobSites((sites) => sites.map((site) => (site.id === editingSiteId ? data : site)));
      showStatus('Job site updated.');
    } else {
      setJobSites((sites) => [...sites, data].sort((a, b) => a.name.localeCompare(b.name)));
      showStatus('Job site added.');
    }

    resetSiteForm();
  };

  const handleDeleteSite = async (site) => {
    if (!isAdmin || !isOnline) {
      showError('Deleting a job site needs a connection.');
      return;
    }

    const hasEntries = timeEntries.some((entry) => entry.job_site_id === site.id);
    if (hasEntries) {
      showError('This site has timesheet entries. Mark it completed instead of deleting it.');
      return;
    }

    if (!window.confirm(`Delete ${site.name}?`)) {
      return;
    }

    setIsBusy(true);
    setErrorMessage('');

    const { error } = await supabase.from('job_sites_2').delete().eq('id', site.id);
    setIsBusy(false);

    if (error) {
      showError(error.message);
      return;
    }

    setJobSites((sites) => sites.filter((item) => item.id !== site.id));
    showStatus('Job site deleted.');
  };

  const handleClockIn = async () => {
    if (!selectedSite) {
      showError('Select a job site before clocking in.');
      return;
    }

    if (!session?.user || !activeCompanyId) return;

    setStatusMessage('');
    setErrorMessage('');
    const clockIn = new Date().toISOString();
    const clientEntryId = `pending-${Date.now()}`;
    const optimisticEntry = {
      id: clientEntryId,
      clientEntryId,
      company_id: activeCompanyId,
      user_id: session.user.id,
      job_site_id: selectedSite,
      work_type_id: workType,
      clock_in: clockIn,
      clock_out: null,
      break_minutes: 0,
      break_started_at: null,
      isPending: true,
    };
    const optimisticSegment = {
      id: `segment-${clientEntryId}`,
      company_id: activeCompanyId,
      user_id: session.user.id,
      time_entry_id: clientEntryId,
      job_site_id: selectedSite,
      work_type_id: workType,
      started_at: clockIn,
      ended_at: null,
      isPending: true,
    };

    setActiveEntry(optimisticEntry);
    setActiveSegment(optimisticSegment);
    setSelectedSite('');

    const location = await getLocationSnapshot();

    if (!isOnline) {
      const offlineEntry = {
        ...optimisticEntry,
        company_id: activeCompanyId,
        user_id: session.user.id,
        job_site_id: selectedSite,
        work_type_id: workType,
        clock_in: clockIn,
        clock_out: null,
        break_minutes: 0,
        break_started_at: null,
        isPending: false,
        isOffline: true,
      };
      const offlineSegment = {
        ...optimisticSegment,
        company_id: activeCompanyId,
        user_id: session.user.id,
        time_entry_id: clientEntryId,
        job_site_id: selectedSite,
        work_type_id: workType,
        started_at: clockIn,
        ended_at: null,
        isPending: false,
        isOffline: true,
      };

      enqueueOfflineAction(
        createQueuedAction('clock_in', {
          clientEntryId,
          companyId: activeCompanyId,
          userId: session.user.id,
          jobSiteId: selectedSite,
          workTypeId: workType,
          clockIn,
          location,
        })
      );

      setActiveEntry(offlineEntry);
      setActiveSegment(offlineSegment);
      showStatus('Clock-in saved offline. It will sync when connection returns.');
      return;
    }

    const { data, error } = await supabase
      .from('time_entries_2')
      .insert({
        company_id: activeCompanyId,
        user_id: session.user.id,
        job_site_id: selectedSite,
        work_type_id: workType,
        clock_in: clockIn,
      })
      .select()
      .single();

    if (error) {
      setActiveEntry(null);
      setActiveSegment(null);
      setSelectedSite(selectedSite);
      showError(error.message);
      return;
    }

    let segmentData = null;
    try {
      segmentData = await createTimeSegment({
        timeEntryId: data.id,
        jobSiteId: selectedSite,
        workTypeId: workType,
        startedAt: clockIn,
      });
    } catch (error) {
      showError(`Clock-in saved, but the task segment did not save: ${error.message}`);
    }

    setActiveEntry(data);
    setActiveSegment(segmentData);
    if (location) {
      try {
        await insertGpsMarker({ timeEntryId: data.id, event: 'clock_in', location });
      } catch (error) {
        showError(`Clock-in saved, but GPS did not save: ${error.message}`);
      }
    }
    await loadTimeEntries();
  };

  const handleSwitchTask = async (nextWorkTypeId) => {
    if (!activeEntry || !session?.user || !activeCompanyId) return false;

    const currentWorkTypeId = activeSegment?.work_type_id ?? activeEntry.work_type_id;
    if (nextWorkTypeId === currentWorkTypeId) return true;

    const switchedAt = new Date().toISOString();

    if (!isOnline || activeEntry.isOffline) {
      enqueueOfflineAction(
        createQueuedAction('switch_task', {
          clientEntryId: activeEntry.clientEntryId,
          entryId: activeEntry.isOffline ? null : activeEntry.id,
          companyId: activeCompanyId,
          userId: session.user.id,
          jobSiteId: activeEntry.job_site_id,
          workTypeId: nextWorkTypeId,
          switchedAt,
        })
      );

      const nextSegment = {
        id: `segment-${Date.now()}`,
        company_id: activeCompanyId,
        user_id: session.user.id,
        time_entry_id: activeEntry.id,
        job_site_id: activeEntry.job_site_id,
        work_type_id: nextWorkTypeId,
        started_at: switchedAt,
        ended_at: null,
        isOffline: true,
      };

      setActiveSegment(nextSegment);
      setActiveEntry((entry) => ({ ...entry, work_type_id: nextWorkTypeId }));
      showStatus('Task switch saved offline.');
      return true;
    }

    setIsBusy(true);
    setErrorMessage('');

    try {
      await closeOpenTimeSegment(activeEntry.id, switchedAt);
      const nextSegment = await createTimeSegment({
        timeEntryId: activeEntry.id,
        jobSiteId: activeEntry.job_site_id,
        workTypeId: nextWorkTypeId,
        startedAt: switchedAt,
      });

      const { data, error } = await supabase
        .from('time_entries_2')
        .update({ work_type_id: nextWorkTypeId })
        .eq('id', activeEntry.id)
        .select()
        .single();

      if (error) throw error;

      setActiveSegment(nextSegment);
      setActiveEntry(data);
      showStatus('Task switched.');
      return true;
    } catch (error) {
      showError(error.message);
      return false;
    } finally {
      setIsBusy(false);
    }
  };

  const openTaskSwitcher = () => {
    setPendingTaskId('');
    setSwitchFeedback('');
    setIsSwitchingTask(true);
  };

  const cancelTaskSwitcher = () => {
    setPendingTaskId('');
    setSwitchFeedback('');
    setIsSwitchingTask(false);
  };

  const handleConfirmTaskSwitch = async () => {
    if (!pendingTaskId) {
      setSwitchFeedback('Choose a task first.');
      return;
    }

    setIsSwitchBusy(true);
    setSwitchFeedback('');
    const switched = await handleSwitchTask(pendingTaskId);
    setIsSwitchBusy(false);

    if (switched) {
      setSwitchFeedback('Success. Task switched.');
      setPendingTaskId('');
      setIsSwitchingTask(false);
      return;
    }

    setSwitchFeedback('Whoops! Something went wrong. Please try again.');
  };

  const handleClockOut = async () => {
    if (!activeEntry) return;

    let breakMinutes = activeEntry.break_minutes ?? 0;
    const clockOut = new Date().toISOString();
    if (activeEntry.break_started_at) {
      breakMinutes += (new Date(clockOut) - new Date(activeEntry.break_started_at)) / 60000;
    }

    const roundedBreakMinutes = Math.round(breakMinutes);
    const location = await getLocationSnapshot();

    if (!isOnline || activeEntry.isOffline) {
      enqueueOfflineAction(
        createQueuedAction('clock_out', {
          clientEntryId: activeEntry.clientEntryId,
          entryId: activeEntry.isOffline ? null : activeEntry.id,
          companyId: activeCompanyId,
          userId: session.user.id,
          clockOut,
          breakMinutes: roundedBreakMinutes,
          location,
        })
      );

      setActiveEntry(null);
      setActiveSegment(null);
      if (offlineEntryStorageKey) {
        writeStoredJson(offlineEntryStorageKey, null);
      }
      if (offlineSegmentStorageKey) {
        writeStoredJson(offlineSegmentStorageKey, null);
      }
      showStatus('Clock-out saved offline. It will sync when connection returns.');
      return;
    }

    let data = null;
    try {
      await closeOpenTimeSegment(activeEntry.id, clockOut);

      const response = await supabase
        .from('time_entries_2')
        .update({
          clock_out: clockOut,
          break_minutes: roundedBreakMinutes,
          break_started_at: null,
        })
        .eq('id', activeEntry.id)
        .select()
        .single();

      if (response.error) throw response.error;
      data = response.data;
    } catch (error) {
      showError(error.message);
      return;
    }

    if (location) {
      try {
        await insertGpsMarker({ timeEntryId: activeEntry.id, event: 'clock_out', location });
      } catch (error) {
        showError(`Shift saved, but GPS did not save: ${error.message}`);
      }
    }
    setActiveEntry(null);
    setActiveSegment(null);
    await loadTimeEntries();

    if (data) {
      showStatus('Shift saved to your timesheet.');
    }
  };

  const handleBreakToggle = async () => {
    if (!activeEntry) return;

    if (!activeEntry.break_started_at) {
      const breakStartedAt = new Date().toISOString();

      if (!isOnline || activeEntry.isOffline) {
        enqueueOfflineAction(
        createQueuedAction('break_start', {
          clientEntryId: activeEntry.clientEntryId,
          entryId: activeEntry.isOffline ? null : activeEntry.id,
          companyId: activeCompanyId,
          userId: session.user.id,
          breakStartedAt,
        })
        );

        setActiveEntry((entry) => ({ ...entry, break_started_at: breakStartedAt }));
        showStatus('Break start saved offline.');
        return;
      }

      const { data, error } = await supabase
        .from('time_entries_2')
        .update({ break_started_at: breakStartedAt })
        .eq('id', activeEntry.id)
        .select()
        .single();

      if (error) {
        showError(error.message);
        return;
      }

      setActiveEntry(data);
      return;
    }

    const breakMinutes =
      (new Date() - new Date(activeEntry.break_started_at)) / 60000 +
      (activeEntry.break_minutes ?? 0);
    const roundedBreakMinutes = Math.round(breakMinutes);

    if (!isOnline || activeEntry.isOffline) {
      enqueueOfflineAction(
        createQueuedAction('break_end', {
          clientEntryId: activeEntry.clientEntryId,
          entryId: activeEntry.isOffline ? null : activeEntry.id,
          companyId: activeCompanyId,
          userId: session.user.id,
          breakMinutes: roundedBreakMinutes,
        })
      );

      setActiveEntry((entry) => ({
        ...entry,
        break_started_at: null,
        break_minutes: roundedBreakMinutes,
      }));
      showStatus('Break end saved offline.');
      return;
    }

    const { data, error } = await supabase
      .from('time_entries_2')
      .update({
        break_started_at: null,
        break_minutes: roundedBreakMinutes,
      })
      .eq('id', activeEntry.id)
      .select()
      .single();

    if (error) {
      showError(error.message);
      return;
    }

    setActiveEntry(data);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center app-bg text-white">
        Loading...
      </div>
    );
  }

  if (!isSupabaseConfigured) {
    return (
      <div className="min-h-screen flex items-center justify-center app-bg px-6 text-white">
        <div className="max-w-md space-y-3 text-center">
          <h1 className="text-2xl font-bold">Supabase is not configured</h1>
          <p className="text-sm text-zinc-400">
            Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to your .env file, then restart the
            dev server.
          </p>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen app-bg px-6 py-10 text-white">
        <div className="max-w-md mx-auto space-y-8">
          <div className="text-center space-y-2">
            <img
              src="/time-tracker-logo.png"
              alt=""
              className="mx-auto h-28 w-28 rounded-2xl object-contain bg-black/40"
            />
            <h1 className="text-3xl font-bold">{APP_NAME}</h1>
            <p className="text-zinc-400">Sign in to track job site, travel, and task time.</p>
          </div>

          <form onSubmit={handleAuthSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm text-zinc-400 font-medium">Email</label>
              <input
                type="email"
                value={authEmail}
                onChange={(event) => setAuthEmail(event.target.value)}
                name="email"
                autoComplete="email"
                className="w-full h-12 bg-zinc-900/80 border border-zinc-800 rounded-2xl text-white text-base px-4"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-zinc-400 font-medium">Password</label>
              <input
                type="password"
                value={authPassword}
                onChange={(event) => setAuthPassword(event.target.value)}
                name="password"
                autoComplete={authMode === 'signup' ? 'new-password' : 'current-password'}
                className="w-full h-12 bg-zinc-900/80 border border-zinc-800 rounded-2xl text-white text-base px-4"
              />
            </div>

            {authError && <p className="text-sm text-red-400">{authError}</p>}
            {authInfo && <p className="text-sm text-emerald-400">{authInfo}</p>}
            {statusMessage && !authInfo && (
              <p className="text-sm text-emerald-400">{statusMessage}</p>
            )}

            <button
              type="submit"
              className="w-full h-12 rounded-2xl bg-gradient-to-r from-emerald-500 to-emerald-600 font-semibold"
            >
              {authMode === 'signup' ? 'Create account' : 'Sign in'}
            </button>
          </form>

          <div className="text-center text-sm text-zinc-400">
            {authMode === 'signup' ? 'Already have an account?' : "Don't have an account?"}{' '}
            <button
              type="button"
              onClick={() => setAuthMode(authMode === 'signup' ? 'signin' : 'signup')}
              className="text-orange-400 font-semibold"
            >
              {authMode === 'signup' ? 'Sign in' : 'Sign up'}
            </button>
          </div>

          {authMode === 'signin' && (
            <div className="text-center text-sm text-zinc-400">
              <button
                type="button"
                onClick={handleResendConfirmation}
                className="text-orange-400 font-semibold"
              >
                Resend confirmation email
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen app-bg">
      <div className="pb-24 px-4 py-8">
        <div className="max-w-md mx-auto">
          <div className="flex items-center justify-between text-xs text-zinc-500 mb-4">
            <span>{activeRole === 'admin' || activeRole === 'owner' ? 'Admin' : 'Crew'} Mode</span>
            <button onClick={handleSignOut} className="text-zinc-400 hover:text-white">
              Sign out
            </button>
          </div>

          {memberships.length > 1 && (
            <div className="mb-6">
              <label className="text-xs text-zinc-500 font-medium">Company</label>
              <select
                value={activeCompanyId}
                onChange={(event) => setActiveCompanyId(event.target.value)}
                className="w-full h-12 mt-2 bg-zinc-900/80 border border-zinc-800 rounded-2xl text-white text-base px-4"
              >
                {memberships.map((membership) => (
                  <option key={membership.company_id} value={membership.company_id}>
                    {membership.companies?.name ?? membership.company_id}
                  </option>
                ))}
              </select>
            </div>
          )}

          {memberships.length === 1 && (
            <div className="mb-6 text-sm text-zinc-400">Company: {activeCompanyName}</div>
          )}

          {memberships.length === 0 && (
            <div className="mb-8 bg-zinc-900/60 backdrop-blur rounded-2xl p-5 space-y-4">
              <div>
                <h1 className="text-xl font-bold text-white">Set up your company</h1>
                <p className="text-sm text-zinc-400 mt-1">
                  Create the first company workspace for your crew.
                </p>
              </div>
              <form onSubmit={handleCreateCompany} className="space-y-3">
                <div className="space-y-2">
                  <label className="text-sm text-zinc-400 font-medium">Company name</label>
                  <input
                    type="text"
                    value={companyName}
                    onChange={(event) => setCompanyName(event.target.value)}
                    className="w-full h-12 bg-zinc-950/70 border border-zinc-800 rounded-2xl text-white text-base px-4"
                    placeholder="Example Traffic Control"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isBusy}
                  className="w-full h-12 rounded-2xl bg-gradient-to-r from-orange-500 to-orange-600 text-white font-semibold disabled:opacity-60"
                >
                  {isBusy ? 'Creating...' : 'Create company'}
                </button>
              </form>
            </div>
          )}

          {(!isOnline || hasQueuedActions) && (
            <div className="mb-4 flex items-center justify-between gap-3 rounded-2xl border border-amber-500/40 bg-amber-500/10 p-3 text-sm text-amber-200">
              <div className="flex items-center gap-2">
                {isSyncingQueue ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <WifiOff className="h-4 w-4" />
                )}
                <span>
                  {!isOnline
                    ? `${offlineQueue.length} action${offlineQueue.length === 1 ? '' : 's'} queued offline`
                    : isSyncingQueue
                      ? 'Syncing queued actions'
                      : `${offlineQueue.length} queued action${offlineQueue.length === 1 ? '' : 's'} ready to sync`}
                </span>
              </div>
              {isOnline && hasQueuedActions && (
                <button
                  type="button"
                  onClick={syncOfflineQueue}
                  className="text-xs font-semibold text-white"
                >
                  Sync
                </button>
              )}
            </div>
          )}

          {errorMessage && <p className="text-sm text-red-400 mb-4">{errorMessage}</p>}
          {statusMessage && <p className="text-sm text-emerald-400 mb-4">{statusMessage}</p>}

          {memberships.length > 0 && isBillingLoading && (
            <div className="rounded-2xl bg-zinc-950/60 p-5 text-center text-zinc-300">
              Checking workspace access...
            </div>
          )}

          {memberships.length > 0 && !isBillingLoading && !hasActiveBilling && (
            <div className="rounded-2xl border border-orange-500/40 bg-zinc-950/70 p-5 text-white shadow-2xl backdrop-blur space-y-5">
              <div className="flex items-center gap-4">
                <img
                  src="/time-tracker-logo.png"
                  alt=""
                  className="h-16 w-16 rounded-xl object-contain bg-black/40"
                />
                <div>
                  <h1 className="text-2xl font-bold">{APP_NAME}</h1>
                  <p className="text-sm text-zinc-400">Workspace access required</p>
                </div>
              </div>
              <p className="text-sm text-zinc-300">
                One user is $9.99/month. Each additional user is $4/month, up to 30 users. No setup charge.
              </p>
              <p className="text-xs text-zinc-500">
                Also available from the WZOS page and Molecular Project Development LLC page.
              </p>
              {isAdmin ? (
                <div className="space-y-3">
                <label className="block text-sm text-zinc-300">Total users, including admins
                  <input type="number" min="1" max="30" step="1" value={checkoutSeats}
                    onChange={event => setCheckoutSeats(event.target.value)} disabled={isCheckoutLoading}
                    className="mt-2 block w-full rounded-xl bg-zinc-900 p-3 text-white" />
                </label>
                <button
                  type="button"
                  onClick={handleStartCheckout}
                  disabled={isCheckoutLoading}
                  className="w-full rounded-2xl bg-orange-500 px-4 py-3 font-semibold text-white disabled:opacity-60"
                >
                  {isCheckoutLoading ? 'Opening checkout...' : 'Activate Time Tracker⚡'}
                </button>
                <button type="button" disabled={isBillingLoading}
                  onClick={async () => showStatus(billingMessage(await loadBillingStatus()))}
                  className="w-full rounded-xl border border-zinc-600 p-3">Refresh billing status</button>
                </div>
              ) : (
                <p className="rounded-xl bg-zinc-900/80 p-3 text-sm text-zinc-300">
                  Ask a company owner or admin to activate this workspace.
                </p>
              )}
            </div>
          )}

          {memberships.length > 0 && hasActiveBilling && currentView === 'clock' && (
            <div className="space-y-8">
              <div className="text-center">
                <div className="flex items-center justify-center gap-3">
                  <img
                    src="/time-tracker-logo.png"
                    alt=""
                    className="h-12 w-12 rounded-xl object-contain bg-black/40"
                  />
                  <h1 className="text-2xl font-bold text-white">{APP_NAME}</h1>
                </div>
                <p className="text-zinc-400 mt-1">{formatDate(new Date())}</p>
              </div>

              {isClockedIn && (
                <div className="bg-zinc-900/60 backdrop-blur rounded-3xl p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-zinc-400">
                      <Clock className="w-4 h-4" />
                      <span className="text-sm">Time Today</span>
                    </div>
                    {isOnBreak && (
                      <div className="flex items-center gap-2 px-3 py-1 bg-amber-500/20 rounded-full">
                        <Coffee className="w-4 h-4 text-amber-400" />
                        <span className="text-sm text-amber-400 font-medium">On Break</span>
                      </div>
                    )}
                  </div>

                  <div className="text-center">
                    <div className="text-5xl font-bold text-white font-mono tracking-wider">
                      {elapsedTime}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-zinc-400 justify-center pt-2 border-t border-zinc-800/50">
                    <MapPin className="w-4 h-4 text-orange-400" />
                    <span className="text-sm">{activeSiteName}</span>
                  </div>

                  <div className="pt-2 border-t border-zinc-800/50 space-y-3">
                    <div className="flex items-center justify-center gap-2 text-zinc-300">
                      {(() => {
                        const ActiveTaskIcon = activeTask.icon;
                        return <ActiveTaskIcon className="w-4 h-4 text-orange-400" />;
                      })()}
                      <span className="text-sm">Current task: {activeTask.label}</span>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-white font-mono">
                        {taskElapsedTime}
                      </div>
                      <p className="text-xs text-zinc-500">Task time</p>
                    </div>

                    {!isSwitchingTask ? (
                      <button
                        type="button"
                        onClick={openTaskSwitcher}
                        disabled={activeEntry?.isPending}
                        className="w-full rounded-2xl bg-orange-500 px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
                      >
                        Switch task
                      </button>
                    ) : (
                      <div className="space-y-3 rounded-2xl bg-zinc-950/50 p-3">
                        <div className="grid grid-cols-2 gap-2">
                          {jobTypes.map((type) => {
                            const Icon = type.icon;
                            const isCurrent =
                              (activeSegment?.work_type_id ?? activeEntry?.work_type_id) === type.id;
                            const isPending = pendingTaskId === type.id;
                            return (
                              <button
                                key={type.id}
                                type="button"
                                onClick={() => setPendingTaskId(type.id)}
                                disabled={isCurrent || isSwitchBusy}
                                className={`flex items-center justify-center gap-2 rounded-xl border px-3 py-3 text-sm transition-all disabled:opacity-60 ${
                                  isPending
                                    ? `bg-${type.color}-500/20 border-${type.color}-500 text-${type.color}-400`
                                    : isCurrent
                                      ? 'bg-zinc-900/80 border-zinc-800 text-zinc-500'
                                      : 'bg-zinc-950/40 border-zinc-800 text-zinc-300 hover:border-zinc-500'
                                }`}
                              >
                                <Icon className="w-4 h-4" />
                                <span>{isCurrent ? `${type.label} active` : type.label}</span>
                              </button>
                            );
                          })}
                        </div>
                        {switchFeedback && (
                          <p className="text-center text-sm text-zinc-300">{switchFeedback}</p>
                        )}
                        <div className="grid grid-cols-2 gap-2">
                          <button
                            type="button"
                            onClick={cancelTaskSwitcher}
                            disabled={isSwitchBusy}
                            className="rounded-xl bg-zinc-800 px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
                          >
                            Cancel
                          </button>
                          <button
                            type="button"
                            onClick={handleConfirmTaskSwitch}
                            disabled={!pendingTaskId || isSwitchBusy}
                            className="rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
                          >
                            {isSwitchBusy ? 'Switching...' : 'Confirm'}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {!isClockedIn && (
                <>
                  <div className="space-y-3">
                    <label className="text-sm text-zinc-400 font-medium px-1">Job Site</label>
                    <select
                      value={selectedSite}
                      onChange={(e) => setSelectedSite(e.target.value)}
                      className="w-full h-14 bg-zinc-900/80 border border-zinc-800 rounded-2xl text-white text-lg px-4"
                    >
                      <option value="">Select job site</option>
                      {jobSites
                        .filter((site) => site.status === 'active')
                        .map((site) => (
                          <option key={site.id} value={site.id}>
                            {site.name}
                          </option>
                        ))}
                    </select>
                  </div>

                  <div className="space-y-3">
                    <label className="text-sm text-zinc-400 font-medium px-1">
                      Starting Task / Pay Area
                    </label>
                    <div className="grid grid-cols-5 gap-2">
                      {jobTypes.map((type) => {
                        const Icon = type.icon;
                        const isSelected = workType === type.id;
                        return (
                          <button
                            key={type.id}
                            onClick={() => setWorkType(type.id)}
                            className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border-2 transition-all ${
                              isSelected
                                ? `bg-${type.color}-500/20 border-${type.color}-500 text-${type.color}-400`
                                : 'bg-zinc-900/50 border-zinc-800 text-zinc-400'
                            }`}
                          >
                            <Icon className="w-5 h-5" />
                            <span className="text-xs font-medium">{type.label}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </>
              )}

              <div className="flex flex-col items-center gap-4 pt-4">
                {!isClockedIn ? (
                  <button
                    onClick={handleClockIn}
                    className="w-44 h-44 rounded-full flex flex-col items-center justify-center bg-gradient-to-br from-emerald-500 to-emerald-600 shadow-[0_8px_32px_rgba(16,185,129,0.4)] active:scale-95 transition-transform"
                  >
                    <Play className="w-14 h-14 text-white fill-white ml-2" />
                    <span className="text-white font-semibold text-lg mt-2">CLOCK IN</span>
                  </button>
                ) : (
                  <>
                    <button
                      onClick={handleClockOut}
                      className="w-44 h-44 rounded-full flex flex-col items-center justify-center bg-gradient-to-br from-red-500 to-red-600 shadow-[0_8px_32px_rgba(239,68,68,0.4)] active:scale-95 transition-transform"
                    >
                      <Square className="w-12 h-12 text-white fill-white" />
                      <span className="text-white font-semibold text-lg mt-2">CLOCK OUT</span>
                    </button>

                    <button
                      onClick={handleBreakToggle}
                      className={`px-8 py-4 rounded-2xl flex items-center gap-3 active:scale-95 transition-all ${
                        isOnBreak
                          ? 'bg-gradient-to-r from-amber-500 to-orange-500 shadow-[0_4px_16px_rgba(245,158,11,0.4)]'
                          : 'bg-zinc-800 shadow-lg'
                      }`}
                    >
                      <Coffee className={`w-6 h-6 ${isOnBreak ? 'text-white' : 'text-amber-400'}`} />
                      <span className="text-white font-medium">
                        {isOnBreak ? 'END BREAK' : 'START BREAK'}
                      </span>
                    </button>
                  </>
                )}
              </div>

              {!isClockedIn && (
                <p className="text-center text-xs text-zinc-500">Location tracking enabled</p>
              )}
            </div>
          )}

          {memberships.length > 0 && hasActiveBilling && currentView === 'timesheet' && (
            <div className="space-y-6">
              <div className="text-center">
                <h1 className="text-2xl font-bold text-white">Timesheet</h1>
                <p className="text-zinc-400 mt-1">View your work history</p>
              </div>

              <div className="bg-gradient-to-br from-zinc-900/80 to-zinc-950/80 backdrop-blur rounded-3xl p-6">
                <div className="flex items-center gap-2 text-zinc-400 mb-4">
                  <Calendar className="w-4 h-4" />
                  <span className="text-sm font-medium">Latest Entries</span>
                  <span className="text-xs text-zinc-500">
                    ({timeEntries.length} most recent)
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-zinc-800/30 rounded-2xl">
                    <Clock className="w-5 h-5 text-orange-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">
                      {timeEntries.length ? `${timeEntries.length} shifts` : '0'}
                    </p>
                    <p className="text-xs text-zinc-400 mt-1">Recent Activity</p>
                  </div>
                  <div className="text-center p-4 bg-zinc-800/30 rounded-2xl">
                    <Calendar className="w-5 h-5 text-blue-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">
                      {timeEntries[0] ? formatShortDate(timeEntries[0].clock_in) : '--'}
                    </p>
                    <p className="text-xs text-zinc-400 mt-1">Last Clock In</p>
                  </div>
                  <div className="text-center p-4 bg-zinc-800/30 rounded-2xl">
                    <TrendingUp className="w-5 h-5 text-emerald-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">
                      {timeEntries[0] && timeEntries[0].clock_out
                        ? formatShortDate(timeEntries[0].clock_out)
                        : '--'}
                    </p>
                    <p className="text-xs text-zinc-400 mt-1">Last Clock Out</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between bg-zinc-900/60 backdrop-blur rounded-2xl p-4">
                <button className="text-zinc-400 hover:text-white p-2">
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <div className="text-center">
                  <p className="text-lg font-semibold text-white">Recent Shifts</p>
                  <p className="text-sm text-zinc-400">Newest first</p>
                </div>
                <button className="text-zinc-400 p-2 opacity-30">
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4">
                {timeEntries.map((entry) => {
                  const workTypeData = entry.work_types;
                  const Icon = workTypeIconMap[workTypeData?.code] ?? Flag;
                  const sortedSegments = [...(entry.segments ?? [])].sort(
                    (a, b) => new Date(a.started_at) - new Date(b.started_at)
                  );
                  return (
                    <div key={entry.id} className="bg-zinc-900/60 backdrop-blur rounded-2xl p-4 space-y-3">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div className="p-2.5 rounded-xl bg-orange-500/20">
                            <Icon className="w-5 h-5 text-orange-400" />
                          </div>
                          <div>
                            <h3 className="font-semibold text-white">
                              {entry.job_sites?.name ?? 'Unknown site'}
                            </h3>
                            <p className="text-sm text-zinc-400 capitalize">
                              {workTypeData?.label ?? 'Work'}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <span className="text-lg font-bold text-white">
                            {entry.clock_out
                              ? formatDuration(
                                  new Date(entry.clock_out) -
                                    new Date(entry.clock_in) -
                                    (entry.break_minutes ?? 0) * 60000
                                )
                              : 'In progress'}
                          </span>
                          <p className="text-xs text-zinc-500">Net time</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between text-sm text-zinc-400 pt-2 border-t border-zinc-800/50">
                        <div className="flex items-center gap-1.5">
                          <Clock className="w-4 h-4" />
                          <span>
                            {formatTime(entry.clock_in)} -{' '}
                            {entry.clock_out ? formatTime(entry.clock_out) : 'Active'}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <Coffee className="w-4 h-4 text-amber-400" />
                          <span>{entry.break_minutes ?? 0} min</span>
                        </div>
                      </div>
                      {sortedSegments.length > 0 && (
                        <div className="space-y-2 border-t border-zinc-800/50 pt-3">
                          {sortedSegments.map((segment) => (
                            <div
                              key={segment.id}
                              className="flex items-center justify-between text-xs text-zinc-400"
                            >
                              <span>{segment.work_types?.label ?? 'Task'}</span>
                              <span>
                                {formatTime(segment.started_at)} -{' '}
                                {segment.ended_at ? formatTime(segment.ended_at) : 'Active'} ·{' '}
                                {formatSegmentDuration(segment, entry.clock_out)}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {memberships.length > 0 && hasActiveBilling && currentView === 'sites' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-bold text-white">Job Sites</h1>
                  <p className="text-zinc-400 mt-1">Manage your work locations</p>
                </div>
                {isAdmin && (
                  <button
                    type="button"
                    onClick={openNewSiteForm}
                    className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-xl flex items-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    Add Site
                  </button>
                )}
              </div>

              {isAdmin && isSiteFormOpen && (
                <form
                  onSubmit={handleSiteFormSubmit}
                  className="bg-zinc-900/70 backdrop-blur rounded-2xl p-4 space-y-4"
                >
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-white">
                      {editingSiteId ? 'Edit Job Site' : 'Add Job Site'}
                    </h2>
                    <button
                      type="button"
                      onClick={resetSiteForm}
                      className="text-zinc-400 hover:text-white p-1"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-zinc-400 font-medium">Site name</label>
                    <input
                      type="text"
                      value={siteForm.name}
                      onChange={(event) =>
                        setSiteForm((form) => ({ ...form, name: event.target.value }))
                      }
                      className="w-full h-12 bg-zinc-950/70 border border-zinc-800 rounded-2xl text-white text-base px-4"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-zinc-400 font-medium">Client</label>
                    <input
                      type="text"
                      value={siteForm.client}
                      onChange={(event) =>
                        setSiteForm((form) => ({ ...form, client: event.target.value }))
                      }
                      className="w-full h-12 bg-zinc-950/70 border border-zinc-800 rounded-2xl text-white text-base px-4"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-zinc-400 font-medium">Address</label>
                    <input
                      type="text"
                      value={siteForm.address}
                      onChange={(event) =>
                        setSiteForm((form) => ({ ...form, address: event.target.value }))
                      }
                      className="w-full h-12 bg-zinc-950/70 border border-zinc-800 rounded-2xl text-white text-base px-4"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-zinc-400 font-medium">Status</label>
                    <select
                      value={siteForm.status}
                      onChange={(event) =>
                        setSiteForm((form) => ({ ...form, status: event.target.value }))
                      }
                      className="w-full h-12 bg-zinc-950/70 border border-zinc-800 rounded-2xl text-white text-base px-4"
                    >
                      <option value="active">Active</option>
                      <option value="on_hold">On hold</option>
                      <option value="completed">Completed</option>
                    </select>
                  </div>

                  <button
                    type="submit"
                    disabled={isBusy}
                    className="w-full h-12 rounded-2xl bg-gradient-to-r from-orange-500 to-orange-600 text-white font-semibold disabled:opacity-60"
                  >
                    {isBusy ? 'Saving...' : editingSiteId ? 'Save changes' : 'Create site'}
                  </button>
                </form>
              )}

              <div className="space-y-3">
                <h2 className="text-sm font-medium text-zinc-400 px-1">Active Sites</h2>
                {jobSites
                  .filter((site) => site.status === 'active')
                  .map((site) => (
                    <div key={site.id} className="bg-zinc-900/60 backdrop-blur rounded-2xl p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          <div className="p-2.5 rounded-xl bg-orange-500/20">
                            <MapPin className="w-5 h-5 text-orange-400" />
                          </div>
                          <div>
                            <h3 className="font-semibold text-white">{site.name}</h3>
                            <div className="flex items-center gap-1.5 mt-1 text-sm text-zinc-400">
                              <Building2 className="w-3.5 h-3.5" />
                              <span>{site.client}</span>
                            </div>
                            <p className="text-sm text-zinc-500 mt-1">{site.address}</p>
                          </div>
                        </div>
                        {isAdmin && (
                          <div className="flex items-center gap-1">
                            <button
                              type="button"
                              onClick={() => openEditSiteForm(site)}
                              className="text-zinc-400 hover:text-white p-2"
                            >
                              <Edit3 className="w-4 h-4" />
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDeleteSite(site)}
                              className="text-zinc-400 hover:text-red-400 p-2"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                {jobSites.filter((site) => site.status === 'active').length === 0 && (
                  <p className="text-sm text-zinc-500 px-1">No active sites yet.</p>
                )}
              </div>

              <div className="space-y-3">
                <h2 className="text-sm font-medium text-zinc-400 px-1">On Hold / Completed</h2>
                {jobSites
                  .filter((site) => site.status !== 'active')
                  .map((site) => (
                    <div
                      key={site.id}
                      className="bg-zinc-900/60 backdrop-blur rounded-2xl p-4 opacity-60"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          <div className="p-2.5 rounded-xl bg-zinc-700/30">
                            <MapPin className="w-5 h-5 text-zinc-500" />
                          </div>
                          <div>
                            <h3 className="font-semibold text-white">{site.name}</h3>
                            <div className="flex items-center gap-1.5 mt-1 text-sm text-zinc-400">
                              <Building2 className="w-3.5 h-3.5" />
                              <span>{site.client}</span>
                            </div>
                            <p className="text-sm text-zinc-500 mt-1">{site.address}</p>
                          </div>
                        </div>
                        {isAdmin && (
                          <div className="flex items-center gap-1">
                            <button
                              type="button"
                              onClick={() => openEditSiteForm(site)}
                              className="text-zinc-400 hover:text-white p-2"
                            >
                              <Edit3 className="w-4 h-4" />
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDeleteSite(site)}
                              className="text-zinc-400 hover:text-red-400 p-2"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                {jobSites.filter((site) => site.status !== 'active').length === 0 && (
                  <p className="text-sm text-zinc-500 px-1">No inactive sites.</p>
                )}
              </div>

              {!isAdmin && (
                <p className="text-center text-xs text-zinc-500">
                  Contact an admin to add or update job sites.
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      <nav className="fixed bottom-0 left-0 right-0 bg-zinc-950/95 backdrop-blur-lg border-t border-zinc-900 px-4 py-2">
        <div className="max-w-md mx-auto flex items-center justify-around">
          <button
            onClick={() => setCurrentView('clock')}
            className={`flex flex-col items-center gap-1 px-4 py-2 rounded-xl transition-all ${
              currentView === 'clock' ? 'text-orange-400' : 'text-zinc-500'
            }`}
          >
            <Clock className={`w-6 h-6 ${currentView === 'clock' ? 'scale-110' : ''}`} />
            <span className="text-xs font-medium">Clock</span>
          </button>

          <button
            onClick={() => setCurrentView('timesheet')}
            className={`flex flex-col items-center gap-1 px-4 py-2 rounded-xl transition-all ${
              currentView === 'timesheet' ? 'text-orange-400' : 'text-zinc-500'
            }`}
          >
            <CalendarDays
              className={`w-6 h-6 ${currentView === 'timesheet' ? 'scale-110' : ''}`}
            />
            <span className="text-xs font-medium">Timesheet</span>
          </button>

          <button
            onClick={() => setCurrentView('sites')}
            className={`flex flex-col items-center gap-1 px-4 py-2 rounded-xl transition-all ${
              currentView === 'sites' ? 'text-orange-400' : 'text-zinc-500'
            }`}
          >
            <MapPin className={`w-6 h-6 ${currentView === 'sites' ? 'scale-110' : ''}`} />
            <span className="text-xs font-medium">Sites</span>
          </button>
        </div>
      </nav>

      <InstallPrompt />
    </div>
  );
}
