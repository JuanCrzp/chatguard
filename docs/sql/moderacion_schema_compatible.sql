-- ChatGuard Moderación - Esquema MySQL compatible (5.6+)
--
-- RECOMENDADO si tu servidor es MySQL 5.6 o si tienes problemas con columnas JSON.
-- Usa solo tipos estándar (TEXT, VARCHAR, ENUM, etc.), máxima compatibilidad.
-- Si tu MySQL es 5.7+ u 8.0, puedes usar el archivo moderacion_schema.sql para soporte JSON.
--
-- Incluye claves foráneas, índices, restricciones y estructura profesional lista para producción.
-- Sin columnas JSON; usa TEXT para metadata/contexto/extras.

SET NAMES utf8mb4;
SET sql_mode = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION';

START TRANSACTION;

CREATE TABLE IF NOT EXISTS bots (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    platform ENUM('telegram','discord','whatsapp','webchat','other') NOT NULL,
    external_id VARCHAR(190) NOT NULL,
    name VARCHAR(190) NOT NULL,
    username VARCHAR(190) NULL,
    token_hash CHAR(64) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_bots_platform_external (platform, external_id),
    UNIQUE KEY uq_bots_platform_username (platform, username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS configuracion_global (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bot_id BIGINT UNSIGNED NOT NULL,
    advertencias_max_default INT DEFAULT 3,
    autoexpulsion_default BOOLEAN DEFAULT TRUE,
    moderacion_activa_default BOOLEAN DEFAULT TRUE,
    mute_duracion_default INT DEFAULT 900,
    flood_max_default INT DEFAULT 10,
    language VARCHAR(10) DEFAULT 'es',
    timezone VARCHAR(64) DEFAULT 'UTC',
    extras TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_conf_global_bot FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    UNIQUE KEY uq_conf_global_bot (bot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS palabras_prohibidas (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bot_id BIGINT UNSIGNED NOT NULL,
    grupo_id VARCHAR(100) NOT NULL,
    palabra VARCHAR(120) NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pp_bot FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    UNIQUE KEY uq_pp_unique (bot_id, grupo_id, palabra),
    KEY idx_pp_lookup (bot_id, grupo_id, activa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS usuarios_sancionados (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bot_id BIGINT UNSIGNED NOT NULL,
    grupo_id VARCHAR(100) NOT NULL,
    usuario_id VARCHAR(120) NOT NULL,
    sancion ENUM('bloqueado','muteado','expulsado') NOT NULL,
    hasta DATETIME NULL,
    motivo TEXT,
    fecha_sancion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sancionado_por VARCHAR(120) NULL,
    CONSTRAINT fk_us_bot FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    KEY idx_us_usuario (bot_id, grupo_id, usuario_id),
    KEY idx_us_estado (sancion, hasta)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS blacklist_moderacion (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bot_id BIGINT UNSIGNED NOT NULL,
    grupo_id VARCHAR(100) NOT NULL,
    usuario_id VARCHAR(120) NOT NULL,
    motivo TEXT,
    creado_por VARCHAR(120) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bl_bot FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    UNIQUE KEY uq_blacklist (bot_id, grupo_id, usuario_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS whitelist_moderacion (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bot_id BIGINT UNSIGNED NOT NULL,
    grupo_id VARCHAR(100) NOT NULL,
    usuario_id VARCHAR(120) NOT NULL,
    motivo TEXT,
    creado_por VARCHAR(120) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_wl_bot FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    UNIQUE KEY uq_whitelist (bot_id, grupo_id, usuario_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS configuracion_moderacion (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bot_id BIGINT UNSIGNED NOT NULL,
    grupo_id VARCHAR(100) NOT NULL,
    advertencias_max INT DEFAULT 3,
    autoexpulsion BOOLEAN DEFAULT TRUE,
    moderacion_activa BOOLEAN DEFAULT TRUE,
    mute_duracion INT DEFAULT 900,
    flood_max INT DEFAULT 10,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_confm_bot FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    UNIQUE KEY uq_confm (bot_id, grupo_id),
    KEY idx_confm_lookup (bot_id, grupo_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS advertencias (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bot_id BIGINT UNSIGNED NOT NULL,
    grupo_id VARCHAR(100) NOT NULL,
    usuario_id VARCHAR(120) NOT NULL,
    motivo TEXT NULL,
    puntos INT NOT NULL DEFAULT 1,
    aplicada_por VARCHAR(120) NULL,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_adv_bot FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    KEY idx_adv_user (bot_id, grupo_id, usuario_id),
    KEY idx_adv_fecha (fecha)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS historial_mensajes (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bot_id BIGINT UNSIGNED NOT NULL,
    grupo_id VARCHAR(100) NOT NULL,
    usuario_id VARCHAR(120) NOT NULL,
    mensaje_id VARCHAR(190) NULL,
    tipo ENUM('texto','imagen','video','audio','documento','sistema') NOT NULL DEFAULT 'texto',
    texto TEXT NULL,
    metadata TEXT NULL,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_hm_bot FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    KEY idx_hm_lookup (bot_id, grupo_id, usuario_id, fecha),
    KEY idx_hm_tipo (tipo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS roles_usuarios (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bot_id BIGINT UNSIGNED NOT NULL,
    grupo_id VARCHAR(100) NOT NULL,
    usuario_id VARCHAR(120) NOT NULL,
    rol ENUM('owner','superadmin','admin','moderador','miembro') NOT NULL DEFAULT 'miembro',
    concedido_por VARCHAR(120) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_roles_bot FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    UNIQUE KEY uq_roles (bot_id, grupo_id, usuario_id, rol),
    KEY idx_roles_user (bot_id, grupo_id, usuario_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS logs_generales (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bot_id BIGINT UNSIGNED NULL,
    nivel ENUM('DEBUG','INFO','WARN','ERROR') NOT NULL DEFAULT 'INFO',
    origen VARCHAR(190) NULL,
    mensaje TEXT NULL,
    contexto TEXT NULL,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_logs_bot FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE SET NULL,
    KEY idx_logs_fecha (fecha),
    KEY idx_logs_nivel (nivel)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS auditoria_moderacion (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bot_id BIGINT UNSIGNED NOT NULL,
    grupo_id VARCHAR(100) NOT NULL,
    usuario_id VARCHAR(120) NOT NULL,
    accion VARCHAR(50) NOT NULL,
    motivo TEXT,
    ejecutado_por VARCHAR(120),
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_aud_bot FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    KEY idx_aud_user_fecha (bot_id, grupo_id, usuario_id, fecha),
    KEY idx_aud_accion (accion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

COMMIT;
