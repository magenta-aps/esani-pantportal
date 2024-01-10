<!--
SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>

SPDX-License-Identifier: MPL-2.0
-->

# Testing
To run the tests run
```
docker exec esani_pantportal bash -c 'coverage run manage.py test --parallel 4 ; coverage combine ; coverage report --show-missing'
```

To run tests only in a specific file run
```
docker exec esani_pantportal bash -c 'coverage run manage.py test esani_pantportal.tests.test_productlist'
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

Når en uregistreret bruger opretter sig selv, skan han først godkendes af en ESANI
bruger, før han kan logge ind. Alle andre bruger typer er automatisk godkendt når de
bliver oprettet.


# ESANI Pantportal

TODOs:
* Await confirmation from ESANI
* Write an entry in salt-automation/docs/projects/grønland/projekter on ESANI Pantportal


[#57563] Definition af tabel til indkommende pant:
Fra TF10 blanketten kan vi udtrække følgende (og mere, men disse er mest interessante):
Importoplysninger:
  - Afgiftsanmeldelsesnummer (IntegerField)

Firmaoplysninger Modtager: 
  - CVR (IntegerField)
  - Firmanavn (CharacterField)
  - Adresse (CharacterField)
  - Telefonnummer (IntegerField)
  - Tilladelsesnummer (IntegerField)

Produktoplysninger:
  - Antal (IntegerField)
