import importlib

import plac

utils = importlib.import_module('utils')
ImpactTableGenerator = importlib.import_module('ImpactTableGenerator')


@plac.annotations(
    config_file="Configuration file",
    input_filename=("Optional input filename", "option", "i", str),
    output_filename_base=("Optional output filename base", "option", "o", str)
)
def main(config_file, input_filename=None, output_filename_base=None):

    impact_table_generator = ImpactTableGenerator.ImpactTableGenerator(
        config_file,
        input_filename=input_filename,
        output_filename_base=output_filename_base)

    impact_table_generator.loop_over_articles()


if __name__ == '__main__':
    plac.call(main)
