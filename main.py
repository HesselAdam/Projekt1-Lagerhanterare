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

try:
    import termios
    import tty
except ImportError:
    termios = None
    tty = None

# Ensure we can read/write Swedish characters (å, ä, ö) in both terminal and files.
for stream in (sys.stdin, sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

def format_currency(value):
    try:
        return locale.currency(value, grouping=True)
    except Exception:
        return f"{value:.2f} kr"


def load_data(filename): 
    products = []
    if not os.path.exists(filename):
        return products

    with open(filename, 'r', encoding='utf-8') as file:       #öppnar en fil med read-rättighet
        reader = csv.DictReader(file)
        for row in reader:
            id = int(row['id'])
            name = row['name']
            desc = row['desc']
            price = float(row['price'])
            quantity = int(row['quantity'])
            
            products.append(
                {                   
                    "id": id,       
                    "name": name,
                    "desc": desc,
                    "price": price,
                    "quantity": quantity
                }
            )
    return products

# SPARAR DATAN SÅ JAG KAN RADERA BORT EN PRODUKT.
def save_data(filename, products):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        fieldnames = ['id', 'name', 'desc', 'price', 'quantity']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for product in products:
            writer.writerow(product)

def ensure_data_file(filename):
    if os.path.exists(filename):
        return
    save_data(filename, [])

def _read_key():
    """Get a single keypress (arrow keys, letters) without needing Enter."""
    if os.name == "nt":
        import msvcrt
        key = msvcrt.getch()
        if key in (b"\x00", b"\xe0"):  # special key prefix
            key += msvcrt.getch()
        return key.decode(encoding="latin-1", errors="ignore")  # latin-1 keeps arrow bytes intact
    if not termios or not tty:
        return sys.stdin.read(1)

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        first = sys.stdin.read(1)
        if first == "\x1b":  # escape sequence
            return first + sys.stdin.read(2)
        return first
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def _is_up(raw_key):
    """Return True if keypress is an up arrow (common ANSI/Windows codes)."""
    return raw_key in ("\x1b[A", "\x1bOA", "\xe0H", "\x00H") or (raw_key.startswith("\x1b[") and raw_key.endswith("A"))

def _is_down(raw_key):
    """Return True if keypress is a down arrow (common ANSI/Windows codes)."""
    return raw_key in ("\x1b[B", "\x1bOB", "\xe0P", "\x00P") or (raw_key.startswith("\x1b[") and raw_key.endswith("B"))

def browse_products(products):
    """Simple cursor-based browser for the product list."""
    if not products:
        print("Inga produkter i lager. Tryck 'a' för att lägga till en ny eller 'q'/Enter för att fortsätta.")
    index = 0
    while True:
        term_width = shutil.get_terminal_size(fallback=(80, 24)).columns
        if products:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Produkter (Piltangenter för att bläddra, Enter för att fortsätta, A för att lägga till, Q för att avsluta):")
            header = f" ID | {'Produktnamn':<30} | Pris      | Antal "
            print(header.ljust(term_width, "="))
            for i, product in enumerate(products):
                name = product['name'][:30]
                line = f" {product['id']:>2} | {name:<30} | {format_currency(product['price']):>8} | {product['quantity']:>5} st "
                line = line.ljust(term_width)
                if i == index:
                    print(f"\033[7m{line}\033[0m")  # invert colors for selection
                else:
                    print(line)
            print("=" * term_width)
        raw_key = _read_key()
        key = raw_key.lower()
        if key in ("", "\r", "\n", "q") or raw_key == "\x1b":  # Enter, q eller Esc avslutar
            break
        if products and _is_up(raw_key):
            index = (index - 1) % len(products)
        elif products and _is_down(raw_key):
            index = (index + 1) % len(products)
        elif key == "a":
            add_product(products, "Lägg till produkt")

def numererad_lista(products, option):
    if option == "Numererad lista":
        for i, product in enumerate(products, 1):
            print(f"{product['id']}) -- {i}. {product['name']} - {format_currency(product['price'])} - {product['quantity']} st")


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
        price = float(input("Ange produktens pris: "))
        quantity = int(input("Ange produktens kvantitet: "))

        new_product = {
            "id":new_id,
            "name": name,
            "desc": desc,
            "price": price,
            "quantity": quantity
        }
        products.append(new_product)
        return print(f"Produkten {name} har lagts till med id {new_id}.")

def change_product(products, option):
    if option == "Ändra data för produkt":
        product_id = int(input("Vilken produkt vill du ändra data för? (ange id): "))
        for product in products:
            if product["id"] != product_id:
                continue

            print(f"Nuvarande namn för produkten är: {product['name']}")
            new_name = input("Ange det nya namnet för produkten: ")
            product['name'] = new_name if new_name else product['name']
            
            print(f"Nuvarande beskrivning för produkten är: {product['desc']}")
            new_desc = input("Ange den nya beskrivningen för produkten: ")
            product['desc'] = new_desc if new_desc else product['desc']
            
            print(f"Nuvarande pris för produkten är: {product['price']}")
            new_price = input("Ange det nya priset för produkten: ")
            product['price'] = float(new_price) if new_price else product['price']
            
            print(f"Nuvarande kvantitet för produkten är: {product['quantity']}")
            new_quantity = input("Ange den nya kvantiteten för produkten: ")
            product['quantity'] = int(new_quantity) if new_quantity else product['quantity']
            
            return print(f"Produkten med id {product_id} har uppdaterats.")
        print(f"Hittade ingen produkt med id {product_id}.")

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

DB_FILE = 'db_products.csv'

os.system('cls' if os.name == 'nt' else 'clear')
try:
    locale.setlocale(locale.LC_ALL, 'sv_SE.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, '')

ensure_data_file(DB_FILE)
products = load_data(DB_FILE)

browse_products(products)

val = option_menu()

numererad_lista(products, val)
statistics(products, val)

if val == "Sök produkt (id)":
    product_id = int(input("Ange produktens id: "))
    get_product_by_id(products, val, product_id)

if val == "Radera produkt":
    product_id = int(input("Ange produktens id som ska tas bort: "))
    remove_product_by_id(products, val, product_id)

add_product(products, val)
change_product(products, val)

save_data(DB_FILE, products)
