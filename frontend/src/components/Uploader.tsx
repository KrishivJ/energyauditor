import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

export default function Uploader({
  onFiles,
  busy,
}: {
  onFiles: (files: File[]) => void;
  busy: boolean;
}) {
  const [picked, setPicked] = useState<File[]>([]);

  const onDrop = useCallback((accepted: File[]) => {
    setPicked((prev) => {
      const names = new Set(prev.map((f) => f.name));
      return [...prev, ...accepted.filter((f) => !names.has(f.name))];
    });
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
        ".xlsx",
      ],
      "application/vnd.ms-excel": [".xls"],
      "text/csv": [".csv"],
    },
  });

  return (
    <div className="panel p-6">
      <h2 className="font-display text-lg font-semibold">Upload meter files</h2>
      <p className="mt-1 text-sm text-muted">
        One file per circuit (.xlsx, .xls, .csv). Columns are auto-detected per
        file — you can override them next.
      </p>

      <div
        {...getRootProps()}
        className={`mt-4 cursor-pointer rounded-lg border-2 border-dashed p-10 text-center transition-colors ${
          isDragActive
            ? "border-amber bg-amber/5"
            : "border-hairline hover:border-amber/50"
        }`}
      >
        <input {...getInputProps()} />
        <p className="text-sm">
          {isDragActive
            ? "Drop the files here…"
            : "Drag meter files here, or click to browse"}
        </p>
      </div>

      {picked.length > 0 && (
        <div className="mt-4">
          <div className="label mb-2">{picked.length} file(s) selected</div>
          <ul className="max-h-40 space-y-1 overflow-auto text-sm">
            {picked.map((f) => (
              <li
                key={f.name}
                className="flex justify-between rounded border border-hairline px-3 py-1.5"
              >
                <span className="truncate">{f.name}</span>
                <button
                  className="text-muted hover:text-waste"
                  onClick={() =>
                    setPicked((p) => p.filter((x) => x.name !== f.name))
                  }
                >
                  remove
                </button>
              </li>
            ))}
          </ul>
          <button
            className="btn btn-primary mt-4"
            disabled={busy || picked.length === 0}
            onClick={() => onFiles(picked)}
          >
            {busy ? "Uploading…" : `Upload ${picked.length} file(s)`}
          </button>
        </div>
      )}
    </div>
  );
}
