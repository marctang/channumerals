from bs4 import BeautifulSoup
from clldutils.path import walk
from pynumerals.number_parser import parse_number
import re

TABLE_IDENTIFIER = 'MsoTableGrid'
SKIP = ['How-to-view-EN.htm', 'How-to-view-CH.htm', 'problem.html']
ETHNOLOGUE = re.compile(r'http://www\.ethnologue\.com/')


def get_file_paths(raw_htmls):
    """
    Build a sorted list of PosixPath() objects for all files in the specified
    directory, e.g. numerals/raw/, skipping files defined in SKIP.
    :param raw_htmls: Path to raw numerals HTML files.
    :return: A list of PosixPath() objects with path information for the files.
    """
    return sorted([f for f in walk(raw_htmls)
                   if f.suffix.startswith('.htm') and f.name not in SKIP])


def find_tables(file_paths):
    """
    Find all tables defined by TABLE_IDENTIFIER in file_paths.
    :param file_paths: A list of PosixPath() objects containing path information
    for the numerals HTML files.
    :return: A generator with pairs of (LanguageName, ResultSet). If ResultSet
    is empty, there was no table defined in TABLE_IDENTIFIER in the
    corresponding HTML file.
    """
    for f in file_paths:
        parsed = BeautifulSoup(f.read_text(), 'html.parser')
        yield (f.stem,
               parsed.find_all('table', {'class': TABLE_IDENTIFIER}))


def find_number_table(table):
    """
    A helper function to identify tables containing number information so that
    we don't have to rely on the (implicit) ordering of tables within the HTML
    files.
    :param table: The tables from a ResultSet to be processed.
    :return: True if number table (>= 10 numerals), False otherwise.
    """
    numbers = []

    for element in table:
        try:
            # We collect all potential numbers in a list and simply check
            # the length of the list at the end.
            numbers.append(parse_number(element))
        except ValueError:
            pass

    # TODO: Check the sanity of this assumption.
    # We assume that we've found a number table if the list of numbers is >= 10.
    if len(numbers) >= 10:
        return True
    else:
        return False


def parse_table(table):
    """
    A helper function to parse tables into a list of strings. This used to
    make identifying tables containing numerals easier.
    :param table: A numerals HTML table.
    :return: A list of strings with the elements and other literal information.
    """
    table_elements = table.find_all('tr')
    elements = []

    for row in table_elements:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]

        for ele in cols:
            if ele:
                elements.append(ele)

    return elements


def iterate_tables(tables):
    number_tables = []
    other_tables = []

    for table in tables:
        parsed_table = parse_table(table)

        if find_number_table(parsed_table) is True:
            number_tables.append(parsed_table)
        else:
            other_tables.append(table)

    return number_tables, other_tables


def find_ethnologue_codes(tables):
    """
    Takes a set of tables (preferably other_tables from a NumeralsEntry object)
    and tries to find Ethnologue links and their corresponding codes for better
    matching of Glottocodes.
    :param tables: A set of tables (or a single table) from parsing a numerals
    HTML entry.
    :return: A list of Ethnologue codes found on the respective site.
    """
    ethnologue_codes = []

    for table in tables:
        link = table.find('a', href=ETHNOLOGUE)

        # Split URLs on their 'code=' part and take the last element, e.g.:
        # 'http://www.ethnologue.com/show_language.asp?code=pot' -> 'pot'
        # 'https://www.ethnologue.com/language/bth' -> 'bth'
        if link and ('code=' in link):
            ethnologue_codes.append(link['href'].split('code=')[1])
        elif link and ('language/' in link):
            ethnologue_codes.append(link['href'].split('language/')[1])

    return ethnologue_codes
