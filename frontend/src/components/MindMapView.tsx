import type { MindMapNode } from "@/lib/api";

function Node({ node, depth }: { node: MindMapNode; depth: number }) {
  const colors = [
    "bg-indigo-600 text-white",
    "bg-indigo-100 text-indigo-900",
    "bg-sky-100 text-sky-900",
    "bg-emerald-100 text-emerald-900",
  ];
  const color = colors[Math.min(depth, colors.length - 1)];
  return (
    <li className="relative">
      <span
        className={`inline-block rounded-lg px-3 py-1 text-sm font-medium ${color}`}
      >
        {node.root}
      </span>
      {node.children?.length > 0 && (
        <ul className="mt-2 ml-6 space-y-2 border-l border-slate-200 pl-4">
          {node.children.map((child, i) => (
            <Node key={i} node={child} depth={depth + 1} />
          ))}
        </ul>
      )}
    </li>
  );
}

export default function MindMapView({ data }: { data: MindMapNode | null }) {
  if (!data) {
    return <p className="text-sm text-slate-500">No mind map available.</p>;
  }
  return (
    <ul className="space-y-2">
      <Node node={data} depth={0} />
    </ul>
  );
}
