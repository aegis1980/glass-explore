#(c)2026 Jon Robinson. All Rights Reserved.

"""Text search over the glass table, for the search modal.

A query is split into words and a glass matches when every word is found in its file
name, product name, manufacturer, coating name or nominal thickness ("6mm"), or at the
start of its ID. Text is compared in a normalised form (lower case, no accents, no
punctuation or trade mark signs), so "solarban 60" finds "Solarban® 60".

Only when no glass matches all the words are two looser readings tried, in this order:

1. words split where letters meet digits ("solarban60" -> "solarban 60");
2. words that occur nowhere in the table replaced by similarly spelled ones that do
   ("pilkinton" -> "pilkington"). SearchResult.similar is True for these.

If neither finds anything the result is empty: there is no "closest 30" fallback, which
used to fill the table with unrelated products.

The manufacturer and thickness filters are applied after matching, so a result also says
how many glasses match in the whole table (SearchResult.total_unfiltered).
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import pandas as pd
from thefuzz import fuzz, process

from glass_explore import DF_GLASS_TABLE

# Most rows the search modal's table is sent. Enough for every glass of the largest
# manufacturer (about 650); it only bites on a one-letter query or on no query and no
# filters, which would otherwise send all of the table on each keystroke.
MAX_ROWS = 1000

_NO_COATING_NAME = ('N/A', 'Unknown')   # IGDB placeholders, not worth matching on

# Spelling correction: only for words at least this long, and only to words this similar
_SPELLING_MIN_LENGTH = 4
_SPELLING_CUTOFF = 80           # thefuzz ratio, 0-100
_SPELLING_ALTERNATIVES = 5


def normalise(text) -> str:
    """Lower case, accents folded, and anything that is not a letter or digit turned into a space."""
    text = '' if text is None else str(text).replace('™', ' ').replace('®', ' ')
    text = ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))
    return ' '.join(re.sub(r'[\W_]+', ' ', text.lower()).split())


def _split_letters_and_digits(text: str) -> str:
    text = re.sub(r'(?<=[^\W\d_])(?=\d)', ' ', text)
    return re.sub(r'(?<=\d)(?=[^\W\d_])', ' ', text)


def _natural_key(text: str) -> list:
    """Sort key that orders the numbers inside a name by value: "3mm" before "10mm"."""
    return [int(part) if part.isdigit() else part for part in re.split(r'(\d+)', text)]


@dataclass(frozen=True)
class SearchIndex:
    """
    Normalised text of a glass table, indexed by Glass.ID. Each text starts with a space, so
    that ' word' finds a word start with a plain substring test.
    """
    text: pd.Series             # everything that is searched
    own: pd.Series              # the same without the coating name, for ordering the results
    ids: pd.Series              # Glass.ID as text
    file: pd.Series             # the IGDB file name (Glass.Name), for ordering the results
    product: pd.Series          # the product name, for ordering the results
    name_rank: pd.Series        # position of the product name in natural sort order
    thickness: pd.Series        # mm, for ordering the results
    vocabulary: Tuple[str, ...] # the distinct words of the table that spelling correction may suggest


def build_index(df: pd.DataFrame) -> SearchIndex:
    """Search index of a glass table (DF_GLASS_TABLE or a frame with the same columns)."""
    coating = df['Coating_Name'].fillna('')
    coating = coating.where(~coating.isin(_NO_COATING_NAME), '')
    nominal = df['Thickness'].fillna(0).round().astype(int).astype(str) + 'mm'
    own = (df['Name'].fillna('') + ' ' + df['ProductName'].fillna('') + ' '
           + df['Manufacturer'].fillna('') + ' ' + nominal).map(normalise)

    text = ' ' + own + ' ' + coating.map(normalise)
    product = df['ProductName'].fillna('').map(normalise)
    name_rank = {name: rank for rank, name in enumerate(sorted(set(product), key=_natural_key))}
    vocabulary = tuple(sorted({
        word for words in text.str.split() for word in words
        if len(word) >= _SPELLING_MIN_LENGTH and not word.isdigit()
    }))

    return SearchIndex(
        text=text,
        own=' ' + own,
        ids=pd.Series(df.index.astype(str), index=df.index),
        file=' ' + df['Name'].fillna('').map(normalise),
        product=' ' + product,
        name_rank=product.map(name_rank),
        thickness=df['Thickness'],
        vocabulary=vocabulary,
    )


_INDEX = build_index(DF_GLASS_TABLE)


@dataclass(frozen=True)
class SearchResult:
    ids: pd.Index           # matching Glass.IDs within the filter, best first, at most `limit`
    total: int              # matches within the filter, before `limit`
    total_unfiltered: int   # matches in the whole table
    similar: bool           # True when the words had to be spelling-corrected to match
    has_query: bool         # False when the query had no letters or digits: nothing was searched for


def _matches(index: SearchIndex, spellings: Sequence[str], word_start: bool = False) -> pd.Series:
    """Glasses that have one query word, in any of its spellings."""
    mask = pd.Series(False, index=index.text.index)
    for word in spellings:
        if word.isdigit():
            # A number counts only from the start of a word or of the ID: "60" should not
            # find "160" or ID 2060.
            mask |= index.text.str.contains(' ' + word, regex=False) | index.ids.str.startswith(word)
        else:
            mask |= index.text.str.contains((' ' + word) if word_start else word, regex=False)
    return mask


def _matches_all(index: SearchIndex, words: List[Sequence[str]]) -> pd.Series:
    mask = pd.Series(True, index=index.text.index)
    for spellings in words:
        mask &= _matches(index, spellings)
    return mask


def _spellings(index: SearchIndex, word: str) -> Sequence[str]:
    """The word itself if the table has it, otherwise the similarly spelled words it does have."""
    if _matches(index, (word,)).any():
        return (word,)
    if word.isdigit() or len(word) < _SPELLING_MIN_LENGTH:
        return ()
    close = process.extractBests(word, index.vocabulary, scorer=fuzz.ratio,
                                 score_cutoff=_SPELLING_CUTOFF, limit=_SPELLING_ALTERNATIVES)
    return tuple(choice for choice, _score in close)


_NOT_IN_NAME = 10_000   # position given to a word that is in neither the file nor the product name


def _best_first(index: SearchIndex, ids: pd.Index, words: List[Sequence[str]]) -> pd.Index:
    """
    Order the matches, most relevant first:

    1. an exact ID;
    2. more of the query words outside the coating name: "skn 176" puts SKN 176 before an
       SKN 076 whose coating is called SKN 176, and "pilkington energy advantage" puts
       Pilkington's glass before another maker's laminate that contains it;
    3. more of the query words at the start of a word: "guard" is inside "SunGuard" but
       starts "Guardian";
    4. a query word earlier in the name: "Solarban 60 on Clear" before a product that
       mentions Solarban 60 further along;
    5. product name, with its numbers in numeric order, then thickness, so the thicknesses
       of one product sit together.
    """
    numbers = [word for spellings in words for word in spellings if word.isdigit()]
    own, file, product = index.own.loc[ids], index.file.loc[ids], index.product.loc[ids]

    own_words = pd.Series(0, index=ids)
    position = pd.Series(_NOT_IN_NAME, index=ids)
    for spellings in words:
        in_own = pd.Series(False, index=ids)
        for word in spellings:
            needle = (' ' + word) if word.isdigit() else word
            in_own |= own.str.contains(needle, regex=False)
            for field in (file, product):
                at = field.str.find(needle)
                position = position.where((at < 0) | (position <= at), at)
        own_words += in_own.astype(int)

    word_starts = sum(_matches(index, spellings, word_start=True).loc[ids].astype(int) for spellings in words)

    order = pd.DataFrame({
        'exact_id': index.ids.loc[ids].isin(numbers),
        'own_words': own_words,
        'word_starts': word_starts,
        'position': position,
        'name_rank': index.name_rank.loc[ids],
        'thickness': index.thickness.loc[ids],
    })
    order = order.sort_values(['exact_id', 'own_words', 'word_starts', 'position', 'name_rank', 'thickness'],
                              ascending=[False, False, False, True, True, True], kind='stable')
    return order.index


def search(query: Optional[str], allowed_ids=None, limit: Optional[int] = None,
           index: Optional[SearchIndex] = None) -> SearchResult:
    """
    Search the glass table.

    Args:
        query: what the user typed; empty or None lists every allowed glass in table order
        allowed_ids: Glass.IDs left by the manufacturer / thickness filters; None for no filter
        limit: most IDs to return (SearchResult.total still counts them all)
        index: search index; the app's glass table by default
    """
    index = index or _INDEX
    all_ids = index.text.index
    allowed = pd.Series(True, index=all_ids) if allowed_ids is None else pd.Series(all_ids.isin(allowed_ids), index=all_ids)

    tokens = normalise(query or '').split()
    if not tokens:
        ids = all_ids[allowed.to_numpy()]
        return SearchResult(ids=ids[:limit], total=len(ids), total_unfiltered=len(all_ids), similar=False, has_query=False)

    words: List[Sequence[str]] = [(token,) for token in tokens]
    mask = _matches_all(index, words)
    similar = False

    if not mask.any():
        split = [(token,) for token in _split_letters_and_digits(' '.join(tokens)).split()]
        if split != words:
            split_mask = _matches_all(index, split)
            if split_mask.any():
                words, mask = split, split_mask

    if not mask.any():
        corrected = [_spellings(index, spellings[0]) for spellings in words]
        corrected_mask = _matches_all(index, corrected)
        if corrected_mask.any():
            words, mask, similar = corrected, corrected_mask, True

    ids = all_ids[(mask & allowed).to_numpy()]
    if len(ids):
        ids = _best_first(index, ids, words)

    return SearchResult(ids=ids[:limit], total=len(ids), total_unfiltered=int(mask.sum()), similar=similar, has_query=True)
