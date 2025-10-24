# Moderación con Machine Learning (Naive Bayes)

Este documento explica a fondo el modo ML de ChatGuard: cuándo usarlo, cómo configurarlo, cómo entrena y cómo diagnosticar su comportamiento.

## Objetivos

- Detectar toxicidad y spam con un clasificador Naive Bayes configurable desde `rules.yaml`.
- Mantener la compatibilidad total con la moderación clásica.
- Permitir activar/desactivar ML por chat y ajustar sensibilidad/acciones sin tocar código.

## Conceptos clave

- ML es opcional. Si `moderation.ml.enabled: false`, el bot usa solo el modo clásico.
- Al activarlo, el flujo evalúa primero ML y, si supera umbrales, aplica la acción inmediata (warn/mute/kick/ban).
- Después (o si ML no dispara), sigue aplicando la moderación clásica (palabras prohibidas, regex, flood, etc.).

## Configuración

Sección en `config/rules.yaml` (por `default` o override por chat):

```yaml
moderation:
  - `immediate`: aplica la acción inmediata (warn/mute/kick/ban) definida en `action`.
  - `thresholds`: solo suma una infracción y respeta `moderation.thresholds` para decidir la sanción.
    toxicity_threshold: 0.55 # Sensibilidad para toxicidad (0-1)
    spam_threshold: 0.90     # Sensibilidad para spam (0-1)
    training:
      toxic:
        - "idiota"
        - "imbecil"
        - "maldito"
      spam:
    ml_mode: immediate       # immediate | thresholds
        - "gana dinero rapido"
        - "haz clic aqui"
      normal:
        - "hola como estas"
        - "gracias por la ayuda"
```
- `toxicity_threshold` y `spam_threshold`: Umbrales en [0,1].
- `training.toxic|spam|normal`: Listas editables de ejemplos. La clase `normal` mejora la calibración.
  - Evalúa ML primero; si supera umbral, ejecuta según `ml_mode` (acción directa o suma infracción y thresholds).
  - Si ML no dispara, continúa con el modo clásico.

- Tokenizador (`src/ml/tokenizer.py`):
  - Remueve stopwords comunes en español.
- Modelo (`src/ml/nb_text.py`):
    ml: { enabled: true, ml_mode: immediate, action: mute, toxicity_threshold: 0.5 }
- Runtime (`src/ml/runtime.py`):
  - Reconstruye el modelo al cambiar el YAML (firma diferente).
- Handler (`src/handlers/moderacion.py`):
    ml: { enabled: true, ml_mode: immediate, action: warn, delete_on_ml: false, spam_threshold: 0.85 }
  - Si ML no dispara, continúa con el modo clásico.
## Aprendizaje sin ML (listas manuales)

Puedes ampliar el modo clásico con listas en `moderation.learning`:

 - ML que respeta thresholds (suma infracción) con acción clásica:
   ```yaml
   moderation:
     ml: { enabled: true, ml_mode: thresholds, toxicity_threshold: 0.55 }
   ```
```yaml
moderation:
    toxic_words: ["idiota", "imbecil", "imbécil"]
    spam_words: ["oferta limitada", "gana dinero rapido"]
```

- Estas entradas se suman a `banned_words` en tiempo de ejecución.
- Comparación por substring en minúsculas (sensible a acentos); añade variantes cuando importe.

## Recetas rápidas

- “Mute” inmediato por toxicidad leve:
  ```yaml
  moderation:
    ml: { enabled: true, action: mute, toxicity_threshold: 0.5 }
  ```
- Solo advertir (sin borrar) cuando ML detecte spam:
  ```yaml
  moderation:
    ml: { enabled: true, action: warn, delete_on_ml: false, spam_threshold: 0.85 }
  ```
- Desactivar ML en un grupo ruidoso (seguir clásico):
  ```yaml
  moderation:
    ml: { enabled: false }
  ```

## Logs y diagnóstico

- Se emiten eventos JSON estructurados:
  - `ml_eval`: `{ scores: {toxic, spam}, toxicity_threshold, spam_threshold, triggered }`
  - `ml_action`: `{ action, scores: {toxic, spam} }`
- Si no ves disparos, baja `toxicity_threshold` o añade más ejemplos a `training.toxic` y `training.normal`.
- Usa `/reload` en Telegram para forzar recarga del YAML si el bot ya está corriendo.

## Buenas prácticas

- Mantén `toxic`, `spam` y `normal` con tamaños similares.
- Añade frases realistas multi-palabra (no solo insultos sueltos).
- Evita ejemplos contradictorios (una misma frase en dos clases).
- Revisa sesgos: palabras que podrían ser legítimas en contextos neutros.

## Preguntas frecuentes (FAQ)

- ¿Apagar ML desactiva la moderación? No; el modo clásico sigue activo.
- ¿Cubre acentos y variantes? ML sí (normaliza diacríticos). El modo clásico no: añade ambas variantes si es crucial.
- ¿Consume los thresholds clásicos? No; `ml.action` se aplica de inmediato.
- ¿Puedo tener diferentes entrenamientos por grupo? Sí, en overrides por `chat_id`.

## Compatibilidad y seguridad

- En caso de error interno de ML, el flujo cae al modo clásico (fail-safe).
- No hay llamadas externas: todo se ejecuta en memoria (privacidad local).

---

Para un resumen de claves y más ejemplos, consulta también `docs/rules_reference.md` y la guía de admins `docs/guia_admin.md`.
