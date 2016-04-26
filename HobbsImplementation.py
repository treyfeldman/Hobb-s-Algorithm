from nltk import ParentedTree, corpus
from nltk.corpus import treebank, names

import Queue

from collections import deque
from sys import argv

FILENAMES = [file for file in treebank.fileids()[:20]]


PRONOUNS = {'he': 'male', 'him': 'male', 'his': 'male', 'himself': 'male',
            'she': 'female', 'her': 'female', 'hers': 'female', 'herself': 'female',
            'they': 'plural', 'them': 'plural', 'their': 'plural', 'theirs': 'plural', 'themselves': 'plural',
            'it': 'singular', 'its': 'singular', 'itself': 'singular'}

PRONOUN_RESULTS = {'male': 0, 'male_total':0, 'male_pct':0, 'female': 0, 'female_total': 0, 'female_pct':0,'neutral': 0,
            'neutral_total': 0, 'neutral_pct':0, 'they': 0, 'they_total': 0, 'they_pct':0, 'reflexive': 0, 'reflexive_total': 0,
                   'reflexive_pct':0,}

NAMELIST = ([(name, "male") for name in names.words("male.txt")] +
           [(name, "female") for name in names.words("female.txt")])

NOMINALS = {'NN': 'singular', 'NNS': 'plural', 'NNP': 'singular', 'NNPS': 'plural', 'PRP': 'singular'}

def update_pronoun_results(pronoun, correct):
    if pronoun in ['he', 'him', 'his', 'himself']:
        if correct:
            PRONOUN_RESULTS['male'] += 1
        else:
            PRONOUN_RESULTS['male_total'] += 1
            PRONOUN_RESULTS['male_pct'] = PRONOUN_RESULTS['male'] / float(PRONOUN_RESULTS['male_total'])
    if pronoun in ['she', 'her', 'hers', 'herself']:
        if correct:
            PRONOUN_RESULTS['female'] += 1
        else:
            PRONOUN_RESULTS['female_total'] += 1
            PRONOUN_RESULTS['female_pct'] = PRONOUN_RESULTS['female'] / float(PRONOUN_RESULTS['female_total'])

    if pronoun in ['they', 'them', 'their', 'theirs', 'themselves']:
        if correct:
            PRONOUN_RESULTS['they'] += 1
        else:
            PRONOUN_RESULTS['they_total'] += 1
            PRONOUN_RESULTS['they_pct'] = PRONOUN_RESULTS['they'] / float(PRONOUN_RESULTS['they_total'])
    if pronoun in ['it', 'its', 'itself']:
        if correct:
            PRONOUN_RESULTS['neutral'] += 1
        else:
            PRONOUN_RESULTS['neutral_total'] += 1
            PRONOUN_RESULTS['neutral_pct'] = PRONOUN_RESULTS['neutral'] / float(PRONOUN_RESULTS['neutral_total'])
    if pronoun in ['himself', 'herself', 'themselves', 'itself']:
        if correct:
            PRONOUN_RESULTS['reflexive'] += 1
        else:
            PRONOUN_RESULTS['reflexive_total'] += 1
            PRONOUN_RESULTS['reflexive_pct'] = PRONOUN_RESULTS['reflexive'] / float(PRONOUN_RESULTS['reflexive_total'])

def get_bft(root):
    """Returns a list of nodes in the order of a breadth first traversal."""

    traversal = []

    queue = deque()
    queue.append(root)

    while len(queue) is not 0:
        node = queue.popleft()

        for child in node:
            if isinstance(child, ParentedTree):
                queue.append(child)

        traversal.append(node)

    return traversal


def get_dominant_np_or_s(node):

    path = [node]
    node = node.parent()
    if node == None:
        return None
    else:
        path.append(node)

    label = node.label()

    while label[0:2] != 'NP' and label[0:1] != 'S' and label[0:4] != 'SBAR':
        if isinstance(node, ParentedTree):
            node = node.parent()
            if node == None: return None
            label = node.label()
            path.append(node)

    return path


