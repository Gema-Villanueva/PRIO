# Decisiones técnicas de PRIO

Este documento resume las principales decisiones adoptadas durante el
desarrollo, su motivo y sus consecuencias.

## 1. Separar el portal del cliente del panel interno

**Decisión:** utilizar dos aplicaciones Streamlit independientes.

**Motivo:** huéspedes y anfitriones solo necesitan enviar un aviso y recibir
una confirmación. La clasificación, las métricas y las herramientas de revisión
son información interna.

**Consecuencia:** la experiencia resulta más clara y no expone identificadores,
proveedores ni decisiones internas al cliente. A cambio, deben mantenerse dos
procesos de interfaz.

## 2. Centralizar la lógica en FastAPI

**Decisión:** las interfaces acceden a los datos y a los modelos a través de una
API común.

**Motivo:** evita duplicar reglas en Streamlit y permite probar la lógica sin
depender de la interfaz visual.

**Consecuencia:** el portal y el panel necesitan que FastAPI esté activo, pero
la aplicación queda dividida en responsabilidades claras.

## 3. Validar la salida del modelo con Pydantic

**Decisión:** exigir una respuesta JSON con categorías y valores definidos.

**Motivo:** una respuesta de lenguaje natural puede omitir campos, inventar
valores o usar formatos difíciles de procesar.

**Consecuencia:** las respuestas inválidas se rechazan y pueden reintentarse.
La validación estructural reduce errores, aunque no garantiza que una
clasificación válida sea correcta.

## 4. Mantener revisión humana antes de derivar

**Decisión:** ninguna propuesta se deriva hasta que una persona la aprueba o
corrige.

**Motivo:** la clasificación influye en la prioridad y el destino de una
solicitud, y un modelo puede equivocarse o reproducir sesgos.

**Consecuencia:** mejora el control y la trazabilidad, pero introduce un paso
manual y no elimina completamente el tiempo de espera.

## 5. Ofrecer Groq y Ollama

**Decisión:** soportar un proveedor externo y otro local con un esquema común.

**Motivo:** permite comparar velocidad, privacidad y dependencia de servicios
externos.

**Consecuencia:** Groq fue más rápido en la evaluación, mientras que Ollama
permite procesar localmente. El modo automático aporta continuidad usando
Ollama como respaldo.

## 6. Guardar los datos en SQLite

**Decisión:** usar una base de datos SQLite para el prototipo.

**Motivo:** no necesita un servidor adicional, es fácil de inspeccionar y
permite demostrar persistencia con una configuración mínima.

**Consecuencia:** es apropiada para desarrollo y demostración local, pero no
para gran concurrencia o varios servidores. Un despliegue real debería utilizar
una base de datos compartida como PostgreSQL.

## 7. Representar la derivación mediante bandejas internas

**Decisión:** guardar cada derivación y mostrarla en una bandeja por destino.

**Motivo:** permite demostrar el ciclo completo sin depender de correo,
mensajería o servicios de tickets externos.

**Consecuencia:** PRIO demuestra a quién se enviaría la solicitud y permite
actualizarla de `Nueva` a `En gestión` y `Resuelta`, pero todavía no entrega
notificaciones reales.

## 8. Conservar propuesta y decisión definitiva

**Decisión:** guardar la clasificación original junto con la revisión final.

**Motivo:** permite analizar errores del modelo y comprobar qué cambió la
persona revisora.

**Consecuencia:** el historial aporta trazabilidad y puede utilizarse en el
futuro para ampliar la evaluación o mejorar las instrucciones del modelo.

## 9. Usar una justificación breve

**Decisión:** mostrar una explicación concisa de la clasificación en lugar de
solicitar o exponer razonamientos internos extensos del modelo.

**Motivo:** la persona revisora necesita evidencia suficiente para valorar la
propuesta, pero no una cadena de pensamiento privada ni texto innecesariamente
largo.

**Consecuencia:** la decisión es más fácil de revisar y auditar. La
justificación debe tratarse como una explicación generada que también puede
contener errores.

## 10. Evaluar ambos modelos con los mismos casos

**Decisión:** utilizar un conjunto común de diez solicitudes para Groq y
Ollama.

**Motivo:** una comparación solo es útil si ambos proveedores reciben los
mismos casos y se miden con los mismos criterios.

**Consecuencia:** los resultados permiten comparar calidad, latencia, tokens y
coste estimado. El conjunto es pequeño y controlado, por lo que el resultado
10/10 no demuestra un rendimiento perfecto en situaciones reales.
