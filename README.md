# 1. úkol z KIV/DS

## Architektura

Uzly jsou uspořádány do logického kruhu. Každý uzel komunikuje pouze s uzlem vpravo. Každý uzel má před spuštěním informaci o:
* svém portu (např. 8001)
* base-portu (např. 8000)
* počtu uzlů

Pravý soused uzlu má číslo portu o 1 vyšší než uzel (krom posledního uzlu - ten má jako pravého souseda první uzel).

Process volby a obravení je následující:
* Uzel generuje náhodné ID, čeká 15 vteřin a pak začne posílat pravému sousedovi ELECTION zprávu.
Pokud election zprávu přijme, předává ji doprava pouze pokud je ID odesílatele vyšší než ID uzlu. Každá zpráva obsahuje ID odesílatele - tzn. levého souseda - 
a původce, což je uzel, od kterého zpráva pochází (nepřepisuje se při předávání).
* Pokud uzel obdrží svoji ELECTION zprávu, tak udělala kolečko přes celý kruh. Uzel pak přestává vysílat ELECTION zprávy a vysílá LEADER zprávu.
* Uzel, který přijme LEADER zprávu, přestane vysílat ELECTION zprávy. Pokud uzel přijme svou vlastní LEADER zprávu, vyšle COLLECT zprávu pro získání ID uzlů.
* Pokud uzel přijme COLLECT zprávu, připojí k ní své ID a předá ji dál. Pokud se COLLECT zpráva vrátí k leaderovi, tak vygeneruje obarvení a pošle COLOR zprávu.
* Pokud uzel přijme COLOR zprávu, nastaví svou barvu.

Uzly tedy vysílají ELECTION zprávy dokud není jisté, že nějaká zpráva dokončila kolečko přes celý kruh - taková situace nastane, pokud leader uzel přijme znovu
svoji ELECTION zprávu, nebo pokud jiný (ne-leader) uzel přijme LEADER zprávu. V momentě, kdy je leader zvolený, nevadí, že jsou v oběhu ELECTION zprávy - protože
již existuje leader, tak zablokuje jakoukoliv ELECTION zprávu a tím pádem nemůže dojít k situaci, kdy by byli dva leadeři.
