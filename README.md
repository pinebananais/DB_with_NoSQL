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
> **CREATE TABLE** identifier **"("** Data-type identifier ( **","** Data-type identifier )* **")" ";"**

Insert
> **INSERT INTO** identifier **VALUES "("** Value ( **","** Value )* **")" ";"**

Select
> **SELECT** ( __"*"__ | identifier ( **","** identifier )* ) **FROM** identifier ( **Where** Condition )? **";"**

Update
> **UPDATE** identifier **SET** identifier = Value ( **WHERE** Condition )? **";"** 

Delete
> **DELETE FROM** identifier ( **WHERE** Condition )? **";"**

Condition
> identifier filter Value ( **"and"** identifier filter Value )*

filter
> ( **">"**|**"="**|**"<"**|**">="**|**"!="**|**"<="** )

identifier
> **alphbet** ( **alphbet** | **digit** )*

Data-type
> **INT** | **CHAR**

Value
> **INTLITERAL** | **STRINGLITERAL**