# DB_with_NoSQL
> database project : stimulate DB with NOSQL

## How to Use

In hard-coded main.py, the parser will automatically parse your code.
When a parser calls parse method, it will return a list that have separated tokens.

## Command EBNF

Command
> Show | Create | Insert | Select | Update | Delete

Show
> **SHOW TABLES ";"**

Create
> **CREATE TABLE** Table-name **"("** Data-type Attribute-name ( **","** Data-type Attribute-name )* **")" ";"**

Insert
> **INSERT INTO** Table-name **VALUES "("** Attribute-value ( **","** Attribute-value )* **")" ";"**

Select
> **SELECT** ( __"*"__ | Attribute-name ( **","** Attribute-name )* ) **FROM** Table-name ( **Where** Simple-condition )? **";"**

Update
> **UPDATE** Table-name **SET** Attribute-name = Attribute-value ( **WHERE** Simple-condition )? **";"** 

Delete
> **DELETE FROM** Table-name ( **WHERE** Simple-condition )? **";"**

Table-name
> 

Data-type
> **INT | CHAR**

Attribute-name
>

Attribute-value
>

Simple-condition
>