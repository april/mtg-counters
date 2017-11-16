#!/usr/bin/env python3

import os.path
import requests

# A list of words used for counters
COUNTER_WORDS = ('counter', 'counters')

# A list of prepositions and what not that cannot be counter types
FORBIDDEN_COUNTERS = ('a', 'additional', 'all', 'and', 'another', 'does', 'each',
                      'may', 'more', 'moved', 'no', 'of', 'target', 'that', 'the', 'those', 'with', 'would', 'X',
                      'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten')

# Retrieve the list of cards with "counter" in the name using the Scryfall API
#   re:"\bcounter\b" -oracle:"counter it" -oracle:"counter target" \
#   -oracle:"counter that" -oracle:"counter the" include:extras in:paper
# In theory "counter that" hits Decree of Silence, but depletion counters are on other cards
url = ('https://api.scryfall.com/cards/search?q='
       're%3A"\\bcounter\\b"+-oracle%3A"counter+it"'
       '+-oracle%3A"counter+target"+-oracle%3A"counter+that"+-oracle%3A"counter+the"+include%3Aextras+in%3Apaper')
session = requests.Session()

# Scryfall's API paginates responses, so you retrieve them 175 at a time
pages = [session.get(url).json()]
while pages[-1]['has_more']:
    pages.append(session.get(pages[-1]['next_page']).json())

# Each counter name is unique, so we use a set to store it
counters = set()


def get_counters(words: list, position: int, counters: list=[]):
    """
    :param words: a list of each word in a given card face
    :param position: the current position to begin looking for the counter name
    :param counters: any counters we've found thus far on the card face
    :return: list of all counters found on the card
    """

    # Guard against mutable arguments
    if not counters:
        counters = []

    # Get the word prior to the current word, in theory it's a counter type
    word = words[position]
    counter = word.replace(',', '')

    # If it's not in the preposition list, we can add it to the counters found at this position
    if counter not in FORBIDDEN_COUNTERS:
        counters.append(counter)

    # Now we need to look backwards – if it ended in a ',' or the previous word is 'or', we need to step backwards
    # and keep searching for more counter types. See Frankenstein's Monster for a reason why we need to do this:
    # https://scryfall.com/card/drk/45
    if word.endswith(','):
        get_counters(words, position - 1, counters)
    elif words[position - 1] == 'or':
        get_counters(words, position - 2, counters)

    return counters


for page in pages:
    for card in page.get('data'):
        # Cards can have multiple faces, such as split cards or flip cards. If so, we need to iterate through
        # each face. If they don't have a face, we can just look at the card itself
        for face in card.get('card_faces', [card]):
            words = face.get('oracle_text').split()

            for i in range(len(words)):
                if words[i] in COUNTER_WORDS:
                    [counters.add(counter) for counter in get_counters(words, i - 1)]

# Write the types to the types file
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist', 'types.txt'), 'w') as f:
    for counter in sorted(list(counters), key=lambda s: s.lower()):
        f.write(counter + '\n')
    f.write('\n')
