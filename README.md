# DB_with_NoSQL
> database project : simulate DB with NOSQL

## How to (re)compile Redis source code

https://redis.io/download
if you failed to compile, you should check redis-5.0.2/deps directory and make all of them first.

## How to run Redis server

in bash, enter commands as shown below.

cd redis-5.0.2
src/redis-server

## How to run Redis Client (for debug)

in bash, enter commands as shown below.

cd redis-5.0.2
src/redis-cli

redis command is provided at
https://redis.io/commands

## How to Use

In hard-coded main.py, the parser will automatically parse your code.
When a parser calls parse method, it will return a list that have separated tokens.

## Command EBNF

Command
> show-stmt | create-stmt | insert-stmt | select-stmt | update-stmt | delete-stmt

show-stmt
> **SHOW TABLES ";"**

create-stmt
> **CREATE TABLE** identifier **"("** vardecls **")" ";"**

insert-stmt
> **INSERT INTO** identifier **VALUES "("** literals **")" ";"**

select-stmt
> **SELECT** ( __"*"__ | identifiers | aggregation) **FROM** identifier ( **Where** clause )? ( **GROUP BY** identifier )? ( **HAVING** having-clause )? **";"**

update-stmt
> **UPDATE** identifier **SET** identifier **"="** literal ( **WHERE** clause )? **";"** 

delete-stmt
> **DELETE FROM** identifier ( **WHERE** clause )? **";"**

vardecls
> vardecl ( **","** vardecl )*

vardecl
> identifier datatype

literals
> value ( **","** value )*

value
> **INTLITERAL** | **STRINGLITERAL**

clauses
> clause ( ( "and" | "or" ) clauses )? | "(" clauses ")"

clause
> identifier filter literal

having-clause
> aggregation filter literal

operator
> ( **">"** | **"="** | **"<"** | **">="** | **"!="** | **"<="** )

aggregation
> **SUM** **"("** identifier **")"** | **COUNT** **"("** identifier **")"**

identifiers
> identifier ( **","** identifier )*

identifier
> **alphabet** ( **alphabet** | **digit** )*

datatype
> **INT** | **VARCHAR**

literal
> **INTLITERAL** | **STRINGLITERAL**
