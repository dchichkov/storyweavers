"""Mechanical storytelling gates, independent of an English prose judge."""


def unfinished_outcomes(rows):
    keys = {k for row in rows for k in row.get('diagnostics',{}).get('outcome_writes',[])}
    def occurred(row, key):
        trace = row['trace']
        # A completed loan returns to its initial owner/null loan slot. The
        # executed history, not merely the endpoints, proves it took place.
        return (trace['initial'][key] != trace['final'][key] or
                any(key in event.get('changes', {}) for event in trace.get('events', [])))
    return sorted(k for k in keys if not any(occurred(row, k) for row in rows))


def validate_outcomes(rows):
    inert = unfinished_outcomes(rows)
    if inert:
        raise ValueError('Intended outcomes have writers but never change in any sample: '+str(inert)+'. '
                         'The goal may stop at a plan before actual performance/delivery/response. '
                         'Require the intended accomplishment in the goal; do not merely remove its outcome key.')
    kernels = {e['kernel'] for row in rows for e in row['trace']['events']}
    if not kernels.intersection({'Observe','Tell','Transfer'}):
        raise ValueError('No reusable knowledge or ownership kernel contributes to any final story')
