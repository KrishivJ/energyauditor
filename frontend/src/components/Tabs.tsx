// Segmented control with a sliding thumb. Equal-width tabs, so the thumb is one
// slot wide and translates by whole slots — no measurement needed.

export type Tab = { id: string; label: string };

export default function Tabs({
  tabs,
  active,
  onChange,
}: {
  tabs: Tab[];
  active: string;
  onChange: (id: string) => void;
}) {
  const n = tabs.length;
  const activeIndex = Math.max(
    0,
    tabs.findIndex((t) => t.id === active),
  );
  return (
    <div className="seg" role="tablist" aria-label="View">
      <span
        className="seg-thumb"
        style={{
          top: 4,
          bottom: 4,
          left: 4,
          width: `calc((100% - 8px) / ${n})`,
          transform: `translateX(${activeIndex * 100}%)`,
        }}
      />
      {tabs.map((t) => (
        <button
          key={t.id}
          role="tab"
          aria-selected={t.id === active}
          data-active={t.id === active}
          className="seg-btn flex-1"
          onClick={() => onChange(t.id)}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
