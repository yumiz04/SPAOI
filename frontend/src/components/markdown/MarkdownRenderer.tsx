import { memo, useMemo } from 'react';
import type { FC } from 'react';
import ReactMarkdown from 'react-markdown';
import type { Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { MarkdownTable } from './MarkdownTable';

interface MarkdownRendererProps {
  readonly markdown: string;
}

/*
  Mapa de elementos markdown a clases del tema.
  El agente responde con H2/H3, negritas, listas, codigo en linea y sobre todo tablas
  GFM; cada elemento tiene su propio tratamiento para que la respuesta se lea bien.
  react-markdown no interpreta HTML crudo, asi que la respuesta del modelo es inerte.
*/
const components: Components = {
  h1: ({ children }) => (
    <h1 className="mb-3 mt-6 text-xl font-semibold text-ink first:mt-0">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="mb-2 mt-6 text-lg font-semibold tracking-tight text-ink first:mt-0">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="mb-2 mt-5 text-base font-semibold text-ink first:mt-0">{children}</h3>
  ),
  h4: ({ children }) => <h4 className="mb-1 mt-4 text-sm font-semibold text-ink">{children}</h4>,
  p: ({ children }) => <p className="my-2 leading-relaxed text-ink-muted first:mt-0 last:mb-0">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold text-ink">{children}</strong>,
  em: ({ children }) => <em className="italic text-ink-muted">{children}</em>,
  a: ({ children, href }) => (
    <a
      className="font-medium text-brand underline decoration-brand/40 underline-offset-2 hover:decoration-brand"
      href={href}
      rel="noreferrer noopener"
      target="_blank"
    >
      {children}
    </a>
  ),
  ul: ({ children }) => <ul className="my-2 list-disc space-y-1.5 pl-5 text-ink-muted">{children}</ul>,
  ol: ({ children }) => <ol className="my-2 list-decimal space-y-1.5 pl-5 text-ink-muted">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed [&>ul]:my-1 [&>ol]:my-1">{children}</li>,
  blockquote: ({ children }) => (
    <blockquote className="my-3 border-l-4 border-brand/50 bg-brand-soft/50 py-2 pl-4 text-ink-muted">
      {children}
    </blockquote>
  ),
  hr: () => <hr className="my-5 border-line" />,
  table: ({ children }) => <MarkdownTable>{children}</MarkdownTable>,
  code: ({ children, className }) => {
    const isBlock = className?.startsWith('language-') ?? false;
    if (isBlock) {
      return <code className={`${className ?? ''} font-mono text-[13px] leading-relaxed`}>{children}</code>;
    }
    return (
      <code className="rounded bg-surface-3 px-1.5 py-0.5 font-mono text-[0.85em] text-ink">
        {children}
      </code>
    );
  },
  pre: ({ children }) => (
    <pre className="my-3 overflow-x-auto rounded-card border border-line bg-surface-3 p-4 text-ink">
      {children}
    </pre>
  ),
};

/** Convierte la respuesta markdown del agente en contenido formateado. */
export const MarkdownRenderer: FC<MarkdownRendererProps> = memo(({ markdown }) => {
  const remarkPlugins = useMemo(() => [remarkGfm], []);

  return (
    <div className="text-[15px]">
      <ReactMarkdown remarkPlugins={remarkPlugins} components={components}>
        {markdown}
      </ReactMarkdown>
    </div>
  );
});

MarkdownRenderer.displayName = 'MarkdownRenderer';

export default MarkdownRenderer;