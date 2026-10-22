import sys
import re
from playwright.sync_api import sync_playwright

URL = "https://shop.casperxo.com/events/zurueck-zuhause-2026-xoxo-zwei-naechte-in-voller-laenge-lokschuppen-samstag?tab=resale"
MIN_TICKETS = 2
EMPTY_TEXT = "Aktuell sind keine re:sale Tickets verfügbar."

def check_tickets(page):
    print("Prüfe Seite...")
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(3000)
    
    body_text = page.locator("body").inner_text()
    
    # 1. Hauptprüfung: Steht der "Keine Tickets"-Text noch auf der Seite?
    if EMPTY_TEXT.lower() in body_text.lower():
        return False, f"Status unverändert: '{EMPTY_TEXT}'"
    
    print(" -> 'Keine Tickets'-Text ist verschwunden! Prüfe Anzahl...")

    # 2. Prüfen, ob mindestens 2 einzelne Preise gelistet sind (z. B. "65,00 €")
    prices = re.findall(r'\d+[,\.]\d{2}\s*€', body_text)
    if len(prices) >= MIN_TICKETS:
        return True, f"{len(prices)} Ticket-Angebote/Preise im re:sale gefunden!"

    # 3. Prüfen, ob es ein Dropdown (<select>) gibt, in dem >= 2 wählbar ist
    selects = page.locator("select").all()
    for select in selects:
        if select.is_visible():
            options = select.locator("option").all_inner_texts()
            for opt in options:
                if re.search(rf'\b[{MIN_TICKETS}-9]\b', opt):
                    return True, f"Dropdown mit Auswahl für mind. {MIN_TICKETS} Tickets verfügbar!"

    # 4. Prüfen auf '+' Buttons
    plus_buttons = page.locator("button:has-text('+'), [aria-label*='plus' i], [aria-label*='erhöhen' i], [aria-label*='mehr' i]").all()
    visible_plus = [b for b in plus_buttons if b.is_visible() and b.is_enabled()]
    
    if len(visible_plus) >= MIN_TICKETS:
        return True, f"{len(visible_plus)} separate Ticket-Optionen im re:sale gefunden!"
    elif len(visible_plus) == 1:
        try:
            visible_plus[0].click(timeout=2000)
            page.wait_for_timeout(500)
            inputs = page.locator("input[type='number'], input[type='text']").all()
            for inp in inputs:
                if inp.is_visible() and inp.input_value() == str(MIN_TICKETS):
                    return True, f"Ticket-Zähler ließ sich erfolgreich auf {MIN_TICKETS} stellen!"
            return True, "re:sale ist aktiv und '+' Button konnte geklickt werden!"
        except Exception:
            pass

    # 5. Sicherheits-Fallback
    if "re:sale" in body_text.lower() or "resale" in body_text.lower():
        return True, "Der Text 'Keine re:sale Tickets' ist verschwunden! Schnell selbst prüfen!"

    return False, "Seite geladen, aber Status unklar."

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        available, reason = check_tickets(page)
        print(reason)
        browser.close()
        
        if available:
            print(f"\n[ALARM] TICKETS GEFUNDEN! Hier klicken: {URL}")
            # Lässt den Durchlauf auf GitHub absichtlich fehlschlagen -> löst sofort die E-Mail aus!
            sys.exit(1)

if __name__ == "__main__":
    main()