def find_pronouns(tree):
    pronouns = []
    for child in tree:
        if type(child) in [unicode, str] and child.lower() in PRONOUNS:
            pronouns.append((child, get_dominant_np_or_s(tree)[-1]))

        if isinstance(child, ParentedTree):
            pronouns = pronouns + find_pronouns(child)

    return pronouns

def propose(node, pronoun):

    at_least_one_proper = False
    if node.label() == 'NP-TMP':
        return False

    gender = PRONOUNS[pronoun]

    checked = False

    for child in node:
        if isinstance(child, ParentedTree):

            if child.label() in ['NNS', 'NNP']:
                at_least_one_proper = True

            if gender in ['male', 'female'] and child.label() == 'PRP$':
                    return False

            if child.label() in NOMINALS:
                checked = True


                noun = child.leaves()[0]


                if child.label() == 'PRP':
                    return False
                if child.label() == 'NNP':
                    if (noun, 'male') in NAMELIST and gender is not 'male':
                        if len(node) == 1:
                            return False
                    if (noun, 'female') in NAMELIST and gender is not 'female':
                        if len(node) == 1:
                            return False
                    if noun in ['Dr.', 'Mr.', 'Ms.', 'Mrs.', 'Judge']:
                        if noun == 'Mr.' and gender is not 'male':
                            return False
                        if noun in ['Ms.', 'Mrs.'] and gender is not 'female':
                            return False
                    else:
                        if child != node[-1] and '.' not in list(child.leaves()[0]):
                            if gender == 'male' and (noun, 'male') not in NAMELIST:
                                return False
                            if gender == 'female' and (noun, 'female') not in NAMELIST:
                                return False

                else:
                    if NOMINALS[child.label()] in ['singular', 'male', 'female'] and PRONOUNS[pronoun] == 'plural': # Check number agreement
                        return False
                    if NOMINALS[child.label()] == 'plural' and PRONOUNS[pronoun] != 'plural':
                        return False
    return (checked and at_least_one_proper)

def check_path_nps(x, proposed):
    """Checks whether there is an NP or S node between x and proposed"""


    proposed = proposed.parent()

    while proposed != x:
        if proposed.label()[0] == 'S' or proposed.label()[0:2] == 'NP':
            return True
        proposed = proposed.parent()


    return False

def check_path_nominal(path):
    for node in path:
        if node.label() in NOMINALS:
            return False

    return True


def path_is_child(node, list):
    """Checks if a list of nodes representing a path can be found in a tree given a node."""
    if len(list) == 0:
        return True
    else:
        for child in node:
            if child == list[-1]:
                return path_is_child(child, list[:-1])

    return False


def traverse_l_to_r(x, path, pronoun, check=0):

    queue = deque()
    if not check:
        queue.append(x)

    #Queue children that are left of path, if there is no path, all will get queued
    for child in x:
        if isinstance(child, ParentedTree):
            if path and child == path[-2]:
                break
            else:
                queue.append(child)


    while len(queue) is not 0:
        node = queue.popleft()

        if node != x:
            for child in node:
                if isinstance(child, ParentedTree):
                    queue.append(child)

        if node.label()[0:2] == 'NP':
            if check and not check_path_nps(x, node):
                continue
            if propose(node, pronoun):
                return node


def traverse_r_to_l(x, path, pronoun):
    queue = deque()
    right_of_path = False
    for child in x:
        if isinstance(child, ParentedTree):
            if path and child == path[-2]:
                right_of_path = True
                continue
            if right_of_path:
                queue.append(child)

    while len(queue) is not 0:
        node = queue.popleft()
        for child in node:
            if isinstance(child, ParentedTree):
                if node.label()[0:2] != 'NP' and node.label()[0] != 'S':
                    queue.append(child)

        if node.label()[0:2] == 'NP':
            if propose(node, pronoun):
                return node





def hobbs_to_string(np_node):
    if not np_node:
        return "No antecedent found."
    else:
        string = ""
        for leaf in np_node.leaves():
            string += leaf + " "

        return string[:-1]


