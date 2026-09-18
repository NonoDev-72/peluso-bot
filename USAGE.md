# Uso

Todo (menos los comandos slash) se configura desde el panel web — no hace falta tocar código ni la base de
datos a mano.

## Panel web

1. Entrá a la URL donde corre el panel (por ejemplo `http://localhost:8000`) e iniciá sesión con Discord.
2. Vas a ver la lista de servidores donde tenés permiso de **Manage Server** (o cualquier servidor, si tu
   Discord ID está en `BOT_OWNER_IDS`).
3. Elegí un servidor para entrar a su configuración.

### 👋 Bienvenida

- **Activar mensaje de bienvenida**: prendé el checkbox y elegí el ID del canal de texto donde se va a
  publicar.
- **Mensaje**: soporta los placeholders `{member}` (mención), `{guild}` (nombre del servidor) y
  `{member_count}` (cantidad de miembros).
- **Imagen de fondo**: subí una imagen (PNG/JPEG/WEBP). A partir de ahí, cada bienvenida se manda como una
  **tarjeta generada**: tu imagen de fondo, con el avatar del usuario recortado en círculo y el mensaje
  (sin Markdown) dibujado debajo, agrupados sobre un panel semitransparente para que se lean bien encima de
  cualquier fondo. Podés sacar la imagen con el checkbox "Quitar la imagen de fondo actual" — sin imagen, el
  bot vuelve a mandar el mensaje como texto plano.
- **Tipografía de la tarjeta**: elegí entre 5 fuentes arcade (Press Start 2P, VT323, Silkscreen, Bungee,
  Monoton). Debajo del selector hay una **vista previa en vivo** que se actualiza sola con tu propio avatar
  al cambiar la fuente o editar el mensaje.

### 👋 Despedida

Igual que la bienvenida pero sin tarjeta de imagen: checkbox para activarla, canal, y mensaje con los mismos
placeholders.

### 🎭 Rol automático

Elegí un rol del desplegable (se carga en vivo desde Discord) para asignarlo automáticamente a cada miembro
que entra. Si no aparece o falla, revisá que el rol del bot esté por encima del elegido en **Configuración del
servidor → Roles**.

### 🔊 Salas de voz temporales ("Crear Sala")

1. En la sección **Salas de voz temporales**, elegí un canal de voz existente del desplegable y un nombre
   para las salas que genere (usá `{n}` donde querés que aparezca el número, ej. `Sala {n}`).
2. Guardá con **Agregar**. Ese canal queda marcado como disparador.
3. Cuando alguien se conecte a ese canal, el bot le crea una sala de voz nueva en la misma categoría (con el
   nombre elegido y el número más bajo disponible), lo mueve adentro, y la borra sola apenas queda vacía.
4. Podés configurar **varios** canales "Crear Sala" en el mismo servidor, cada uno con su propia plantilla de
   nombre. Para sacar uno, usá **Eliminar** en la tabla.

## Comandos del bot (slash commands)

| Comando | Qué hace |
| --- | --- |
| `/ping` | Muestra la latencia de la API y del bot. |
| `/info` | Cantidad de servidores donde está el bot y latencia actual. |

## Páginas públicas

- `/legal/terms` y `/legal/privacy`: Términos de Servicio y Política de Privacidad, enlazadas desde el pie de
  página del panel.
- Errores de acceso (401/403/404) se muestran con una página propia en vez de un JSON crudo.
