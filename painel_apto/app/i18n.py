"""Traduções do painel do hóspede (PT, EN, ES)."""

LANGS = ("pt", "en", "es")
DEFAULT = "pt"

STRINGS = {
    "pt": {
        "hello": "Olá",
        "confirm_msg": "Confirme com os <strong>4 últimos dígitos do celular</strong> informado na reserva.",
        "enter": "Entrar",
        "expired_res": "Esta reserva não está mais ativa. Fale com o anfitrião se precisar de acesso.",
        "expired_access": "Seu acesso expirou. Se precisar consultar algo, fale com o anfitrião.",
        "use_link": "Para acessar, use o link exclusivo da sua reserva enviado pelo anfitrião.",
        "wrong_digits": "Dígitos incorretos. Verifique os 4 últimos números do celular informado na reserva.",
        "too_many": "Muitas tentativas. Aguarde 15 minutos e tente novamente.",
        "apartment": "Apartamento",
        "nav_panel": "Painel", "nav_energy": "Consumo",
        "nav_autom": "Automações", "nav_exit": "Sair",
        "access_until": "Acesso disponível até",
        "g_guest": "Hóspede", "g_checkin": "Check-in", "g_checkout": "Check-out",
        "g_nights": "noites",
        "kwh_cycle": "KWH NO CICLO", "since": "Desde", "cycle_day": "Dia do ciclo",
        "tariff": "Tarifa",
        "energy_invoice": "Fatura de energia", "pay_pix": "Pagar com PIX",
        "other_period": "Consultar outro período",
        "from": "De", "to": "Até", "consult": "Consultar",
        "invoice_history": "Histórico de faturas",
        "st_aberta": "aberta", "st_paga": "paga", "st_cancelada": "cancelada",
        "no_autom": "Nenhuma automação liberada.",
        "not_found": "não encontrada",
        "autom_error": "Erro ao consultar automações",
        "energy_error": "Não foi possível ler o consumo agora",
        "back": "Voltar",
        "scan_qr": "Escaneie com o app do seu banco ou use o copia e cola:",
        "copy_pix": "Copiar código PIX", "copied": "Copiado ✓",
        "after_payment": "Após o pagamento, o anfitrião confirma no extrato e marca a fatura como paga.",
        "pix_missing": "Chave PIX ainda não configurada pelo anfitrião.",
        "js_choose": "Escolha as duas datas.", "js_query": "Consultando...",
        "js_error": "Erro na consulta.", "js_toggle_error": "Não foi possível alterar a automação.",
    },
    "en": {
        "hello": "Hi",
        "confirm_msg": "Confirm with the <strong>last 4 digits of the phone number</strong> on the reservation.",
        "enter": "Sign in",
        "expired_res": "This reservation is no longer active. Contact the host if you need access.",
        "expired_access": "Your access has expired. Contact the host if you need anything.",
        "use_link": "To sign in, use the exclusive reservation link sent by your host.",
        "wrong_digits": "Wrong digits. Check the last 4 digits of the phone number on the reservation.",
        "too_many": "Too many attempts. Wait 15 minutes and try again.",
        "apartment": "Apartment",
        "nav_panel": "Home", "nav_energy": "Usage",
        "nav_autom": "Automations", "nav_exit": "Sign out",
        "access_until": "Access available until",
        "g_guest": "Guest", "g_checkin": "Check-in", "g_checkout": "Check-out",
        "g_nights": "nights",
        "kwh_cycle": "KWH THIS CYCLE", "since": "Since", "cycle_day": "Cycle day",
        "tariff": "Rate",
        "energy_invoice": "Energy bill", "pay_pix": "Pay with PIX",
        "other_period": "Check another period",
        "from": "From", "to": "To", "consult": "Check",
        "invoice_history": "Bill history",
        "st_aberta": "open", "st_paga": "paid", "st_cancelada": "canceled",
        "no_autom": "No automations available.",
        "not_found": "not found",
        "autom_error": "Error loading automations",
        "energy_error": "Couldn't read energy usage right now",
        "back": "Back",
        "scan_qr": "Scan with your bank app or use copy & paste:",
        "copy_pix": "Copy PIX code", "copied": "Copied ✓",
        "after_payment": "After payment, the host confirms it on their statement and marks the bill as paid.",
        "pix_missing": "PIX key not configured by the host yet.",
        "js_choose": "Pick both dates.", "js_query": "Loading...",
        "js_error": "Query failed.", "js_toggle_error": "Couldn't toggle the automation.",
    },
    "es": {
        "hello": "Hola",
        "confirm_msg": "Confirma con los <strong>últimos 4 dígitos del móvil</strong> informado en la reserva.",
        "enter": "Entrar",
        "expired_res": "Esta reserva ya no está activa. Habla con el anfitrión si necesitas acceso.",
        "expired_access": "Tu acceso ha caducado. Habla con el anfitrión si necesitas algo.",
        "use_link": "Para acceder, usa el enlace exclusivo de tu reserva enviado por el anfitrión.",
        "wrong_digits": "Dígitos incorrectos. Verifica los últimos 4 números del móvil informado en la reserva.",
        "too_many": "Demasiados intentos. Espera 15 minutos e inténtalo de nuevo.",
        "apartment": "Apartamento",
        "nav_panel": "Panel", "nav_energy": "Consumo",
        "nav_autom": "Automatizaciones", "nav_exit": "Salir",
        "access_until": "Acceso disponible hasta",
        "g_guest": "Huésped", "g_checkin": "Check-in", "g_checkout": "Check-out",
        "g_nights": "noches",
        "kwh_cycle": "KWH EN EL CICLO", "since": "Desde", "cycle_day": "Día del ciclo",
        "tariff": "Tarifa",
        "energy_invoice": "Factura de energía", "pay_pix": "Pagar con PIX",
        "other_period": "Consultar otro período",
        "from": "De", "to": "Hasta", "consult": "Consultar",
        "invoice_history": "Historial de facturas",
        "st_aberta": "abierta", "st_paga": "pagada", "st_cancelada": "cancelada",
        "no_autom": "Ninguna automatización disponible.",
        "not_found": "no encontrada",
        "autom_error": "Error al consultar automatizaciones",
        "energy_error": "No fue posible leer el consumo ahora",
        "back": "Volver",
        "scan_qr": "Escanea con la app de tu banco o usa copiar y pegar:",
        "copy_pix": "Copiar código PIX", "copied": "Copiado ✓",
        "after_payment": "Tras el pago, el anfitrión lo confirma en su extracto y marca la factura como pagada.",
        "pix_missing": "El anfitrión aún no configuró la clave PIX.",
        "js_choose": "Elige las dos fechas.", "js_query": "Consultando...",
        "js_error": "Error en la consulta.", "js_toggle_error": "No fue posible cambiar la automatización.",
    },
}


def detect_language(request) -> str:
    """Idioma: query string ?lang= > cookie > padrão (pt)."""
    from_query = request.query_params.get("lang")
    if from_query in LANGS:
        return from_query
    from_cookie = request.cookies.get("lang")
    return from_cookie if from_cookie in LANGS else DEFAULT


def get_texts(language: str) -> dict:
    """Dicionário de textos traduzidos do idioma (usado como `t` nos templates)."""
    return STRINGS.get(language, STRINGS[DEFAULT])
