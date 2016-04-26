from nltk.corpus import treebank
from nltk import ParentedTree
from operator import itemgetter

stats = {'name': '', 'gendered': 0, 'total': 0, 'itits': 0, 'pct_gendered':0.0}

PRONOUNS = ['he', 'him', 'his', 'himself',
            'she', 'her', 'hers', 'herself',
            'they', 'them', 'their', 'theirs', 'themselves',
            'it', 'its', 'itself']

gendered = ['he', 'him', 'his', 'she', 'her', 'hers', 'himself', 'herself']

itits = ['it', 'its', 'itself']

files = []

def find_pronouns(tree):
    pronouns = []
    for child in tree:
        if type(child) in [unicode, str] and child.lower() in PRONOUNS:
            pronouns.append((child.lower(), None))

        if isinstance(child, ParentedTree):
            pronouns = pronouns + find_pronouns(child)

    return pronouns

total = 0
for file in treebank.fileids():
    stats['name'] = file
    for tree in treebank.parsed_sents(file):
        tree = ParentedTree.convert(tree)
        for pronoun, np_node in find_pronouns(tree):
            if pronoun in gendered:
                stats['gendered'] += 1
            if pronoun in itits:
                stats['itits'] += 1
            stats['total'] += 1
            total += 1
            stats['pct_gendered'] = stats['gendered']/float(stats['total'])
    print file, total


    files.append(stats.copy())
    stats = dict.fromkeys(stats, 0)






for f in files:
    print f
