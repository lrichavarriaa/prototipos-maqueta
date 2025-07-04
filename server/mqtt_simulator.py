#!/usr/bin/env python3

import json
import time
import random
import paho.mqtt.client as mqtt
from typing import Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class Valvula:
    id: int
    presion: float
    estado: bool
    flujo_max: float = 10.0

    def get_flujo_actual(self) -> float:
        """Calcula el flujo actual basado en estado y presión"""
        if not self.estado:
            return 0.0
        return (self.presion / 100.0) * self.flujo_max

    def actualizar_presion(self, hay_flujo_real=False):
        """Actualiza la presión con variación realista basada en flujo real"""
        if self.estado and hay_flujo_real:
            # Válvula abierta CON flujo real: presión alta y fluctuante
            variacion = random.uniform(-1.0, 1.0)
            self.presion = max(75.0, min(85.0, self.presion + variacion))
        elif self.estado and not hay_flujo_real:
            # Válvula abierta SIN flujo: presión media (agua estancada)
            variacion = random.uniform(-0.3, 0.3)
            self.presion = max(15.0, min(25.0, self.presion + variacion))
        else:
            # Válvula cerrada: presión muy baja y estable
            variacion = random.uniform(-0.2, 0.2)
            self.presion = max(2.0, min(8.0, self.presion + variacion))


@dataclass
class Tanque:
    nombre: str
    capacidad: float
    nivel_actual: float
    flujo_entrada: float = 0.0
    flujo_salida: float = 0.0

    def actualizar_nivel(self, dt: float = 2.0):
        """Actualiza el nivel del tanque basado en flujos"""
        # Calcular espacio disponible
        espacio_disponible = self.capacidad - self.nivel_actual

        # Limitar flujo de entrada según espacio disponible
        flujo_entrada_real = min(self.flujo_entrada, espacio_disponible / dt)

        # Calcular cambio neto
        flujo_neto = flujo_entrada_real - self.flujo_salida
        cambio = flujo_neto * dt

        # Actualizar nivel con límites estrictos
        self.nivel_actual = max(0.0, min(self.capacidad, self.nivel_actual + cambio))

    def get_porcentaje(self) -> float:
        return (self.nivel_actual / self.capacidad) * 100.0


class SistemaSimulacion:
    def __init__(self):
        self.valvulas = {
            1: Valvula(1, 3.0, False),  # Empezar con presión muy baja
            2: Valvula(2, 3.0, False),
            3: Valvula(3, 3.0, False),
        }

        self.tanques = {
            "principal": Tanque("Principal", 2000.0, 2000.0),  # Empezar LLENO
            "secundario1": Tanque("Secundario1", 1000.0, 0.0),  # Empezar VACÍO
            "secundario2": Tanque("Secundario2", 1000.0, 0.0),  # Empezar VACÍO
        }

        self.flujo_base = 5.0

    def calcular_flujos(self):
        """Calcula los flujos del sistema basado en topología y estados de válvulas"""
        # Verificar si hay espacio en tanques de destino
        espacio_s1 = (
            self.tanques["secundario1"].capacidad
            - self.tanques["secundario1"].nivel_actual
        )
        espacio_s2 = (
            self.tanques["secundario2"].capacidad
            - self.tanques["secundario2"].nivel_actual
        )

        # Solo hay flujo si las válvulas están abiertas Y hay espacio en el tanque destino
        flujo_v2 = (
            self.flujo_base
            if (
                self.valvulas[1].estado and self.valvulas[2].estado and espacio_s1 > 1.0
            )
            else 0.0
        )
        flujo_v3 = (
            self.flujo_base
            if (
                self.valvulas[1].estado and self.valvulas[3].estado and espacio_s2 > 1.0
            )
            else 0.0
        )

        # El flujo principal es la suma de lo que realmente sale hacia otros tanques
        flujo_principal = flujo_v2 + flujo_v3

        # Actualizar flujos en tanques
        self.tanques["principal"].flujo_salida = flujo_principal
        self.tanques["secundario1"].flujo_entrada = flujo_v2
        self.tanques["secundario2"].flujo_entrada = flujo_v3

        return {
            "principal_a_v1": flujo_principal,
            "v1_a_v2": flujo_v2,
            "v1_a_v3": flujo_v3,
            "v2_a_s1": flujo_v2,
            "v3_a_s2": flujo_v3,
        }

    def actualizar_sistema(self):
        """Actualiza todo el sistema"""
        # Calcular flujos
        flujos = self.calcular_flujos()

        # Determinar qué válvulas tienen flujo real
        hay_flujo_v1 = flujos["principal_a_v1"] > 0
        hay_flujo_v2 = flujos["v2_a_s1"] > 0
        hay_flujo_v3 = flujos["v3_a_s2"] > 0

        # Actualizar válvulas con información de flujo real
        self.valvulas[1].actualizar_presion(hay_flujo_v1)
        self.valvulas[2].actualizar_presion(hay_flujo_v2)
        self.valvulas[3].actualizar_presion(hay_flujo_v3)

        # Actualizar tanques
        for tanque in self.tanques.values():
            tanque.actualizar_nivel()

        return flujos

    def cambiar_valvula(self, valvula_id: int, nuevo_estado: bool):
        """Cambia el estado de una válvula"""
        if valvula_id in self.valvulas:
            self.valvulas[valvula_id].estado = nuevo_estado
            print(f"🔧 Válvula {valvula_id} {'ABIERTA' if nuevo_estado else 'CERRADA'}")

    def get_datos_mqtt(self, flujos: Dict[str, float]) -> Dict[str, Any]:
        """Genera los datos para enviar por MQTT"""
        return {
            # Tanques
            "principal": round(self.tanques["principal"].nivel_actual, 1),
            "secundario1": round(self.tanques["secundario1"].nivel_actual, 1),
            "secundario2": round(self.tanques["secundario2"].nivel_actual, 1),
            # Válvulas
            "valvula1_presion": round(self.valvulas[1].presion, 1),
            "valvula1_estado": self.valvulas[1].estado,
            "valvula2_presion": round(self.valvulas[2].presion, 1),
            "valvula2_estado": self.valvulas[2].estado,
            "valvula3_presion": round(self.valvulas[3].presion, 1),
            "valvula3_estado": self.valvulas[3].estado,
            # Flujos para líneas dinámicas
            "flujos": flujos,
            "flujo_total": round(sum(flujos.values()), 2),
        }


