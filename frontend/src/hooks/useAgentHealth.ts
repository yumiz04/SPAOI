import { useEffect, useState } from 'react';
import { checkHealth } from '../api/agentClient';

export interface UseAgentHealthResult {
  /** `null` mientras la sonda inicial sigue en curso. */
  readonly isReachable: boolean | null;
}

/**
 * Sonda el endpoint de salud al montar para distinguir "el agente esta caido" de
 * "el agente tardo". Solo se ejecuta una vez: no es un monitor.
 */
export function useAgentHealth(): UseAgentHealthResult {
  const [isReachable, setIsReachable] = useState<boolean | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    void checkHealth(controller.signal).then((reachable) => {
      if (!controller.signal.aborted) {
        setIsReachable(reachable);
      }
    });

    return () => controller.abort();
  }, []);

  return { isReachable };
}