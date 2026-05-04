from enum import Enum
import sys
import os
import struct
from dataclasses import dataclass


# import sqlparse - available if you need it!
def read_var_int(file):
    value = 0
    for i in range(9):
        byte = file.read(1)
        val = byte[0]
        if i == 8:
            value = (value << 8) | val
        else:
            value = (value << 7) | (val & 0x7F)
            if (val & 0x80) == 0:
                break
    return value


class column_type_enum(Enum):
    NULL = 0
    BIT8INT = 1
    BIT16INT = 2
    BIT24INT = 3
    BIT32INT = 4
    BIT48INT = 5
    BIT64INT = 6
    BIT64FLOAT = 7
    BLOB = 8
    STRING = 9


type_int_map = {
    0: column_type_enum.NULL,
    1: column_type_enum.BIT8INT,
    2: column_type_enum.BIT16INT,
    3: column_type_enum.BIT24INT,
    4: column_type_enum.BIT32INT,
    5: column_type_enum.BIT48INT,
    6: column_type_enum.BIT64INT,
    7: column_type_enum.BIT64FLOAT,
}

type_size_map = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 6, 6: 8, 7: 8}


def cast_int(x):
    return int.from_bytes(x, byteorder="big")


cast_bytes_map = {
    column_type_enum.BIT8INT: cast_int,
    column_type_enum.BIT16INT: cast_int,
    column_type_enum.BIT24INT: cast_int,
    column_type_enum.BIT32INT: cast_int,
    column_type_enum.BIT48INT: cast_int,
    column_type_enum.BIT64INT: cast_int,
    column_type_enum.BIT64FLOAT: lambda x: struct.unpack(">d", x)[0],
    column_type_enum.BLOB: lambda x: x,
    column_type_enum.STRING: lambda x: x.decode("utf-8"),
}


class column_type:
    def __init__(self, col_type, size):
        self.col_type = col_type
        self.size = size

    def __repr__(self):
        return f"column_type(col_type={self.col_type}, size={self.size})\n"


def get_column_type(type_i):
    if type_i in type_size_map:
        return type_int_map[type_i]

    if type_i % 2 == 0:
        return column_type_enum.BLOB

    if type_i % 2 == 1:
        return column_type_enum.STRING


def get_column_size(type, type_i):
    if type.value in type_size_map:
        return type_size_map[type.value]
    if type == column_type_enum.BLOB:
        return (type_i - 12) // 2
    if type == column_type_enum.STRING:
        return (type_i - 13) // 2


def get_column_type_info(type_t):
    t = get_column_type(type_t)
    s = get_column_size(t, type_t)

    return column_type(t, s)


class column_value:
    def __init__(self, col_type, value):
        self.col_type = col_type
        self.value = value

    def __repr__(self):
        return f"column_value(col_type={self.col_type}, value={self.value})\n"


def main():
    database_file_path = sys.argv[1]
    command = sys.argv[2]

    if command == ".dbinfo":
        with open(database_file_path, "rb") as database_file:
            # You can use print statements as follows for debugging, they'll be visible when running tests.
            print("Logs from your program will appear here!", file=sys.stderr)

            database_file.seek(16)  # Skip the first 16 bytes of the header
            page_size = int.from_bytes(database_file.read(2), byteorder="big")
            print(f"database page size: {page_size}")

            # skip remaining of file header
            database_file.seek(82, os.SEEK_CUR)

            # page header number cells
            database_file.seek(3, os.SEEK_CUR)
            nb_cells = int.from_bytes(database_file.read(2), byteorder="big")

            # go to the end of page header
            database_file.seek(3, os.SEEK_CUR)

            # collect cell pointers
            cell_pointers = []
            for cell in range(nb_cells):
                cell_pointers.append(
                    int.from_bytes(database_file.read(2), byteorder="big")
                )

            database_file.seek(cell_pointers[2])
            payload_size = read_var_int(database_file)
            rowid = read_var_int(database_file)

            start_payload_pointer = database_file.tell()
            payload_header_size = read_var_int(database_file)

            column_types = []

            while database_file.tell() < start_payload_pointer + payload_header_size:
                column_type = read_var_int(database_file)
                column_types.append(get_column_type_info(column_type))

            column_values = []

            for column_type in column_types:
                value = cast_bytes_map[column_type.col_type](
                    database_file.read(column_type.size)
                )
                column_values.append(column_value(column_type.col_type, value))

            print(column_values)
            print(f"number of tables: {nb_cells}")
    else:
        print(f"Invalid command: {command}")


if __name__ == "__main__":
    main()
