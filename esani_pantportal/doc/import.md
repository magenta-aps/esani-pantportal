<!--
SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>

SPDX-License-Identifier: MPL-2.0
-->
Import af produkttyper
======================

Formular
--------

Produkttyper kan oprettes enkeltvis gennem [denne formular](/produkt/opret).
Alle felter udfyldes, og efterfølgende er produkttypen registreret og fremgår
af [produktlisten](/produkt).

Regneark
--------

Produkttyper kan oprettes i større mængder ved upload af et regneark til
[denne formular](/produkt/opret/multiple).  Skabelon til regnearket kan hentes i
[CSV-format](produkt/opret/multiple/csv_sample) eller
[Excel-format](produkt/opret/multiple/excel_sample), og der udfyldes en række
pr. produkttype.

I formularen skal filen angives, samt navn på hver kolonne, således at
regnearket kan fortolkes.  Formularen har forudfyldt disse felter med
kolonnenavnene som findes i skabelonen, så hvis de ikke er ændrede i
regnearket, behøver man ikke ændre standardværdierne i formularen.

Ved fejl i regnearket oprettes der ingen produkttyper, og der gøres opmærksom
på hvor fejlen ligger.
