from fastapi import APIRouter, Depends
from src.middleware.auth import get_current_user
from src.models.user import User
from src.utils.shared_state import user_sync_data
from src.utils.response import success_response

router = APIRouter(prefix="/sync", tags=["Sync"])

MOCK_SYNC_DATA = [
        # ── 1. Sistema ──────────────────────────────────────────────────
        {
            "id": "system",
            "name": "SYSTEM MONITOR",
            "color": "#64748B",
            "icon": "Desktop",
            "shortcuts": [
                {
                    "id": "SYS_CPU",
                    "label": "PROCESADOR",
                    "icon": "Cpu",
                    "size": "big",
                    "subtitle": "Intel Core i9 · 13th Gen",
                    "stats": [
                        {"label": "USO", "value": "42%"},
                        {"label": "TEMP", "value": "68°C"},
                        {"label": "NÚCLEOS", "value": "24 activos"},
                        {"label": "FREC", "value": "4.8 GHz"},
                    ],
                    "progressValue": 42,
                    "settingsGroups": [
                        {
                            "title": "Rendimiento",
                            "fields": [
                                {"type": "select", "key": "power_plan", "label": "Plan de energía", "value": "Equilibrado", "options": ["Ahorro", "Equilibrado", "Alto rendimiento", "Máximo"]},
                                {"type": "toggle", "key": "turbo_boost", "label": "Turbo Boost", "value": True},
                                {"type": "slider", "key": "temp_alert", "label": "Alerta de temp.", "value": 85, "min": 60, "max": 100, "unit": "°C"},
                            ],
                        },
                    ],
                },
                {
                    "id": "SYS_RAM",
                    "label": "MEMORIA RAM",
                    "icon": "Memory",
                    "size": "tall",
                    "detail": "DDR5 · 32 GB total",
                    "stats": [
                        {"label": "USADA", "value": "18.4 GB"},
                        {"label": "LIBRE", "value": "13.6 GB"},
                        {"label": "CACHÉ", "value": "4.2 GB"},
                    ],
                    "logs": [
                        "Chrome.exe       4.8 GB",
                        "node.exe          2.1 GB",
                        "Code.exe          1.6 GB",
                    ],
                    "settingsGroups": [
                        {
                            "title": "Gestor RAM",
                            "fields": [
                                {"type": "toggle", "key": "auto_flush", "label": "Liberación automática", "value": True},
                                {"type": "slider", "key": "flush_limit", "label": "Límite de uso", "value": 80, "min": 50, "max": 95, "unit": "%"},
                                {"type": "info", "key": "mem_clk", "label": "Frecuencia", "value": "5600 MT/s"}
                            ]
                        }
                    ]
                },
                {
                    "id": "SYS_DISK",
                    "label": "ALMACENAMIENTO",
                    "icon": "HardDrives",
                    "size": "wide",
                    "detail": "NVMe SSD · 2 TB",
                    "actionType": "slider",
                    "value": 74,
                    "min": 0,
                    "max": 100,
                    "unit": "%",
                    "settingsGroups": [
                        {
                            "title": "Disco Principal",
                            "fields": [
                                {"type": "toggle", "key": "trim", "label": "Soporte TRIM", "value": True},
                                {"type": "slider", "key": "reserve", "label": "Espacio de reserva", "value": 10, "min": 0, "max": 20, "unit": "%"}
                            ]
                        }
                    ]
                },
                {
                    "id": "SYS_NET",
                    "label": "RED",
                    "icon": "WifiHigh",
                    "size": "wide",
                    "detail": "Ethernet · 1 Gbps",
                    "actionType": "chips",
                    "value": "GIGABIT",
                    "options": ["WIFI", "ETHERNET", "GIGABIT", "VPN"],
                    "settingsGroups": [
                        {
                            "title": "Interfaces",
                            "fields": [
                                {"type": "select", "key": "pref", "label": "Red preferida", "value": "Auto", "options": ["Auto", "LAN", "WLAN"]},
                                {"type": "toggle", "key": "vpn_kill", "label": "Killswitch VPN", "value": False},
                                {"type": "toggle", "key": "metered", "label": "Conexión medida", "value": False}
                            ]
                        }
                    ]
                },
                {
                    "id": "SYS_FAN",
                    "label": "VENTILADOR",
                    "icon": "Fan",
                    "size": "small",
                    "value": "2,400 rpm",
                    "actionType": "status",
                    "command": {"action": "set_fan_speed", "target": "system", "params": {"curve": "Standard"}},
                    "settingsGroups": [
                        {
                            "title": "Control BIOS",
                            "fields": [
                                {"type": "select", "key": "curve", "label": "Curva ventilación", "value": "Silent", "options": ["Silent", "Standard", "Turbo", "Full Speed"]},
                                {"type": "info", "key": "chassis", "label": "Ubicación", "value": "Chassis Fan 1"}
                            ]
                        }
                    ]
                },
                {
                    "id": "SYS_UPT",
                    "label": "UPTIME",
                    "icon": "Clock",
                    "size": "small",
                    "value": "3d 14h",
                    "actionType": "status",
                    "command": {"action": "lock_screen", "target": "system"},
                    "settingsGroups": [
                        {
                            "title": "Estado del Sistema",
                            "fields": [
                                {"type": "info", "key": "boot", "label": "Último arranque", "value": "12 de Abril, 08:32 AM"},
                                {"type": "toggle", "key": "fast_boot", "label": "Inicio Rápido", "value": True}
                            ]
                        }
                    ]
                },
            ],
        },
        # ── 2. Navegador (Chrome / Arc) ─────────────────────────────────
        {
            "id": "browser",
            "name": "NAVEGADOR WEB",
            "color": "#3B82F6",
            "icon": "Globe",
            "shortcuts": [
                {
                    "id": "BR_TABS",
                    "label": "PESTAÑAS ABIERTAS",
                    "icon": "Stack",
                    "size": "big",
                    "subtitle": "18 tabs · 3 grupos",
                    "stats": [
                        {"label": "ACTIVAS", "value": "18"},
                        {"label": "DURMIENDO", "value": "11"},
                        {"label": "GRUPOS", "value": "3"},
                        {"label": "RAM USADA", "value": "4.8 GB"},
                    ],
                    "progressValue": 60,
                    "settingsGroups": [
                        {
                            "title": "Rendimiento",
                            "fields": [
                                {"type": "toggle", "key": "tab_sleep", "label": "Suspender tabs inactivas", "value": True},
                                {"type": "slider", "key": "sleep_after", "label": "Suspender después de", "value": 5, "min": 1, "max": 60, "unit": "min"},
                                {"type": "toggle", "key": "preload", "label": "Precargar páginas", "value": False},
                            ],
                        },
                        {
                            "title": "Privacidad",
                            "fields": [
                                {"type": "toggle", "key": "tracking", "label": "Bloquear rastreadores", "value": True},
                                {"type": "select", "key": "dns", "label": "DNS seguro", "value": "Cloudflare", "options": ["Sistema", "Google", "Cloudflare", "Quad9"]},
                            ],
                        },
                    ],
                },
                {
                    "id": "BR_DL",
                    "label": "DESCARGAS",
                    "icon": "DownloadSimple",
                    "size": "tall",
                    "detail": "3 activas · 12.4 GB libres",
                    "stats": [
                        {"label": "ACTIVAS", "value": "3"},
                        {"label": "VELOCIDAD", "value": "48 MB/s"},
                        {"label": "COMPLETADAS", "value": "7 hoy"},
                    ],
                    "logs": [
                        "ubuntu-22.iso        87%",
                        "dataset_v2.zip       43%",
                        "figma-backup.fig     12%",
                    ],
                    "settingsGroups": [
                        {
                            "title": "Rutas",
                            "fields": [
                                {"type": "info", "key": "path", "label": "Guardar en", "value": "C:/Descargas/"},
                                {"type": "toggle", "key": "ask", "label": "Preguntar ubicación", "value": False}
                            ]
                        }
                    ]
                },
                {
                    "id": "BR_ZOOM",
                    "label": "ZOOM DE PÁGINA",
                    "icon": "MagnifyingGlass",
                    "size": "wide",
                    "detail": "Zoom actual de la pestaña activa",
                    "actionType": "chips",
                    "value": "100%",
                    "options": ["75%", "90%", "100%", "125%", "150%"],
                    "command": {"action": "zoom_browser", "target": "browser", "params": {"level": "100%"}},
                    "settingsGroups": [
                        {
                            "title": "Accesibilidad",
                            "fields": [
                                {"type": "toggle", "key": "high_contrast", "label": "Alto contraste web", "value": False},
                                {"type": "slider", "key": "font_size", "label": "Tamaño de fuente base", "value": 16, "min": 10, "max": 24, "unit": "px"}
                            ]
                        }
                    ]
                },
                {
                    "id": "BR_SHIELD",
                    "label": "AD BLOCKER",
                    "icon": "ShieldCheck",
                    "size": "small",
                    "value": True,
                    "actionType": "toggle",
                    "command": {"action": "toggle_adblocker", "target": "browser"},
                    "settingsGroups": [
                        {
                            "title": "Filtros",
                            "fields": [
                                {"type": "toggle", "key": "cosmetic", "label": "Filtros cosméticos", "value": True},
                                {"type": "toggle", "key": "social", "label": "Bloquear widgets sociales", "value": True},
                                {"type": "select", "key": "lists", "label": "Listas activas", "value": "EasyList", "options": ["EasyList", "UBlock", "Fanboy"]}
                            ]
                        }
                    ]
                },
                {
                    "id": "BR_BM",
                    "label": "MARCADORES",
                    "icon": "BookmarkSimple",
                    "size": "small",
                    "value": "324",
                    "actionType": "status",
                    "settingsGroups": [
                        {
                            "title": "Sincronización",
                            "fields": [
                                {"type": "info", "key": "sync", "label": "Cuenta", "value": "user@cloud.com"},
                                {"type": "toggle", "key": "sync_pass", "label": "Sincronizar contraseñas", "value": True}
                            ]
                        }
                    ]
                },
            ],
        },
        # ── 3. Word (procesador de texto) ───────────────────────────────
        {
            "id": "word",
            "name": "WORD PROCESSOR",
            "color": "#2563EB",
            "icon": "FileDoc",
            "shortcuts": [
                {
                    "id": "WD_DOC",
                    "label": "DOCUMENTO ACTIVO",
                    "icon": "FileDoc",
                    "size": "big",
                    "subtitle": "Informe Q3 2025.docx",
                    "stats": [
                        {"label": "PALABRAS", "value": "8,432"},
                        {"label": "PÁGINAS", "value": "24"},
                        {"label": "GUARDADO", "value": "Hace 2 min"},
                        {"label": "IDIOMA", "value": "ES-MX"},
                    ],
                    "progressValue": 0,
                    "settingsGroups": [
                        {
                            "title": "Autoguardado",
                            "fields": [
                                {"type": "toggle", "key": "autosave", "label": "Autoguardado", "value": True},
                                {"type": "slider", "key": "save_every", "label": "Guardar cada", "value": 2, "min": 1, "max": 30, "unit": "min"},
                                {"type": "select", "key": "format", "label": "Formato por defecto", "value": ".docx", "options": [".docx", ".odt", ".pdf", ".txt"]},
                            ],
                        },
                        {
                            "title": "Revisión",
                            "fields": [
                                {"type": "toggle", "key": "spellcheck", "label": "Corrección ortográfica", "value": True},
                                {"type": "toggle", "key": "track", "label": "Control de cambios", "value": False},
                            ],
                        },
                    ],
                },
                {
                    "id": "WD_RECENT",
                    "label": "RECIENTES",
                    "icon": "Clock",
                    "size": "tall",
                    "detail": "5 documentos recientes",
                    "stats": [
                        {"label": "HOY", "value": "2 docs"},
                        {"label": "SEMANA", "value": "9 docs"},
                        {"label": "TOTAL", "value": "148 docs"},
                    ],
                    "logs": [
                        "Informe Q3 2025.docx",
                        "Contrato NDA v2.docx",
                        "Presentación cliente.docx",
                    ],
                    "settingsGroups": [
                        {
                            "title": "Historial",
                            "fields": [
                                {"type": "toggle", "key": "keep_history", "label": "Mantener historial", "value": True},
                                {"type": "slider", "key": "max_docs", "label": "Límite en lista", "value": 15, "min": 5, "max": 50}
                            ]
                        }
                    ]
                },
                {
                    "id": "WD_PRINT",
                    "label": "IMPRESIÓN",
                    "icon": "Printer",
                    "size": "wide",
                    "detail": "HP LaserJet Pro · Lista",
                    "actionType": "chips",
                    "value": "COLOR",
                    "options": ["BORRADOR", "NORMAL", "ALTA CAL.", "COLOR"],
                    "settingsGroups": [
                        {
                            "title": "Gestor de Tinta",
                            "fields": [
                                {"type": "info", "key": "ink", "label": "Niveles", "value": "Cyan 80% / Black 30%"},
                                {"type": "toggle", "key": "eco_print", "label": "Modo Ecológico", "value": False}
                            ]
                        }
                    ]
                },
                {
                    "id": "WD_CLOUD",
                    "label": "ONEDRIVE SYNC",
                    "icon": "CloudArrowUp",
                    "size": "small",
                    "value": True,
                    "actionType": "toggle",
                    "settingsGroups": [
                        {
                            "title": "Nube",
                            "fields": [
                                {"type": "toggle", "key": "wifi_only", "label": "Solo sincronizar WiFi", "value": True},
                                {"type": "info", "key": "quota", "label": "Almacenamiento", "value": "750 GB Libres"}
                            ]
                        }
                    ]
                },
                {
                    "id": "WD_LANG",
                    "label": "IDIOMA",
                    "icon": "Globe",
                    "size": "small",
                    "value": "ES-MX",
                    "actionType": "status",
                    "settingsGroups": [
                        {
                            "title": "Traducción",
                            "fields": [
                                {"type": "select", "key": "dict", "label": "Diccionario Primario", "value": "Español (México)", "options": ["Español (México)", "English (US)"]},
                                {"type": "toggle", "key": "auto_lang", "label": "Detectar idioma escrito", "value": True}
                            ]
                        }
                    ]
                },
            ],
        },
        # ── 4. Excel (hoja de cálculo) ──────────────────────────────────
        {
            "id": "excel",
            "name": "SPREADSHEET",
            "color": "#16A34A",
            "icon": "Table",
            "shortcuts": [
                {
                    "id": "XL_SHEET",
                    "label": "LIBRO ACTIVO",
                    "icon": "Table",
                    "size": "big",
                    "subtitle": "Ventas_2025.xlsx · 6 hojas",
                    "stats": [
                        {"label": "FILAS", "value": "48,320"},
                        {"label": "FÓRMULAS", "value": "1,240"},
                        {"label": "HOJAS", "value": "6"},
                        {"label": "TAMAÑO", "value": "14.2 MB"},
                    ],
                    "progressValue": 0,
                    "settingsGroups": [
                        {
                            "title": "Cálculo",
                            "fields": [
                                {"type": "select", "key": "calc_mode", "label": "Modo de cálculo", "value": "Automático", "options": ["Automático", "Manual", "Excepto tablas"]},
                                {"type": "toggle", "key": "iter_calc", "label": "Cálculo iterativo", "value": False},
                                {"type": "slider", "key": "max_iter", "label": "Máx. iteraciones", "value": 100, "min": 1, "max": 1000},
                            ],
                        },
                        {
                            "title": "Visualización",
                            "fields": [
                                {"type": "toggle", "key": "gridlines", "label": "Líneas de cuadrícula", "value": True},
                                {"type": "toggle", "key": "formula_bar", "label": "Barra de fórmulas", "value": True},
                            ],
                        },
                    ],
                },
                {
                    "id": "XL_ERRORS",
                    "label": "ERRORES",
                    "icon": "Activity",
                    "size": "tall",
                    "detail": "3 errores detectados",
                    "stats": [
                        {"label": "#REF!", "value": "1"},
                        {"label": "#DIV/0!", "value": "2"},
                        {"label": "#N/A", "value": "0"},
                    ],
                    "logs": [
                        "B24: #DIV/0! → Total ventas",
                        "F102: #DIV/0! → Margen neto",
                        "K7: #REF! → Hoja eliminada",
                    ],
                    "settingsGroups": [
                        {
                            "title": "Depuración",
                            "fields": [
                                {"type": "toggle", "key": "highlight_err", "label": "Resaltar errores", "value": True},
                                {"type": "select", "key": "err_color", "label": "Color de error", "value": "Rojo", "options": ["Rojo", "Amarillo", "Rosa"]}
                            ]
                        }
                    ]
                },
                {
                    "id": "XL_ZOOM",
                    "label": "ZOOM",
                    "icon": "MagnifyingGlass",
                    "size": "wide",
                    "detail": "Nivel de zoom de la hoja activa",
                    "actionType": "chips",
                    "value": "100%",
                    "options": ["75%", "100%", "125%", "150%", "200%"],
                    "settingsGroups": [
                        {
                            "title": "Presentación",
                            "fields": [
                                {"type": "select", "key": "zoom_mode", "label": "Ajuste inicial", "value": "100%", "options": ["100%", "Ajustar ancho", "Ajustar selección"]},
                            ]
                        }
                    ]
                },
                {
                    "id": "XL_CLOUD",
                    "label": "ONEDRIVE SYNC",
                    "icon": "CloudArrowUp",
                    "size": "small",
                    "value": True,
                    "actionType": "toggle",
                    "settingsGroups": [
                        {
                            "title": "Co-Autoria",
                            "fields": [
                                {"type": "toggle", "key": "live_edit", "label": "Mostrar cursores live", "value": True},
                                {"type": "info", "key": "co_auth", "label": "Participantes en línea", "value": "2 personas"}
                            ]
                        }
                    ]
                },
                {
                    "id": "XL_REC",
                    "label": "MACRO REC.",
                    "icon": "ArrowClockwise",
                    "size": "small",
                    "value": False,
                    "actionType": "toggle",
                    "settingsGroups": [
                        {
                            "title": "Seguridad",
                            "fields": [
                                {"type": "toggle", "key": "macro_sec", "label": "Deshabilitar Macros sin firma", "value": True},
                            ]
                        }
                    ]
                },
            ],
        },
        # ── 5. Spotify ──────────────────────────────────────────────────
        {
            "id": "spotify",
            "name": "SPOTIFY",
            "color": "#1DB954",
            "icon": "MusicNotes",
            "shortcuts": [
                {
                    "id": "MED_NOW",
                    "label": "NOW PLAYING",
                    "icon": "MusicNotes",
                    "size": "big",
                    "subtitle": "Sin reproducción activa",
                    "stats": [
                        {"label": "PISTA",   "value": "—"},
                        {"label": "ARTISTA", "value": "—"},
                        {"label": "ÁLBUM",   "value": "—"},
                        {"label": "CALIDAD", "value": "—"},
                    ],
                    "progressValue": 0,
                    "progressLabel": ["0:00", "0:00"],
                    "command": {"action": "media_play"},
                },
                {
                    "id": "SP_QUEUE",
                    "label": "EN COLA",
                    "icon": "Stack",
                    "size": "tall",
                    "detail": "12 canciones · 48 min",
                    "stats": [
                        {"label": "EN COLA", "value": "12"},
                        {"label": "DURACIÓN", "value": "48 min"},
                        {"label": "PLAYLIST", "value": "Indie Focus"},
                    ],
                    "logs": [
                        "New Person, Same Old Mistakes",
                        "Eventually",
                        "Yes I'm Changing",
                    ],
                    "settingsGroups": [
                        {
                            "title": "Cola de reproducción",
                            "fields": [
                                {"type": "toggle", "key": "auto_dj", "label": "Autoplay cuando termine", "value": True},
                                {"type": "toggle", "key": "dj_ai", "label": "Modo DJ AI", "value": False}
                            ]
                        }
                    ]
                },
                {
                    "id": "SP_VOL",
                    "label": "VOLUMEN",
                    "icon": "SpeakerHigh",
                    "size": "wide",
                    "detail": "Salida: Auriculares Sony",
                    "actionType": "slider",
                    "value": 72,
                    "min": 0,
                    "max": 100,
                    "unit": "%",
                    "command": {"action": "set_volume", "target": "spotify", "params": {"value": 72}},
                    "settingsGroups": [
                        {
                            "title": "Mezclador",
                            "fields": [
                                {"type": "toggle", "key": "eqActive", "label": "Ecualizador paramétrico", "value": True},
                                {"type": "slider", "key": "bass_boost", "label": "Bass Boost", "value": 40, "min": 0, "max": 100, "unit": "%"}
                            ]
                        }
                    ]
                },
                {
                    "id": "SP_SHUFFLE",
                    "label": "ALEATORIO",
                    "icon": "ArrowClockwise",
                    "size": "small",
                    "value": True,
                    "actionType": "toggle",
                    "command": {"action": "media_shuffle", "target": "spotify"},
                    "settingsGroups": [
                        {
                            "title": "Algoritmo",
                            "fields": [
                                {"type": "select", "key": "shuffle_rng", "label": "Modo de mezcla", "value": "Inteligente", "options": ["Puro (True RNG)", "Inteligente"]}
                            ]
                        }
                    ]
                },
                {
                    "id": "SP_PODCAST",
                    "label": "PODCASTS",
                    "icon": "VideoCamera",
                    "size": "small",
                    "value": "3 unread",
                    "actionType": "status",
                    "settingsGroups": [
                        {
                            "title": "Suscripciones",
                            "fields": [
                                {"type": "toggle", "key": "pod_down", "label": "Descargar nuevos eps. en WiFi", "value": True},
                                {"type": "slider", "key": "pod_speed", "label": "Velocidad base", "value": 1.2, "min": 0.5, "max": 3, "unit": "x"}
                            ]
                        }
                    ]
                },
                {
                    "id": "MED_PREV",
                    "label": "ANTERIOR",
                    "icon": "SkipBack",
                    "size": "small",
                    "actionType": "status",
                    "value": "⏮",
                    "command": {"action": "media_prev"},
                },
                {
                    "id": "MED_PLAY",
                    "label": "PLAY / PAUSE",
                    "icon": "Play",
                    "size": "small",
                    "actionType": "toggle",
                    "value": False,
                    "command": {"action": "media_play"},
                },
                {
                    "id": "MED_NEXT",
                    "label": "SIGUIENTE",
                    "icon": "SkipForward",
                    "size": "small",
                    "actionType": "status",
                    "value": "⏭",
                    "command": {"action": "media_next"},
                },
                {
                    "id": "MED_STOP",
                    "label": "DETENER",
                    "icon": "Stop",
                    "size": "small",
                    "actionType": "status",
                    "value": "⏹",
                    "command": {"action": "media_stop"},
                },
                {
                    "id": "MED_MUTE",
                    "label": "SILENCIAR",
                    "icon": "SpeakerSlash",
                    "size": "small",
                    "actionType": "toggle",
                    "value": False,
                    "command": {"action": "volume_mute"},
                },
                {
                    "id": "MED_VOL",
                    "label": "VOL. SISTEMA",
                    "icon": "SpeakerHigh",
                    "size": "wide",
                    "detail": "Volumen del sistema",
                    "actionType": "slider",
                    "value": 70,
                    "min": 0,
                    "max": 100,
                    "unit": "%",
                    "command": {"action": "set_volume", "params": {"value": 70}},
                },
            ],
        },
        # ── 6. Explorador de archivos ───────────────────────────────────
        {
            "id": "explorer",
            "name": "FILE EXPLORER",
            "color": "#F59E0B",
            "icon": "Folder",
            "shortcuts": [
                {
                    "id": "EX_DISK",
                    "label": "DISCO PRINCIPAL",
                    "icon": "HardDrives",
                    "size": "big",
                    "subtitle": "SSD NVMe · Windows (C:)",
                    "stats": [
                        {"label": "TOTAL", "value": "2 TB"},
                        {"label": "USADO", "value": "1.48 TB"},
                        {"label": "LIBRE", "value": "520 GB"},
                        {"label": "TIPO", "value": "NVMe Gen4"},
                    ],
                    "progressValue": 74,
                    "settingsGroups": [
                        {
                            "title": "Limpieza",
                            "fields": [
                                {"type": "toggle", "key": "recycle_alert", "label": "Alerta papelera llena", "value": True},
                                {"type": "slider", "key": "recycle_limit", "label": "Tamaño máx. papelera", "value": 10, "min": 1, "max": 50, "unit": "GB"},
                                {"type": "toggle", "key": "compress_old", "label": "Comprimir archivos viejos", "value": False},
                            ],
                        },
                        {
                            "title": "Vista",
                            "fields": [
                                {"type": "select", "key": "view_mode", "label": "Modo de vista", "value": "Detalles", "options": ["Íconos", "Lista", "Detalles", "Mosaico"]},
                                {"type": "toggle", "key": "hidden_files", "label": "Mostrar archivos ocultos", "value": False},
                            ],
                        },
                    ],
                },
                {
                    "id": "EX_RECENT",
                    "label": "ARCHIVOS RECIENTES",
                    "icon": "Clock",
                    "size": "tall",
                    "detail": "Últimos 24 h · 18 archivos",
                    "stats": [
                        {"label": "DOCS", "value": "8"},
                        {"label": "IMÁGENES", "value": "6"},
                        {"label": "OTROS", "value": "4"},
                    ],
                    "logs": [
                        "Ventas_2025.xlsx       hace 5 min",
                        "logo_final_v3.png      hace 18 min",
                        "deploy_notes.md        hace 1 h",
                    ],
                    "settingsGroups": [
                        {
                            "title": "Indización",
                            "fields": [
                                {"type": "toggle", "key": "windows_search", "label": "Búsqueda rápida indexada", "value": True},
                                {"type": "info", "key": "index_status", "label": "Archivos procesados", "value": "1,048,110 items"}
                            ]
                        }
                    ]
                },
                {
                    "id": "EX_ZIP",
                    "label": "COMPRIMIR",
                    "icon": "FileZip",
                    "size": "wide",
                    "detail": "Formato de compresión",
                    "actionType": "chips",
                    "value": "ZIP",
                    "options": ["ZIP", "7Z", "TAR.GZ", "RAR"],
                    "settingsGroups": [
                        {
                            "title": "Algoritmo",
                            "fields": [
                                {"type": "select", "key": "zip_dict", "label": "Nivel de compresión", "value": "Máxima", "options": ["Rápida", "Normal", "Máxima", "Ultra"]},
                                {"type": "toggle", "key": "zip_del", "label": "Borrar original al terminar", "value": False}
                            ]
                        }
                    ]
                },
                {
                    "id": "EX_CLOUD",
                    "label": "ONEDRIVE",
                    "icon": "CloudArrowUp",
                    "size": "small",
                    "value": "SYNC",
                    "actionType": "status",
                    "settingsGroups": [
                        {
                            "title": "Nube Activa",
                            "fields": [
                                {"type": "toggle", "key": "onedrive_boot", "label": "Arrancar con Windows", "value": True},
                                {"type": "info", "key": "one_quota", "label": "Plan actual", "value": "Microsoft 365 1TB"}
                            ]
                        }
                    ]
                },
                {
                    "id": "EX_HIDDEN",
                    "label": "ARCHIVOS OCULTOS",
                    "icon": "LockKey",
                    "size": "small",
                    "value": False,
                    "actionType": "toggle",
                    "settingsGroups": [
                        {
                            "title": "Privacidad",
                            "fields": [
                                {"type": "toggle", "key": "sys_hidden", "label": "Ocultar archivos del OS", "value": True},
                                {"type": "toggle", "key": "ext_hidden", "label": "Ocultar .extensiones", "value": False}
                            ]
                        }
                    ]
                },
            ],
        },
        # ── 7. X-Tools (Utilidades nuevas) ──────────────────────────────
        {
            "id": "xtools",
            "name": "X-TOOLS",
            "color": "#00F0FF",
            "icon": "Wrench",
            "shortcuts": [
                {
                    "id": "T_TRACKPAD",
                    "label": "TRACKPAD TÁCTIL",
                    "icon": "HandPointing",
                    "size": "big",
                    "subtitle": "Control remoto y gestos",
                    "stats": [
                        {"label": "ESTADO", "value": "Conectado"},
                        {"label": "LATENCIA", "value": "12ms"},
                        {"label": "GESTOS", "value": "D-Tap, Swipe"},
                        {"label": "MODO", "value": "Gamepad"},
                    ],
                    "progressValue": 100,
                    "command": {"action": "open_app", "target": "trackpad_mode"},
                    "settingsGroups": []
                },
                {
                    "id": "T_FILES",
                    "label": "GESTOR DE ARCHIVOS",
                    "icon": "Folder",
                    "size": "tall",
                    "detail": "Documentos",
                    "stats": [
                        {"label": "DISQUETE", "value": "Local"},
                    ],
                    "logs": [
                        "Soporta fotos.",
                        "Soporta Pdfs.",
                        "Puntajes listos."
                    ]
                },
                {
                    "id": "T_AUDIO",
                    "label": "LAB DE AUDIO",
                    "icon": "Microphone",
                    "size": "wide",
                    "value": "Mic Active",
                    "actionType": "chips",
                    "options": ["RECORD", "PLAY", "STOP"],
                    "command": {"action": "run_script", "target": "audio", "params": {"script": "toggle_mic"}}
                }
            ]
        },
    ]


@router.get("")
async def get_sync_data(user: User = Depends(get_current_user)):
    """Return synchronized dashboard categories and shortcuts."""
    user_id = str(user.id)

    live = user_sync_data.get(user_id)
    data = live if live else MOCK_SYNC_DATA

    return success_response(
        data=data,
        message="Live sync data" if live else "Mock sync data"
    )
