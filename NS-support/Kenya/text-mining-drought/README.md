# text-mining-drought

Extract impact data from bulletins of Kenya's National Drought Management Authority

## Requirements
1. Python > 3.6
2. [pandas](https://pypi.org/project/pandas/), [click](https://pypi.org/project/click/), [camelot](https://pypi.org/project/camelot-py/)
3. [ghostscript](https://www.ghostscript.com/)

## Usage
example:
```
$ python parse_table.py --input example-input.pdf --output example-output.xlsx
```
docstring
```shell
Usage: parse_table.py [OPTIONS]

Options:
  --input TEXT   input file (pdf)
  --output TEXT  output file (xlsx)
  --help         Show this message and exit.
```

