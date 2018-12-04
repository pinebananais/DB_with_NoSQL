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
> **CREATE TABLE** identifier **"("** Vardecl ( **","** Vardecl )* **")" ";"**

Insert
> **INSERT INTO** identifier **VALUES "("** Value ( **","** Value )* **")" ";"**

Select
> **SELECT** ( __"*"__ | identifier ( **","** identifier )* ) **FROM** identifier ( **Where** Conditions )? **";"**

Update
> **UPDATE** identifier **SET** identifier **"="** Value ( **WHERE** Conditions )? **";"** 

Delete
> **DELETE FROM** identifier ( **WHERE** Conditions )? **";"**

Vardecl
> identifier Data-type

Conditions
> Condition ( ( **"and"** | **"or"** ) Condition )*

Condition
> identifier filter Value | "(" Conditions ")"

filter
> ( **">"** | **"="** | **"<"** | **">="** | **"!="** | **"<="** )

identifier
> **alphabet** ( **alphabet** | **digit** )*

Data-type
> **INT** | **VARCHAR**

Value
> **INTLITERAL** | **STRINGLITERAL**