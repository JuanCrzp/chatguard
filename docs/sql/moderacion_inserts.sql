-- Ejemplos de inserción para moderación profesional

-- Insertar palabras prohibidas
INSERT INTO palabras_prohibidas (bot_id, grupo_id, palabra) VALUES
  (1, 'grupo_general', 'spam'),
  (1, 'grupo_general', 'oferta'),
  (1, 'grupo_general', 'prohibido'),
  (2, 'grupo_ventas', 'estafa');

-- Insertar configuración de moderación por grupo
INSERT INTO configuracion_moderacion (bot_id, grupo_id, advertencias_max, autoexpulsion, moderacion_activa, mute_duracion, flood_max)
VALUES
  (1, 'grupo_general', 3, TRUE, TRUE, 900, 10),
  (2, 'grupo_ventas', 2, TRUE, TRUE, 600, 5);

-- Insertar usuario sancionado
INSERT INTO usuarios_sancionados (bot_id, grupo_id, usuario_id, sancion, hasta, motivo, sancionado_por)
VALUES
  (1, 'grupo_general', 'user123', 'muteado', DATE_ADD(NOW(), INTERVAL 15 MINUTE), 'Spam reiterado', 'admin1'),
  (1, 'grupo_general', 'user456', 'bloqueado', NULL, 'Lenguaje ofensivo', 'admin2');

-- Insertar acción de auditoría
INSERT INTO auditoria_moderacion (bot_id, grupo_id, usuario_id, accion, motivo, ejecutado_por)
VALUES
  (1, 'grupo_general', 'user123', 'mute', 'Spam reiterado', 'admin1'),
  (1, 'grupo_general', 'user456', 'ban', 'Lenguaje ofensivo', 'admin2');

-- Insertar usuario en whitelist
INSERT INTO whitelist_moderacion (bot_id, grupo_id, usuario_id, motivo, creado_por)
VALUES
  (1, 'grupo_general', 'user789', 'Moderador oficial', 'admin1');
