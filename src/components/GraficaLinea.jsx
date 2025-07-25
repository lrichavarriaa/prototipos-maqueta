import React, { memo } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const GraficaLinea = memo(function GraficaLinea({
  datos,
  titulo,
  color = "#8884d8",
  dataKey = "presion",
  unidad = "PSI",
  domainMin = 0,
  domainMax = 7, // Reducido a 7 PSI para mejor visualización de cambios
  etiqueta = "Valor"
}) {
  if (!datos || datos.length === 0) {
    return (
      <Card className="h-[100px]">
        <CardHeader>
          <CardTitle className="text-xs font-medium">{titulo}</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[140px]">
          <p className="text-sm text-muted-foreground">No hay datos suficientes</p>
        </CardContent>
      </Card>
    );
  }

  // Crear un ID único para el gradiente
  const gradienteId = `color${titulo.replace(/\s+/g, '')}${dataKey}`;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xs font-medium">{titulo}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[100px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={datos}
              margin={{ top: 5, right: 5, left: -20, bottom: 5 }}
            >
              <defs>
                <linearGradient id={gradienteId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={color} stopOpacity={0.8} />
                  <stop offset="95%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="time"
                tick={{ fontSize: 9 }}
                interval="preserveStartEnd"
                tickCount={2}
                domain={['dataMin', 'dataMax']}
              />
              <YAxis
                domain={[domainMin, domainMax]}
                tick={{ fontSize: 9 }}
                tickCount={3}
              />
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <Tooltip
                contentStyle={{
                  fontSize: '10px',
                  padding: '4px 8px',
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px'
                }}
                labelStyle={{ fontSize: '10px' }}
                itemStyle={{ fontSize: '10px', padding: 0, margin: 0 }}
                formatter={(value) => {
                  // Los datos ya vienen convertidos a PSI desde App.jsx
                  const valorMostrar = typeof value === 'number' ? value.toFixed(1) : value;
                  return [`${valorMostrar} ${unidad}`, etiqueta];
                }}
              />
              <Area
                type="monotone"
                dataKey={dataKey}
                stroke={color}
                fillOpacity={1}
                fill={`url(#${gradienteId})`}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
});

export { GraficaLinea };