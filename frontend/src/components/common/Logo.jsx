export default function Logo() {
  return (
    <div className="logo-mark">
      <svg className="logo-icon" viewBox="0 0 64 64" aria-hidden="true">
        <rect width="64" height="64" rx="14" fill="#0d0f12" />
        <line x1="22" y1="18" x2="22" y2="46" stroke="#eef0f2" strokeWidth="5" strokeLinecap="round" />
        <line x1="42" y1="18" x2="42" y2="46" stroke="#eef0f2" strokeWidth="5" strokeLinecap="round" />
        <line x1="22" y1="18" x2="42" y2="46" stroke="#0ec090" strokeWidth="5" strokeLinecap="round" />
        <circle cx="32" cy="32" r="3" fill="#0ec090" />
      </svg>
      NexiLeads
    </div>
  );
}