class MQTTManager:
    def __init__(self, sistema: SistemaSimulacion):
        self.sistema = sistema
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ MQTT Conectado")
            # Suscribirse a comandos de válvulas
            client.subscribe("tanques/comandos")
            print("🎛️  Escuchando comandos...")
        else:
            print(f"❌ Error MQTT: {rc}")

    def on_message(self, client, userdata, msg):
        """Maneja comandos recibidos"""
        try:
            comando = json.loads(msg.payload.decode())
            if comando.get("tipo") == "valvula":
                valvula_id = comando.get("id")
                estado = comando.get("estado")
                self.sistema.cambiar_valvula(valvula_id, estado)
        except Exception as e:
            print(f"❌ Error procesando comando: {e}")

    def conectar(self):
        """Conecta al broker MQTT"""
        try:
            self.client.connect("localhost", 1883, 60)
            self.client.loop_start()
            return True
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            return False

    def publicar_datos(self, datos: Dict[str, Any]):
        """Publica datos del sistema"""
        mensaje = json.dumps(datos)
        self.client.publish("tanques/datos", mensaje)

    def desconectar(self):
        """Desconecta del broker"""
        self.client.disconnect()


def main():
    # Inicializar sistema
    sistema = SistemaSimulacion()
    mqtt_manager = MQTTManager(sistema)

    if not mqtt_manager.conectar():
        return

    print("🚀 Simulador avanzado iniciado...")
    print("📊 Sistema de tanques en cascada activo")
    print("🎛️  Control bidireccional de válvulas habilitado")

    try:
        while True:
            # Actualizar sistema
            flujos = sistema.actualizar_sistema()

            # Preparar datos
            datos = sistema.get_datos_mqtt(flujos)

            # Publicar
            mqtt_manager.publicar_datos(datos)

            # Log de estado
            principal_pct = (datos["principal"] / 2000.0) * 100
            s1_pct = (datos["secundario1"] / 1000.0) * 100
            s2_pct = (datos["secundario2"] / 1000.0) * 100

            # Indicadores de estado
            v1_flujo = flujos.get("principal_a_v1", 0) > 0
            v2_flujo = flujos.get("v2_a_s1", 0) > 0
            v3_flujo = flujos.get("v3_a_s2", 0) > 0

            v1_estado = (
                "🟢💧"
                if (sistema.valvulas[1].estado and v1_flujo)
                else "🟢⚪" if sistema.valvulas[1].estado else "🔴"
            )
            v2_estado = (
                "🟢💧"
                if (sistema.valvulas[2].estado and v2_flujo)
                else "🟢⚪" if sistema.valvulas[2].estado else "🔴"
            )
            v3_estado = (
                "🟢💧"
                if (sistema.valvulas[3].estado and v3_flujo)
                else "🟢⚪" if sistema.valvulas[3].estado else "🔴"
            )

            s1_estado = "🚫LLENO" if s1_pct >= 99 else f"{s1_pct:.0f}%"
            s2_estado = "🚫LLENO" if s2_pct >= 99 else f"{s2_pct:.0f}%"

            print(
                f"📊 Principal: {datos['principal']:.0f}L ({principal_pct:.0f}%) | "
                f"S1: {datos['secundario1']:.0f}L ({s1_estado}) | "
                f"S2: {datos['secundario2']:.0f}L ({s2_estado})"
            )
            print(
                f"🚿 V1: {v1_estado} ({datos['valvula1_presion']:.1f}kPa) | "
                f"V2: {v2_estado} ({datos['valvula2_presion']:.1f}kPa) | "
                f"V3: {v3_estado} ({datos['valvula3_presion']:.1f}kPa) | "
                f"Flujo: {datos.get('flujo_total', 0):.1f}L/s"
            )

            time.sleep(2)

    except KeyboardInterrupt:
        print("\n🛑 Simulador detenido")
    finally:
        mqtt_manager.desconectar()


if __name__ == "__main__":
    main()
