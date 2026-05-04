[![progress-banner](https://backend.codecrafters.io/progress/sqlite/81bc6281-502e-45b3-9c54-15ea437f5b32)](https://app.codecrafters.io/users/codecrafters-bot?r=2qF)

This is a starting point for Python solutions to the
["Build Your Own SQLite" Challenge](https://codecrafters.io/challenges/sqlite).

In this challenge, you'll build a barebones SQLite implementation that supports
basic SQL queries like `SELECT`. Along the way we'll learn about
[SQLite's file format](https://www.sqlite.org/fileformat.html), how indexed data
is
[stored in B-trees](https://jvns.ca/blog/2014/10/02/how-does-sqlite-work-part-2-btrees/)
and more.

**Note**: If you're viewing this repo on GitHub, head over to
[codecrafters.io](https://codecrafters.io) to try the challenge.

# Current Implementation

This repository currently implements a subset of an SQLite parser capable of reading basic database structure and record formats. The following features are currently implemented in `app/main.py`:

## 1. Database Header Parsing
- Extracts the **database page size** from the SQLite file header.

## 2. Page Header Parsing
- Reads the page header of the root B-tree page to extract the **number of cells** (which corresponds to the number of tables/indexes in the `sqlite_schema`).

## 3. SQLite Varint Decoding
- Implements custom logic to correctly decode SQLite's variable-length integers (varints), which use 7-bit payloads per byte (and 8 bits for the 9th byte).

## 4. B-Tree Leaf Cell Parsing
- Reads cell pointers from the page header.
- Navigates to B-tree leaf cells to extract:
  - **Payload Size**
  - **Row ID**

## 5. Record Format Parsing
- Parses the SQLite record format header to determine column data types.
- Supports decoding the following SQLite serial types into Python structures:
  - `NULL`
  - Integer types: 8-bit, 16-bit, 24-bit, 32-bit, 48-bit, 64-bit (`BIT8INT` to `BIT64INT`)
  - Float type: 64-bit IEEE 754 float (`BIT64FLOAT`) using the `struct` module
  - Text: `STRING` (UTF-8 encoded)
  - Raw binary: `BLOB`
- Dynamically casts byte sequences into appropriate Python primitives (`int`, `float`, `str`, `bytes`) based on the serial type.

## Supported Commands
- `.dbinfo`: When run against a database file (e.g., `python3 -m app.main sample.db .dbinfo`), it outputs:
  - The database page size.
  - The decoded column values of a record from the `sqlite_schema` table.
  - The total number of tables (cells) in the database.
