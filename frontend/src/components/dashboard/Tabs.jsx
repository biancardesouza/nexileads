export default function Tabs({ activeTab, onChange, countSalvos, countNovos }) {
  return (
    <nav className="tabs">
      <button
        className={`tab-btn${activeTab === "salvos" ? " active" : ""}`}
        onClick={() => onChange("salvos")}
      >
        Meus leads <span className="badge-count">{countSalvos}</span>
      </button>
      <button
        className={`tab-btn${activeTab === "novos" ? " active" : ""}`}
        onClick={() => onChange("novos")}
      >
        Novos leads <span className="badge-count">{countNovos}</span>
      </button>
    </nav>
  );
}
