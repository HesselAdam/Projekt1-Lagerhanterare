'''
main.py: Detta är en lagerhanterare för tavlor

__author__  = "Adam Hessel"
__version__ = "1.0.0"
__email__   = "adam.hessel@elev.ga.ntig.se"
'''

import csv
import os
import locale
import sys
import shutil
import webbrowser
from urllib.parse import quote

# Enkla färger för snyggare terminaltext.
COLOR_RESET = "\033[0m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_DIM = "\033[90m"
COLOR_SELECTED = "\033[7m"

for stream in (sys.stdin, sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

def money_text(value):
    try:
        return locale.currency(value, grouping=True)
    except Exception:
        return f"{value:.2f} kr"

def shorten(text, max_length):
    # Kortar ner text och lägger till ...
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def read_products(filename):
    products = []
    if not os.path.exists(filename):
        return products

    with open(filename, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            id = int(row['id'])
            name = row['name']
            desc = row['desc']
            price = float(row['price'])
            quantity = int(row['quantity'])
            cost = float(row.get('cost', 0) or 0)
            product_link_name = (row.get('product_link_name') or "").strip().lstrip("/")
            
            products.append(
                {                   
                    "id": id,       
                    "name": name,
                    "desc": desc,
                    "price": price,
                    "quantity": quantity,
                    "cost": cost,
                    "product_link_name": product_link_name
                }
            )
    return products

# Save products to the CSV file.
def save_products(filename, products):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        fieldnames = ['id', 'name', 'desc', 'price', 'quantity', 'cost', 'product_link_name']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for product in products:
            writer.writerow({field: product.get(field, "") for field in fieldnames})

def read_key():
    # Read one key press without needing Enter (Windows only).
    import msvcrt
    key = msvcrt.getch()
    if key in (b"\x00", b"\xe0"):  # arrow/key prefix
        key += msvcrt.getch()
    return key.decode(encoding="latin-1", errors="ignore")

def is_up_arrow(raw_key):
    # True if key press was up arrow.
    return raw_key in ("\x1b[A", "\x1bOA", "\xe0H", "\x00H") or (raw_key.startswith("\x1b[") and raw_key.endswith("A"))

def is_down_arrow(raw_key):
    # True if key press was down arrow.
    return raw_key in ("\x1b[B", "\x1bOB", "\xe0P", "\x00P") or (raw_key.startswith("\x1b[") and raw_key.endswith("B"))

def prompt_float(prompt_text, allow_empty=False, default=None):
    """Prompt for a float, optionally allowing empty input to keep default."""
    while True:
        value = input(prompt_text).strip()
        if allow_empty and value == "":
            return default
        try:
            return float(value)
        except ValueError:
            print("Ogiltigt värde, ange ett numeriskt tal.")

def prompt_int(prompt_text, allow_empty=False, default=None):
    """Prompt for an int, optionally allowing empty input to keep default."""
    while True:
        value = input(prompt_text).strip()
        if allow_empty and value == "":
            return default
        try:
            return int(value)
        except ValueError:
            print("Ogiltigt värde, ange ett heltal.")

def open_product_link(product):
    """Open a product link based on the stored link end."""
    base_url = "https://frmd.se/products/"
    product_link_name = (product.get("product_link_name") or "").strip().lstrip("/")
    if not product_link_name:
        print("Produkten saknar produktlänk. Uppdatera den och försök igen.")
        return

    url = base_url + quote(product_link_name)
    print(f"Öppnar länk: {url}")
    webbrowser.open(url)

def show_menu(products, selected_product=None):
    # Visa vald produkt och enkla val.
    if not selected_product:
        return True

    while True:
        os.system('cls')
        term_width = shutil.get_terminal_size(fallback=(80, 24)).columns
        print(f"{COLOR_YELLOW}VISAR PRODUKT MED ID: {selected_product['id']}{COLOR_RESET}")
        print(COLOR_DIM + "-" * term_width + COLOR_RESET)
        print(f"    Namn:        {selected_product['name']}")
        print(f"    Beskrivning: {selected_product['desc']}")
        print(f"    Pris:        {money_text(selected_product['price'])}")
        print(f"    Kvantitet:   {selected_product['quantity']}")

        print()
        print(f"{COLOR_YELLOW}HANTERA PRODUKT{COLOR_RESET}")
        print(COLOR_DIM + "-" * 30 + COLOR_RESET)
        print(f"{COLOR_CYAN}[MELLANSLAG]{COLOR_RESET} Redigera produkt")
        print(f"{COLOR_CYAN}[D]{COLOR_RESET} Ta bort produkt")
        print(f"{COLOR_CYAN}[S]{COLOR_RESET} Kort statistik")
        print(f"{COLOR_CYAN}[O]{COLOR_RESET} Öppna produktlänk")
        print(f"{COLOR_CYAN}[ESC/ENTER]{COLOR_RESET} Gå tillbaka")

        raw = read_key()
        choice = raw.lower()

        if raw in ("", "\r", "\n") or raw == "\x1b":  # Enter eller Esc
            return True
        if raw == " ":
            change_product(products, "Ändra data för produkt", selected_product)
            continue
        if choice == "d":
            confirm = input("Ta bort produkten? (j/n): ").strip().lower()
            if confirm == "j":
                products.remove(selected_product)
                os.system('cls')
                return True
        if choice == "s":
            os.system('cls')
            short_stats(products)
            input("\nTryck Enter för att fortsätta...")
        if choice == "o":
            open_product_link(selected_product)
            input("\nTryck Enter för att fortsätta...")

def list_products(products):
    # Show products and let the user move with arrow keys.
    if not products:
        print("Inga produkter i lager. Tryck 'a' för att lägga till en ny eller 'q'/Enter för att fortsätta.")
    index = 0
    while True:
        term_width = shutil.get_terminal_size(fallback=(80, 24)).columns
        if products:
            os.system('cls')
            title = f"{COLOR_CYAN}Adamos Lagerr{COLOR_RESET}"
            commands = "[UPP/NED] Navigera  [ENTER] Visa  [A] Ny produkt  [D] Ta bort  [Q/ESC] Avsluta"
            print(f"{title}  {commands}"[:term_width])
            print(COLOR_DIM + "-" * term_width + COLOR_RESET)
            header = f"#  {'NAMN':<25}  {'BESKRIVNING':<45}  {'PRIS':>10}  {'KVANTITET':>9}"
            print(header[:term_width])
            print(COLOR_DIM + "-" * term_width + COLOR_RESET)
            for i, product in enumerate(products):
                name = shorten(product['name'], 25).ljust(25)
                desc = shorten(product['desc'], 45).ljust(45)
                price = money_text(product['price']).rjust(10)
                qty = str(product['quantity']).rjust(9)
                line = f"{product['id']:>2}  {name}  {desc}  {price}  {qty}"
                line = line[:term_width].ljust(term_width)
                if i == index:
                    print(f"{COLOR_SELECTED}{line}{COLOR_RESET}")  # marker för vald rad
                else:
                    print(line)
            print(COLOR_DIM + "-" * term_width + COLOR_RESET)
        raw_key = read_key()
        key = raw_key.lower()
        if key in ("", "\r", "\n", "q") or raw_key == "\x1b":  # Enter, q eller Esc avslutar
            if key == "q" or raw_key == "\x1b":
                return None  # signal to exit program
            break
        if products and is_up_arrow(raw_key):
            index = (index - 1) % len(products)
        elif products and is_down_arrow(raw_key):
            index = (index + 1) % len(products)
        elif key == "a":
            add_product(products, "Lägg till produkt")
        elif key == "d" and products:
            prod = products[index]
            confirm = input(f"Ta bort '{prod['name']}'? (j/n): ").strip().lower()
            if confirm == "j":
                products.pop(index)
                if not products:
                    return None
                index = min(index, len(products) - 1)
    return products[index] if products else None

def numererad_lista(products, option):
    if option == "Numererad lista":
        for i, product in enumerate(products, 1):
            print(f"{product['id']}) -- {i}. {product['name']} - {money_text(product['price'])} - {product['quantity']} st")


def get_product_by_id(products, option, products_id):
    if option == "Sök produkt (id)":
        for product in products:
            if product["id"] == products_id:
                return print(f"Produkt: {product['name']} Beskrivning: {product['desc']} Pris: {product['price']} Antal i lager: {product['quantity']} st")
        print(f"Hittade ingen produkt med id {products_id}.")


def remove_product_by_id(products, option, products_id):
    if option == "Radera produkt":
        for product in products:
            if product["id"] == products_id:
                products.remove(product)
                return print(f"Produkten med id {products_id} har tagits bort.")
        print(f"Hittade ingen produkt med id {products_id}.")
        return None

def add_product(products, option):
    if option == "Lägg till produkt":
        print("Lägga till produkt:")
        print()
        
        new_id = max(product["id"] for product in products) + 1 if products else 1
        name = input("Ange produktens namn: ")
        desc = input("Ange produktens beskrivning: ")
        price = prompt_float("Ange produktens pris: ")
        quantity = prompt_int("Ange produktens kvantitet: ")
        cost = prompt_float("Ange produktens kostnad: ")
        product_link_name = input("Ange produktlänk (endast slutet, t.ex. 'are'): ").strip().lstrip("/")

        new_product = {
            "id":new_id,
            "name": name,
            "desc": desc,
            "price": price,
            "quantity": quantity,
            "cost": cost,
            "product_link_name": product_link_name
        }
        products.append(new_product)
        return print(f"Produkten {name} har lagts till med id {new_id}.")

def change_product(products, option, selected_product=None):
    if option != "Ändra data för produkt":
        return

    product = selected_product
    if not product:
        product_id = int(input("Vilken produkt vill du ändra data för? (ange id): "))
        for p in products:
            if p["id"] == product_id:
                product = p
                break
        if not product:
            print(f"Hittade ingen produkt med id {product_id}.")
            return

    print(f"Nuvarande namn för produkten är: {product['name']}")
    new_name = input("Ange det nya namnet för produkten: ")
    product['name'] = new_name if new_name else product['name']
    
    print(f"Nuvarande beskrivning för produkten är: {product['desc']}")
    new_desc = input("Ange den nya beskrivningen för produkten: ")
    product['desc'] = new_desc if new_desc else product['desc']
    
    print(f"Nuvarande pris för produkten är: {product['price']}")
    product['price'] = prompt_float("Ange det nya priset för produkten: ", allow_empty=True, default=product['price'])
    
    print(f"Nuvarande kvantitet för produkten är: {product['quantity']}")
    product['quantity'] = prompt_int("Ange den nya kvantiteten för produkten: ", allow_empty=True, default=product['quantity'])

    print(f"Nuvarande kostnad för produkten är: {product.get('cost', 0)}")
    product['cost'] = prompt_float("Ange den nya kostnaden för produkten: ", allow_empty=True, default=product.get('cost', 0))

    print(f"Nuvarande produktlänk är: {product.get('product_link_name', '') or '(saknas)'}")
    new_link = input("Ange den nya produktlänken (endast slutet, lämna tomt för att behålla): ").strip().lstrip("/")
    product['product_link_name'] = new_link if new_link else product.get('product_link_name', '')
    
    return print(f"Produkten med id {product['id']} har uppdaterats.")

def option_menu():
    options = ["Totalt antal", "Medelvärde", "Sök produkt (id)", "Numererad lista", "Lägg till produkt", "Radera produkt", "Ändra data för produkt"]
    print("Vilken statistik vill du veta?")
    for idx, option in enumerate(options, start=1):
        print(f"{idx}) {option}")

    choice = input("Välj nummer: ").strip()
    try:
        index = int(choice) - 1
        return options[index]
    except (ValueError, IndexError):
        print("Ogiltigt val, försöker med standardalternativet (Totalt antal).")
        return options[0]

def statistics(products, option):
    if option == "Totalt antal":
        total_quantity = sum(product['quantity'] for product in products)
        print(f"Totalt antal produkter i lager: {total_quantity} st")
    
    if option == "Medelvärde":
        print()
        print("Medelvärde för produkterna i lager är:")
        if not products:
            print("Inga produkter finns i lager.")
            return
        total = 0
        for product in products:
            total += product['price']
        average = total / len(products)
        print(f"Medelpris: {average:.2f} Kr")

def short_stats(products):
    # Quick stats without extra menus.
    total_quantity = sum(p['quantity'] for p in products)
    if not products:
        print("Inga produkter finns i lager.")
        return

    total_price = sum(p['price'] for p in products)
    total_cost = sum(p.get('cost', 0) for p in products)
    profit_per_item = (total_price - total_cost) / len(products) if products else 0

    stock_value = sum(p['price'] * p['quantity'] for p in products)
    stock_costs = sum(p.get('cost', 0) * p['quantity'] for p in products)

    print("=== Statistik ===")
    print(f"Totalt antal produkter: {total_quantity}")
    print(f"Vinst per produkt: {money_text(profit_per_item)}")
    print(f"Lagervärde (pris * antal): {money_text(stock_value)}")
    print(f"Kostnader totalt: {money_text(stock_costs)}")

DB_FILE = 'db_products.csv'

os.system('cls')
try:
    locale.setlocale(locale.LC_ALL, 'sv_SE.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, '')

products = read_products(DB_FILE)

keep_running = True
while keep_running:
    selected = list_products(products)
    if selected is None:
        break
    keep_running = show_menu(products, selected)

save_products(DB_FILE, products)
