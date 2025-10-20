
-- ===============================
-- Ejemplos de inserción para moderación profesional (coherentes con el nuevo esquema)
-- ===============================

-- 1) Bots base
-- Crea los bots principales de la plataforma. Ajusta external_id y username según tu plataforma real.
INSERT INTO bots (platform, external_id, name, username, token_hash)
VALUES
  ('telegram', '123456789', 'ChatGuard TG', 'chatguard_bot', NULL),
  ('discord', '987654321', 'ChatGuard Discord', 'ChatGuard', NULL);

-- 2) Configuración global por bot
-- Define los valores por defecto de moderación para cada bot (aplicados si no hay override por grupo).
INSERT INTO configuracion_global (bot_id, advertencias_max_default, autoexpulsion_default, moderacion_activa_default, mute_duracion_default, flood_max_default, language, timezone)
VALUES
  (1, 3, TRUE, TRUE, 900, 10, 'es', 'UTC'),
  (2, 3, TRUE, TRUE, 900, 10, 'es', 'UTC');

-- 3) Configuración de moderación por grupo
-- Permite personalizar la moderación para cada grupo/comunidad.
INSERT INTO configuracion_moderacion (bot_id, grupo_id, advertencias_max, autoexpulsion, moderacion_activa, mute_duracion, flood_max)
VALUES
  (1, 'grupo_general', 3, TRUE, TRUE, 900, 10),
  (1, 'grupo_soporte', 2, TRUE, TRUE, 600, 8),
  (2, 'guild_general', 3, TRUE, TRUE, 900, 10);

-- 4) Palabras prohibidas
-- Lista de palabras que activan sanción automática por grupo/bot.
INSERT INTO palabras_prohibidas (bot_id, grupo_id, palabra) VALUES
  (1, 'grupo_general', 'spam'),
  (1, 'grupo_general', 'oferta'),
  (1, 'grupo_general', 'prohibido'),
  (1, 'grupo_soporte', 'estafa'),
  (2, 'guild_general', 'scam');

-- 5) Roles de usuarios
-- Asigna roles administrativos y de moderación a usuarios en cada grupo.
INSERT INTO roles_usuarios (bot_id, grupo_id, usuario_id, rol, concedido_por)
VALUES
  (1, 'grupo_general', 'admin1', 'admin', 'owner1'),
  (1, 'grupo_general', 'mod1', 'moderador', 'admin1'),
  (1, 'grupo_soporte', 'agent1', 'moderador', 'admin1');

-- 6) Whitelist/Blacklist
-- Whitelist: usuarios exentos de moderación automática.
INSERT INTO whitelist_moderacion (bot_id, grupo_id, usuario_id, motivo, creado_por)
VALUES (1, 'grupo_general', 'vip1', 'Colaborador', 'admin1');

-- Blacklist: usuarios bloqueados permanentemente.
INSERT INTO blacklist_moderacion (bot_id, grupo_id, usuario_id, motivo, creado_por)
VALUES (1, 'grupo_general', 'troll1', 'Troll reincidente', 'admin1');

-- 7) Advertencias, sanciones y auditoría
-- Advertencias: historial de warnings antes de sanción.
INSERT INTO advertencias (bot_id, grupo_id, usuario_id, motivo, puntos, aplicada_por)
VALUES (1, 'grupo_general', 'user123', 'Primer aviso por spam', 1, 'mod1');

-- Sanciones: usuarios actualmente sancionados (mute, ban, etc).
INSERT INTO usuarios_sancionados (bot_id, grupo_id, usuario_id, sancion, hasta, motivo, sancionado_por)
VALUES (1, 'grupo_general', 'user123', 'muteado', DATE_ADD(NOW(), INTERVAL 15 MINUTE), 'Spam reiterado', 'mod1');

-- Auditoría: registro de acciones administrativas relevantes.
INSERT INTO auditoria_moderacion (bot_id, grupo_id, usuario_id, accion, motivo, ejecutado_por)
VALUES
  (1, 'grupo_general', 'user123', 'warn', 'Primer aviso por spam', 'mod1'),
  (1, 'grupo_general', 'user123', 'mute', 'Spam reiterado', 'mod1');
