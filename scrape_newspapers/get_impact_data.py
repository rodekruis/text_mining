import plac

from impact_table_generator import ImpactTableGenerator
from utils import utils


@plac.annotations(
    config_file="Configuration file",
    input_filename=("Optional input filename", "option", "i", str),
    output_filename_base=("Optional output filename base", "option", "f", str),
    output_directory=("Optional output directory", "option", "o", str),
    debug=("Set log level to debug", "flag", "d")
)
def main(config_file, input_filename=None, output_filename_base=None, output_directory=None, debug=False):
    utils.set_log_level(debug)

    impact_table_generator = ImpactTableGenerator.ImpactTableGenerator(
        config_file,
        input_filename=input_filename,
        output_filename_base=output_filename_base,
        output_directory=output_directory)

    impact_table_generator.loop_over_articles()


if __name__ == '__main__':
    plac.call(main)
