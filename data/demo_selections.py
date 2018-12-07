"""demo_selections: Reproduce and demonstrate  how selections for
risk-limiting audits are done
"""

import collections
import hashlib
import sampler
import logging
import re


Batch = collections.namedtuple("batch", "county scanner batch cardcount location")


def select_ballots_to_audit(seed, batches, n):
    """Return list of n ballots to audit based on the given batches.

    batches is an iterator of manifest rows, as Batch objects

    Pull in full set of batches.
    Calculate total count.
    Draw sample of indexes into manifest across combined manifest.
    Map indexes to imprintedIds

    Print out by county

    >>> batches = [Batch("Adams", 1, 1, 90, ''), Batch("Boulder", 1, 1, 10, ''), ]
    >>> select_ballots_to_audit("01234567890123456789", batches, 4)
    [u'Adams-1-1-35', u'Adams-1-1-9', u'Adams-1-1-33', u'Boulder-1-1-6']
    """

    # Make a copy, assuming this is an iterator
    batches = list(batches)

    N = sum(batch.cardcount for batch in batches)

    ballots_to_audit = []

    _, new_list = sampler.generate_outputs(n, True, 1, N, seed, 0)

    logging.debug("Random selections, N=%d, n=%d, seed=%s: %s" %
                  (N, n, seed, new_list))

    selected = []
    for selection in new_list:
        i = 1
        for batch in batches:
            # If the selection fits in this batch
            if selection <= i + batch.cardcount:
                imprinted_id = "%s-%s-%s-%s" % (batch.county, batch.scanner, batch.batch, selection - i + 1)
                selected.append(imprinted_id)
                logging.log(5, "Selected ballot %s" % imprinted_id)
                break

            i += batch.cardcount

    return selected

    for i, cvr in enumerate(county_cvrs):
        if i in new_list:
            cvr['record_type'] = 'AUDITOR_ENTERED'
            selected.append(cvr)
            logging.info("Selected cvr %d: id: %d RecordID: %s" % (i, cvr['id'], cvr['imprinted_id']))

    return ballots_to_audit


def sampler_example(N, n, seed, demo_count):
    """Show derivation of first n selected ballots out of N, for given seed and CVR count"""

    print("""First we show how the seed is used by the sampler algorithm to select ballots
 from the CVR file. The seed, %s, is paired up
 with the numbers between 1 and the number of selections we need.
 We show details for the first %d:\n""" % (seed, demo_count))

    for i in range(1, demo_count+1):
        hash_input = "%s,%d" % (seed, i)
        hash_output_hex = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
        hash_output = int(hash_output_hex, 16)
        pick = int(1 + (hash_output % N))
        print("sha256('%s')\n = %s base 16\n = %d base 10.\n = %d mod %d. So the cvr_number of selected CVR number %d is %d."
              % (hash_input, hash_output_hex, hash_output, pick, N, i, pick))

    print()
    print("N=%d, n=%d" % (N, n))
    _, new_list = sampler.generate_outputs(n, True, 1, N, seed, False)
    print("First n cvr_numbers in expected selection order: %s" % new_list[:n])
    sorted_list = sorted(new_list)
    print("Those first n cvr_numbers in CVR file order: %s" % sorted_list[:n])
    print("Note: the imprinted_ids need to be looked up in the manifest file to put them in location order")

    """ comment out Old bisection approach - cleaner, faster, needs re-testing

    # FIXME: adapt this for CVR files, but save this manifest-based approch, hoping we implement that some day
    manifest_fields = ("county_name","scanner_id","batch_id","num_ballots","storage_location")
    ManifestRecord = collections.namedtuple('ManifestRecord', manifest_fields)

    with open(manifest_path, 'r') as manifest_stream:
        manifest_stream.readline()  # skip header - too inconsistent
        reader = csv.reader(manifest_stream)
        scanner_batch_ids = []
        cumulative_counts = []
        count = 0
        for row in map(ManifestRecord._make, reader):
            scanner_batch_ids.append('%s-%s' % (row.scanner_id, row.batch_id))
            num_ballots = int(row.num_ballots)
            cumulative_counts.append(count + num_ballots + 1)
            count += num_ballots

    N = count

    ...

    print("Assuming (incorrectly) that selection is from sorted imprinted ids....")
    for selection in sorted_list:
        batch = bisect.bisect(cumulative_counts, selection)
        batchname = scanner_batch_ids[batch]
        imprinted_id = "%s-%d" % (batchname, selection - cumulative_counts[batch - 1])
        print("Selection %d from imprinted_id: %s" % (selection, imprinted_id))

    """


# Code for natural sorting of selected ballots: natural_keys() and atoi(), from @unutbu
# https://stackoverflow.com/questions/5967500/how-to-correctly-sort-a-string-with-a-number-inside

def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)

    >>> alist = [
    ...          'Orange County--1-3-288-117',
    ...          'Orange County--48256-242',
    ...          'Orange County--1-3-388-203',
    ...          'Orange County--1-19-19-150',
    ...          'Orange County--1-1-64-290',
    ...          'Orange County--1-1-55-256']
    >>> alist.sort(key=natural_keys)
    >>> from pprint import pprint
    >>> pprint(alist)
    [u'Orange County--1-1-55-256',
     u'Orange County--1-1-64-290',
     u'Orange County--1-3-288-117',
     u'Orange County--1-3-388-203',
     u'Orange County--1-19-19-150',
     u'Orange County--48256-242']
    '''

    return [ atoi(c) for c in re.split('(\d+)', text) ]


def atoi(text):
    "Convert text to integer, or return it unmodified if it isn't numeric"

    return int(text) if text.isdigit() else text
