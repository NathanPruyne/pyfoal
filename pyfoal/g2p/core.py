import multiprocessing
import string

import g2p_en
import torch

import pyfoal


###############################################################################
# Grapheme-to-phoneme (G2P)
###############################################################################


def from_text(text):
    """Convert text to cmu"""
    # Remove newlines, tabs, and extra whitespace
    text = text.replace('\n', ' ')
    text = text.replace('\t', ' ')
    while '  ' in text:
        text = text.replace('  ', ' ')

    # Convert numbers to text
    text = g2p_en.expand.normalize_numbers(text)

    # Remove punctuation
    punctuation = [s for s in string.punctuation + '”“—' if s != '-']
    text = text.translate(str.maketrans('-', ' ', ''.join(punctuation)))

    # Grapheme-to-phoneme conversion
    phonemes = g2p_en.G2p()(text)

    # Remove prominence markings
    phonemes = [
        ''.join(c for c in phoneme if not c.isdigit())
        for phoneme in phonemes]
    
    # Handle silences
    phonemes = [
        '<silent>' if phoneme == ' ' else phoneme for phoneme in phonemes]

    # Ensure start and end have silent tokens
    if phonemes[0] != '<silent>':
        phonemes.insert(0, '<silent>')
    if phonemes[-1] != '<silent>':
        phonemes.append('<silent>')

    # Convert to indices
    indices = pyfoal.convert.phonemes_to_indices(phonemes)

    return torch.tensor(indices, dtype=torch.long)


def from_file(text_file):
    """Convert text on disk to phonemes"""
    return from_text(pyfoal.load.text(text_file))


def from_file_to_file(text_file, output_file):
    """Convert text on disk to phonemes and save"""
    torch.save(from_file(text_file), output_file)


def from_files_to_files(text_files, output_files):
    """Convert text on disk to phonemes and save"""
    with multiprocessing.Pool(pyfoal.NUM_WORKERS) as pool:
        pool.starmap(from_file_to_file, zip(text_files, output_files))