def hobbs(np_node, pronoun, prev_sentences):

    # Step 2... Find first NP or S up the tree. Call it x.
    path = get_dominant_np_or_s(np_node)


    # Step 3... Traverse branches below and to the left of path p, breadth first and left to right. Make proposals.
    x = path[-1]
    proposal = traverse_l_to_r(x, path, pronoun, check=1)
    if proposal:
        return proposal


    # Step 5... out of order but the same logic. Path will be None if S was the root of the tree
    path = get_dominant_np_or_s(x)

    while not proposal:
        checked_sents = []
        # Step 4... S was highest? Traverse previous sentences...
        if not path:
            for prev in reversed(prev_sentences):
                proposal = traverse_l_to_r(prev, [], pronoun)
                checked_sents.append(prev)
                if proposal:
                    for c in reversed(checked_sents):
                        print c.pretty_print()
                    return proposal

            # All previous trees have been searched...
            return False

        # Step 5 ... path is already set to next NP/S node. Will do so again at bottom of loop if necessary
        x = path[-1]

        # Step 6...
        if x.label() == 'NP':
            if check_path_nominal(path):
                if propose(x, pronoun):
                    return x

        # Step 7...
        proposal = traverse_l_to_r(x, path, pronoun)
        if proposal:
            return proposal

        # Step 8...
        if x.label()[0] == 'S' and x.label()[0:4] != 'SBAR':
            proposal = traverse_r_to_l(x, path, pronoun)
            if proposal:
                return proposal


        path = get_dominant_np_or_s(x)


    return False



def main():
    answers = open('coref_key.txt', 'r')
    this_correct = 0
    correct = 0
    total = 0
    prev_sentences = deque()
    for file in FILENAMES:
        this_correct = 0
        this_total = 0
        prev_sentences.clear()
        for tree in treebank.parsed_sents(file):


            tree = ParentedTree.convert(tree)

            for pronoun, np_node in find_pronouns(tree):

                # i = 0
                # for t in list(prev_sentences)[-3:]:
                #     t.pretty_print()
                #     print("-"*25)
                #     i = i + 1
                #     if i == 3: break
                proposed = hobbs_to_string(hobbs(np_node, pronoun.lower(), prev_sentences))
                tree.pretty_print()

                actual = answers.readline()

                if  proposed == actual[:-1]:
                    update_pronoun_results(pronoun, 1)
                    correct += 1
                    this_correct += 1

                update_pronoun_results(pronoun, 0)
                total += 1
                this_total += 1

                print "Pronoun: '" + pronoun + "'   Proposed: '" + proposed + "'   Actual: '" + actual + "'"

                if total: print "Overall:\tCorrect:", correct, "\tTotal:", total, "\tPercentage:", correct/float(total), "\n"


                print("*"*100)
                print("*"*100)
            prev_sentences.append(tree)
        print("-"*50)
        if this_correct: print file,":\tCorrect:", this_correct, "\tTotal:", this_total, "\tPercentage:", this_correct/float(this_total), "\n"
        if total: print "Overall:\tCorrect:", correct, "\tTotal:", total, "\tPercentage:", correct/float(total), "\n"
        print("-"*50)

    print "Male correct:", PRONOUN_RESULTS['male'], "\tMale total:", PRONOUN_RESULTS['male_total'], "\tPercent correct:", PRONOUN_RESULTS['male_pct']
    print "Female correct:", PRONOUN_RESULTS['female'], "\tFemale total:", PRONOUN_RESULTS['female_total'], "\tPercent correct:", PRONOUN_RESULTS['female_pct']
    print "Neutral correct:", PRONOUN_RESULTS['neutral'], "\tNeutral total:", PRONOUN_RESULTS['neutral_total'], "\tPercent correct:", PRONOUN_RESULTS['neutral_pct']
    print "Plural correct:", PRONOUN_RESULTS['they'], "\tPlural total:", PRONOUN_RESULTS['they_total'], "\tPercent correct:", PRONOUN_RESULTS['they_pct']
    print "Reflexive correct:", PRONOUN_RESULTS['reflexive'], "\tReflexive total:", PRONOUN_RESULTS['reflexive_total'], "\tPercent correct:", PRONOUN_RESULTS['reflexive_pct']
    print "Total correct:", correct, "\tTotal:", total, "\tPercent correct:", correct/float(total)



if __name__ == "__main__":
    main()
