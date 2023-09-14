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
  - Afgiftsgruppe (Vareart) (CharacterField)
  - Vareart (CharacterField)
  - Antal (IntegerField)
