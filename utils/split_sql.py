import re
import os
import sys


HEADER = """CREATE DATABASE geometries;

\c geometries

CREATE EXTENSION postgis;

CREATE TABLE IF NOT EXISTS geometries (osm_id varchar, osm_type varchar, geom geometry, PRIMARY KEY (osm_id, osm_type));

INSERT INTO geometries VALUES
"""

TAIL = """
SELECT COUNT(*) FROM geometries;
"""

def write_lines(lines, sql_path):
    with open(sql_path, "w") as sql_file:
        sql_file.write(HEADER)
        for line in lines:
            sql_file.write(line)
        sql_file.write(TAIL)


def main(sql_path, n_lines):
    base_name = os.path.splitext(sql_path)[0]
    lines = []
    n_file = 0
    with open(sql_path) as sql_file:
        for _ in range(9):
            next(sql_file)
        for sql_line in sql_file:
            lines.append(sql_line)
            if "ON CONFLICT DO NOTHING" in sql_line:
                write_lines(lines, "%s_%s.sql" % (base_name, n_file))
                lines = []
                n_file += 1
                break
            elif len(lines) == n_lines:
                lines[-1] = re.sub(r',$', r' ON CONFLICT DO NOTHING;\n', lines[-1])
                write_lines(lines, "%s_%s.sql" % (base_name, n_file))
                lines = []
                n_file += 1


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))


