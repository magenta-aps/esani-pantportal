<!--
SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>

SPDX-License-Identifier: MPL-2.0
-->

# Overview

This directory contains the Pantportal system  (we may think of a better
name in the future).

The Pantportal system implements a deposit refund system for beverage
containers (mainly bottles and cans).

The system allows users to register products eligible for deposit
refunds (identified by their barcodes). It is able to import data about
returned containers from
[reverse vending machines](https://en.wikipedia.org/wiki/Reverse_vending_machine)
and connect these imports to the vendors (shops and other businesses) that will
receive the refunds. Payments may be made to these businesses by integrating
with the deposit administrator's accounts payable system.

The Pantportal system was created by [Magenta ApS](https://www.magenta.dk/)
for [Esani](https://esani.gl/), Greenland's national waste management company.

The Pantportal system is free software, and you are welcome to use,
study, modify and share it under the terms of the
[Mozilla Public License](https://www.mozilla.org/en-US/MPL/2.0/), version 2.0.

Copyright (c) 2023-204 Magenta ApS.

# Technology

The Pantportal system was built using Python and Django with a
Postgresql database.

The development environment uses Docker and `docker compose` - please
see the `docker` directory and the `docker-compose.yml` file for
details.


# Testing
To run the tests run
```
docker exec esani_pantportal bash -c 'coverage run manage.py test --parallel 4 ; coverage combine ; coverage report --show-missing'
```

To run tests only in a specific file run
```
docker exec esani_pantportal bash -c 'coverage run manage.py test esani_pantportal.tests.test_productlist'
```

# Profiling
To profile the application, add `prof` to the url. For example:
```
http://localhost:8000/bruger/?prof
```

# Brugerhåndtering
Der findes 4 forskellige slags brugere:
- ESANI admins (`EsaniUser`)
- Butiksmedarbejdere (`BranchUser`)
- Virksomhedsmedarbejdere (`CompanyUser`)
- Kioskejere (`KioskUser`)

dev miljø login oplysninger er som følgende:

| Bruger type             | login            |
|-------------------------|------------------|
| ESANI admin             | `admin:admin`    |
| Butiksmedarbejder       | `anders:anders`  |
| Virksomhedsmedarbejder  | `alfred:alfred`  |
| Kioskejer               | `oswald:oswald`  |

Butiks-, virksomheds og kioskbrugere kan enten være admin brugere eller også er de
almindelige brugere. Almindelige brugere har begrænsede rettigheder, mens admin brugere
kan oprette andre brugere og registrere nye produkter.

Virksomhedsbrugere kan kun oprette brugere i den samme virksomhed som dem selv, mens
ESANI brugere kan oprette brugere af alle slags:

| Bruger type             | opret `EsaniUser` | opret `BranchUser` | opret `CompanyUser` | opret `KioskUser` |
|-------------------------|---|---|----|----|
| ESANI admin             | x | x | x  | x  |
| Butiksmedarbejder       |   | x |    |    |
| Virksomhedsmedarbejder  |   | x | x  |    |
| Kioskejer               |   |   |    | x  |
| Uregistreret bruger     |   | x | x  | x  |

Når en uregistreret bruger opretter sig selv, skal han først godkendes af en ESANI
bruger, før han kan logge ind. Alle andre bruger typer er automatisk godkendt når de
bliver oprettet.

