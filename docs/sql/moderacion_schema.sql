
-- Palabras prohibidas por grupo/bot
CREATE TABLE IF NOT EXISTS palabras_prohibidas (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bot_id BIGINT UNSIGNED NOT NULL,
    grupo_id VARCHAR(100) NOT NULL,
    palabra VARCHAR(120) NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bot_id) REFERENCES bots(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Usuarios sancionados (mute, ban, expulsión)
CREATE TABLE IF NOT EXISTS usuarios_sancionados (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bot_id BIGINT UNSIGNED NOT NULL,
    grupo_id VARCHAR(100) NOT NULL,
    usuario_id VARCHAR(120) NOT NULL,
    sancion ENUM('bloqueado','muteado','expulsado') NOT NULL,
    hasta DATETIME,
    motivo TEXT,
    fecha_sancion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sancionado_por VARCHAR(120), -- admin que aplicó la sanción
    FOREIGN KEY (bot_id) REFERENCES bots(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Configuración de moderación por grupo/bot
CREATE TABLE IF NOT EXISTS configuracion_moderacion (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bot_id BIGINT UNSIGNED NOT NULL,
    grupo_id VARCHAR(100) NOT NULL,
    advertencias_max INT DEFAULT 3,
    autoexpulsion BOOLEAN DEFAULT TRUE,
    moderacion_activa BOOLEAN DEFAULT TRUE,
    mute_duracion INT DEFAULT 900, -- segundos
    flood_max INT DEFAULT 10, -- mensajes por minuto
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (bot_id) REFERENCES bots(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Auditoría de acciones de moderación
CREATE TABLE IF NOT EXISTS auditoria_moderacion (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bot_id BIGINT UNSIGNED NOT NULL,
    grupo_id VARCHAR(100) NOT NULL,
    usuario_id VARCHAR(120) NOT NULL,
    accion VARCHAR(50) NOT NULL, -- warn, mute, ban, kick, delete, etc.
    motivo TEXT,
    ejecutado_por VARCHAR(120), -- admin que ejecutó la acción
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bot_id) REFERENCES bots(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Whitelist de usuarios exentos de moderación
CREATE TABLE IF NOT EXISTS whitelist_moderacion (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    bot_id BIGINT UNSIGNED NOT NULL,
    grupo_id VARCHAR(100) NOT NULL,
    usuario_id VARCHAR(120) NOT NULL,
    motivo TEXT,
    creado_por VARCHAR(120),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bot_id) REFERENCES bots(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
