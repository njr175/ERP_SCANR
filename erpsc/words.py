"""MODULE DOCSTRING: TO FILL IN."""
from __future__ import print_function, division

import datetime
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords

# Import custom code
from erpsc.base import Base
from erpsc.erp_words import ERPWords
from erpsc.core.urls import URLS

#################################################################################
############################ ERPSC - WORDS - Classes ############################
#################################################################################

class Words(Base):
    """Class for searching through words in the abstracts of specified papers.

    Attributes
    ----------
    results : list of ERPWords() objects
        Results for each ERP, stored in custom Words object.
    """

    def __init__(self):
        """Initialize ERP-SCANR Words() object."""

        # Inherit from ERPSC Base Class
        Base.__init__(self)

        # Initialize a list to store results for all the erps
        self.results = list()


    def add_results(self, new_result):
        """Add a new Words() results object."""

        self.results.append(new_result)


    def scrape_data(self):
        """Search through pubmed for all abstracts referring to a given ERP.

        The scraping does an exact word search for the ERP term given.
        It then loops through all the artciles found about that data.
        For each article, pulls title, year and word data.

        Notes
        -----
        - Pulls data using the hierarchical tag structure that organize the articles.
        - Initially, the procedure was to pull all tags of a certain type.
            For example: extract all 'DateCreated' tags.
            This procedure fails (or badly organizes data) when an articles is
                missing a particular tag.
            Now: take advantage of the hierarchy, loop through each article tag.
                From here, pull out the data, if available.
                This way, can deal with cases of missing data.
        """

        # Set date of when data was collected
        self.date = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

        # Get e-utils URLS object
        urls = URLS(db='pubmed', retmode='xml', auto_gen=False)
        urls.build_search(['db', 'retmode'])
        urls.build_fetch(['db', 'retmode'])

        # Loop through all the erps
        for ind, erp in enumerate(self.erps):

            # Initiliaze object to store data for current erp papers
            cur_erp = ERPWords(erp)

            # Set up search terms - add exclusions, if there are any
            if self.exclusions[ind][0]:
                term_arg = '"' + erp[0] + '"' + 'NOT' + '"' + self.exclusions[ind][0] + '"'
            else:
                term_arg = '"' + erp[0] + '"'

            # Create the url for the erp search term
            url = urls.search + term_arg
            #url = urls.search + '"' + erp[0] + '"'
            #url = urls.search + '"' + erp + '"' + self.search_retmax
            #url = self.eutils_search + '"' + erp + '"NOT"' + '"cell"' + self.search_retmax

            # Get page and parse
            page = self.req.get_url(url)
            page_soup = BeautifulSoup(page.content, 'lxml')

            # Get all ids
            ids = page_soup.find_all('id')

            # Convert ids to string
            ids_str = _ids_to_str(ids)

            # Get article page
            art_url = urls.fetch + ids_str
            art_page = self.req.get_url(art_url)
            art_page_soup = BeautifulSoup(art_page.content, "xml")

            # Pull out articles
            articles = art_page_soup.findAll('PubmedArticle')

            # Loop through each article, extracting relevant information
            for ind, art in enumerate(articles):

                # Get ID of current article
                new_id = int(ids[ind].text)

                # Extract and add all relevant info from current articles to ERPWords object
                cur_erp = self.extract_add_info(cur_erp, new_id, art)

            # Check consistency of extracted results
            cur_erp.check_results()

            # Add the object with current erp data to results list
            self.add_results(cur_erp)


    def extract_add_info(self, cur_erp, new_id, art):
        """Extract information from article web page and add to

        Parameters
        ----------
        cur_erp : ERPWords() object
            xx
        new_id : ?
            xx
        art : ?
            xx

        NOTES
        -----
        - Data extraction is all in try/except statements in order to
        deal with missing data, since fields may be missing.
        """

        # Add ID of current article
        cur_erp.add_id(new_id)

        # Get Title of the paper, if available, and add to current results
        try:
            cur_title = art.find('ArticleTitle').text
        except AttributeError:
            cur_title = None
        cur_erp.add_title(cur_title)

        # Get Words from the Abstract, if available, and add to current results
        try:
            abstract_text = art.find('AbstractText').text
            cur_words = _process_words(abstract_text)
        except AttributeError:
            cur_words = None
        cur_erp.add_words(cur_words)

        # Get keywords, if available, and add to current results
        try:
            keywords = art.findAll('Keyword')
            kws = [kw.text for kw in keywords]
        except AttributeError:
            kws = None
        cur_erp.add_kws(kws)

        # Get the Year of the paper, if available, and add to current results
        try:
            cur_year = int(art.find('DateCreated').find('Year').text)
        except AttributeError:
            cur_year = None
        cur_erp.add_year(cur_year)

        # Increment number of articles included in ERPWords
        cur_erp.increment_n_articles()

        return cur_erp


    def combine_words(self):
        """Combine the words from each article together."""

        # Loop through each erp, and each article
        for erp in range(self.n_erps):
            for art in range(self.results[erp].n_articles):

                # Combine the words from each article into the 'all_words' collection
                self.results[erp].all_words.extend(self.results[erp].words[art])


    def freq_dists(self):
        """Create a frequency distribution from all the extracted words."""

        # Loop through all ERPs
        for erp in range(self.n_erps):

            # Use nltk to create a frequency distribution from all words
            self.results[erp].freqs = nltk.FreqDist(self.results[erp].all_words)

            # Remove the ERPs name from list of words
            #  Do this so that the erp itself isn't trivially the most common word
            try:
                self.results[erp].freqs.pop(self.erps[erp][0].lower())
            except KeyError:
                pass


    def check_words(self, n_check=20):
        """Check the most common words for each ERP.

        Parameters
        ----------
        n_check : int, optional (default=20)
            Number of top words, for each ERP, to print out.
        """

        # Loop through each ERP term
        for erp in range(self.n_erps):

            # Get the requested number of most common words for the ERP
            top_words = self.results[erp].freqs.most_common()[0:n_check]

            # Join together the top words into a string
            top_words_str = ''
            for i in range(n_check):
                top_words_str += top_words[i][0]
                top_words_str += ' , '

            # Print out the top words for the current ERP
            print(self.erps[erp][0], ': ', top_words_str)

#######################################################################################
######################### ERPSC - WORDS - FUNCTIONS (PRIVATE) #########################
#######################################################################################

def _ids_to_str(ids):
    """Takes a list of pubmed ids, returns a str of the ids separated by commas.

    Parameters
    ----------
    ids : BeautifulSoup ResultSet
        List of pubmed ids.

    Returns
    -------
    ids_str : str
        A string of all concatenated ids.
    """

    # Check how many ids in list
    n_ids = len(ids)

    # Initialize string with first id
    ids_str = str(ids[0].text)

    # Loop through rest of the id's, appending to end of id_str
    for i in range(1, n_ids):
        ids_str = ids_str + ',' + str(ids[i].text)

    # Return string of ids
    return ids_str


def _process_words(text):
    """Takes a text, sets to lower case, and removes all stopwords and punctuation.

    Parameters
    ----------
    text : ?
        xx

    Returns
    -------
    words_cleaned : list of str
        List of words, after processing.
    """

    # Tokenize input text
    words = nltk.word_tokenize(text)

    # Remove stop words, and non-alphabetical tokens (punctuation). Return the result.
    words_cleaned = [word.lower() for word in words if ((not word.lower() in stopwords.words('english'))
                                                         & word.isalpha())]

    return words_cleaned
