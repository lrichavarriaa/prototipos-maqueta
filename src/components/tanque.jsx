import { Badge } from "@/components/ui/badge";

export function Tanque({ litros, capacidad = 1000 }) {
  const porcentaje = Math.min(100, (litros / capacidad) * 100);

  return (
    <div className="flex flex-col items-center space-y-2">
      {/* Información del tanque */}
      <div className="flex items-center space-x-2">
        <span className="font-semibold text-primary">{litros.toFixed(0)}</span>
        <span className="text-xs text-muted-foreground">/ {capacidad}L</span>
      </div>

      <div className="relative w-[80px] h-[150px] border-2 border-border rounded-md overflow-hidden bg-card">
        <div
          className="absolute bottom-0 w-full bg-blue-500 transition-all duration-300"
          style={{
            height: `${porcentaje}%`,
            opacity: 0.6
          }}
        />

        <Badge
          className="absolute bottom-4 left-1/2 -translate-x-1/2"
        >
          {porcentaje.toFixed(0)}%
        </Badge>
      </div>
    </div>
  );
}