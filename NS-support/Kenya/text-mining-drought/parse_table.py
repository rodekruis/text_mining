import camelot
import pandas as pd
import click
import os


@click.command()
@click.option('--input', help='input file (pdf)')
@click.option('--output', help='output file (xlsx)')
def parse_table(input, output):

    # load and parse data
    tables = camelot.read_pdf(input, pages="1", area="right")
    data = tables[0].df

    # fix columns
    for ix, row in data.iterrows():
        if row[3] == '' and not pd.isna(row[2]):
            data.at[ix, 3] = row[2]
        if row[2] == '' and not pd.isna(row[3]):
            data.at[ix, 2] = row[3]

    # remove rows with no data or description
    data = data[(data[3] != '') & (data[3] != 'Value')]
    data = data[[1, 3]]

    # transpose index and columns
    data = data.T
    # remove first column
    data = data.drop(data.columns[0], axis=1)
    # use first row as column names
    new_header = data.iloc[0]
    data = data[1:]
    data.columns = new_header

    # print and save data
    print(data)

    if not output.endswith('xlsx'):
        raise TypeError('output has not extension .xlsx')
    data.to_excel(output)


if __name__ == "__main__":
    parse_table()