import type { FC, ReactNode } from 'react';

interface AppShellProps {
  readonly header: ReactNode;
  readonly children: ReactNode;
}

/** Estructura de pagina: cabecera fija y area de contenido a pantalla completa. */
export const AppShell: FC<AppShellProps> = ({ header, children }) => {
  return (
    <div className="flex h-full flex-col bg-canvas">
      {header}
      <main className="flex min-h-0 flex-1 flex-col">{children}</main>
    </div>
  );
};

export default AppShell;