"""Token-local grammar provenance with explicit scene-level semantic scope.

Annotations describe committed traces; they do not authorize state changes.
No English parsing or guessed word-level event/POS attribution is performed.
"""
from copy import deepcopy
from dataclasses import asdict

from ..symbolic_heads.positions import Position, SymbolicRotary


def aligned_expansions(node, ancestors=()):
    """Expand with each terminal's grammar ancestry, preserving unit boundaries."""
    path = ancestors + (node.label,)
    if node.kind == 'text':
        yield tuple((word, frozenset(path)) for word in node.children)
    elif node.kind == 'choice':
        for child in node.children:
            yield from aligned_expansions(child, path)
    elif node.kind == 'sequence':
        rows = [()]
        for child in node.children:
            branches = list(aligned_expansions(child, path))
            rows = [left + right for left in rows for right in branches]
        yield from rows
    else:
        raise ValueError(f'unknown grammar node: {node.kind}')


class TokenAnnotations:
    def __init__(self):
        self.tokens = []
        self.hidden = []

    def append(self, node, tokens, frame, before, after, trace_event):
        """Attach only labels shared by all derivations of the chosen surface."""
        context = dict(name=frame.kind.replace('_', ' '), source_kind=frame.kind,
                       scope='committed_scene',
                       roles={key: getattr(frame, key) for key in
                              ('actor', 'patient', 'instrument', 'destination')
                              if getattr(frame, key)})
        if not tokens:
            # A silent world operation has no invented word/position anchor.
            self.hidden.append(dict(trace_event=trace_event, context=context,
                                    before_next_token=len(self.tokens)))
            return
        matches = [row for row in aligned_expansions(node)
                   if tuple(word for word, _ in row) == tuple(tokens)]
        if not matches:
            raise ValueError('sampled words do not match the annotated grammar')
        anchor = len(self.tokens)
        for i, word in enumerate(tokens):
            labels = set.intersection(*(set(row[i][1]) for row in matches))
            refs = sorted(label.split(':', 1)[1] for label in labels
                          if label.startswith('referent:'))
            if any(entity not in before or entity not in after for entity in refs):
                raise ValueError('entity annotation lacks a physical carrier')
            self.tokens.append(dict(token=word, grammar_tags=sorted(labels),
                entities=refs, event_context={**deepcopy(context), 'anchor_token': anchor},
                entity_state={entity: dict(scope='scene_boundary_observation',
                    before=deepcopy(before[entity]), after=deepcopy(after[entity]))
                    for entity in refs}))

    def finish(self, namespace):
        rotary = SymbolicRotary()
        result = deepcopy(self.tokens)
        sentence = local = 0
        pending_boundary = False
        for index, item in enumerate(result):
            word = item['token']
            # Closing quotes/punctuation belong to the preceding sentence.
            if pending_boundary and word not in {'”', '"', '.', '!', '?'}:
                sentence += 1
                local = 0
                pending_boundary = False
            position = Position(namespace, index, sentence, local)
            item['position'] = asdict(position)
            item['rotary'] = rotary.encode(position)
            local += 1
            if word in {'.', '!', '?'}:
                pending_boundary = True
        return dict(schema='positioned-story-tokens-v1', story=namespace,
                    periods=list(rotary.periods), tokens=result,
                    unnarrated_operations=deepcopy(self.hidden),
                    semantics='observations_after_scene_commit; not online word-level effects')
