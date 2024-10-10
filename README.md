# Data Transfer Protocol Ado (DTPA)

Tento projekt implementuje P2P (peer-to-peer) komunikáciu pomocou protokolu UDP. Je navrhnutý na prenos dát medzi rôznymi uzlami v sieti.

## Obsah projektu

- **connection.py**: Spravuje nadviazanie a spravovanie UDP spojení medzi uzlami.
- **data_transfer.py**: Obsahuje logiku na prenos dát, vrátane fragmentácie a výpočtu kontrolného súčtu.
- **error_handling.py**: Zodpovedá za spracovanie chýb a opätovné odosielanie fragmentov dát.
- **keep_alive.py**: Udržuje aktívne spojenie medzi uzlami prostredníctvom pravidelných "keep-alive" správ.
- **main.py**: Hlavný spúšťací súbor aplikácie, ktorý inicializuje všetky komponenty.

## Použitie

1. Uistite sa, že máte nainštalovaný Python 3.
2. Skopírujte si projekt do svojho lokálneho adresára.
3. Spustite `main.py`, zadajte cieľovú IP adresu, zdrojový a cieľový port na ktorom chcete počúvať.

## Požiadavky/odporúčania/veci

1. Obidva zariadenia musia byť na rovnakej sieti
2. V main repozitári je aj lua script ktorý rozpoznáva DTPA (Data Transfer Protocol Ado) protokol, stačí to spustiť na portoch 1069 alebo 1070


