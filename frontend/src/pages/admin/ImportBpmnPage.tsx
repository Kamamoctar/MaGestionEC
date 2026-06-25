export default function ImportBpmnPage() {
  return (
    <div>
      <h1 className="text-xl font-semibold text-gray-800 mb-2">Import BPMN</h1>
      <p className="text-gray-500 text-sm mb-8">Chargez un fichier .bpmn ou .xml pour générer automatiquement un circuit de traitement.</p>

      <div className="bg-white rounded-xl border-2 border-dashed border-gray-200 p-16 flex flex-col items-center gap-3 text-center">
        <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center">
          <svg className="w-6 h-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </div>
        <p className="font-medium text-gray-700">Glissez-déposez votre fichier BPMN ici</p>
        <p className="text-xs text-gray-400">ou cliquez pour parcourir (.bpmn, .xml)</p>
        <button className="mt-2 px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-dark">
          Choisir un fichier
        </button>
      </div>

      <p className="mt-4 text-xs text-gray-400 text-center">
        Fonctionnalité complète disponible dans la prochaine itération (parsing lxml + mapping lanes → postes).
      </p>
    </div>
  );
}
