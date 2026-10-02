import type { FC, ReactNode } from 'react';

interface MarkdownTableProps {
  readonly children?: ReactNode;
}

/**
 * Envuelve las tablas markdown en un contenedor con desplazamiento horizontal.
 * El agente responde con tablas anchas (producto, riesgo, stock, cobertura, lead time)
 * y en pantallas angostas se desbordarian sin esto.
 *
 * El detalle visual de las celdas vive en `.md-table` (src/index.css) para no
 * dispersar la clase por cada elemento.
 */
export const MarkdownTable: FC<MarkdownTableProps> = ({ children }) => {
  return (
    <div className="my-4 max-w-full overflow-x-auto rounded-card border border-line bg-surface shadow-soft">
      <table className="md-table w-full border-collapse text-sm">{children}</table>
    </div>
  );
};

export default MarkdownTable;