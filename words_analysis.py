"""   """

from erpsc.core.io import load_pickle_obj
from erpsc.erp_data_all import ERPDataAll
from erpsc.plts.wc import make_wc
from erpsc.plts.dat import plot_years

######################################################################
######################################################################

F_NAME = 'BaseScrape_words'

######################################################################
######################################################################

def main():
    """   """

    # Load pickle object
    words = load_pickle_obj(F_NAME)

    for erp in words.result_keys:

        # Check if raw data loaded - load if not
        # TODO!

        # Turn into ERPDataAll object
        erp_dat = ERPDataAll(words[erp])

        # Create and save summary
        erp_dat.create_summary()
        erp_dat.save_summary()

        # Create and save wordcloud figure
        make_wc(erp_dat.word_freqs, 20, erp_dat.label,
                disp_fig=False, save_fig=True)

        # Create and save years figure
        plot_years(erp_dat.year_counts, erp_dat.label,
                   disp_fig=False, save_fig=True)

if __name__ == "__main__":
    main()