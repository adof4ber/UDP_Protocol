# P2P Komunikátor

Tento projekt implementuje P2P komunikáciu pomocou protokolu UDP. Je navrhnutý na zdieľanie dát a súborov medzi rôznymi zariadeniami v sieti.

## Obsah projektu

- **connection.py**: Spravuje nadviazanie a spravovanie UDP spojení medzi uzlami.
- **handshake.py**: 3-Way handshake na nadviazanie komunikácie
- **handshake_close.py**: 3-Way handshake na ukončenie spojenia 
- **data_transfer.py**: Obsahuje logiku na prenos dát, vrátane fragmentácie a výpočtu kontrolného súčtu.
- **file_transfer.py**: Funkcia zodpovedná za prenos súborov
- **keep_alive.py**: Udržuje aktívne spojenie medzi uzlami prostredníctvom pravidelných "keep-alive" správ.
- **main.py**: Hlavný spúšťací súbor aplikácie, ktorý inicializuje všetky komponenty.
- **DTPA.lua**: Dissector na rozpoznávanie protokolu vo WireShark


## Použitie

1. Uistite sa, že máte nainštalovaný Python 3.
2. Skopírujte si projekt do svojho lokálneho adresára.
3. Spustite `main.py`, zadajte port, na ktorom chcete, aby vaša aplikácia počúvala.
4. Pripojte sa k iným uzlom v sieti a začnite komunikovať.

## Požiadavky

Pre tento projekt sú potrebné nasledujúce Python knižnice:

- žiadne špeciálne závislosti (len štandardná knižnica Pythonu)


