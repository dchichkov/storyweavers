"""Pure local, atomic exact-span edits and paired kernel/text patches."""
from __future__ import annotations

import copy
import ast
import difflib
import hashlib
import json
import re

from .kernel_author import parse_kernel, validate_result


SPAN_TOOL = {
    'type': 'function', 'name': 'apply_patch', 'strict': True,
    'description': ('Submit exact-span edits. Each target is story, title, '
                    'qa/ID/question, qa/ID/answer, or qa/ID. Replace old with new '
                    'exactly once in the selected string, not an entire JSON line. '
                    'Include enough surrounding text for a unique match. For qa/ID '
                    'only, old/new are serialized question/answer objects; empty old '
                    'adds a new ID, empty new removes it. Use a unique ID for additions. '
                    'All edits apply atomically; no read/write tools are available.'),
    'parameters': {'type': 'object', 'properties': {'edits': {'type': 'array',
        'items': {'type': 'object', 'properties': {
            'target': {'type': 'string'}, 'old': {'type': 'string'}, 'new': {'type': 'string'}},
            'required': ['target', 'old', 'new'], 'additionalProperties': False}}},
        'required': ['edits'], 'additionalProperties': False},
}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def unique(text, old):
    start = text.find(old) if old else -1
    return start >= 0 and text.find(old, start + 1) < 0


def bundle(kernel, story):
    validate_result(story, len(story['qa']))
    parse_kernel(kernel)
    return {'kernel': kernel, 'title': story['title'], 'story': story['story'],
            'qa': {f'q{i:04d}': row for i, row in enumerate(story['qa'], 1)}}


def story_value(value):
    return {'title': value['title'], 'story': value['story'],
            'qa': [value['qa'][key] for key in sorted(value['qa'])]}


def validate(value):
    parse_kernel(value['kernel'])
    if not value['qa']:
        raise ValueError('QA cannot be empty')
    validate_result(story_value(value), len(value['qa']))


def apply_edits(base, edits, *, stage):
    if not isinstance(edits, list) or not edits:
        raise ValueError('expected nonempty edits')
    result = copy.deepcopy(base)
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != {'target', 'old', 'new'} or any(not isinstance(v, str) for v in edit.values()):
            raise ValueError('edit requires target/old/new strings')
        target, old, new = (edit[k] for k in ('target', 'old', 'new'))
        if old == new:
            raise ValueError('no-op edit')
        parts = target.split('/')
        if stage == 'kernel':
            if target != 'kernel':
                raise ValueError('kernel stage may only edit kernel')
            parent, key = result, target
        elif stage == 'text' and target in ('story', 'title'):
            parent, key = result, target
        elif stage == 'text' and len(parts) in (2, 3) and parts[0] == 'qa' and parts[1] and all(c.isalnum() or c in '_-' for c in parts[1]):
            qid = parts[1]
            if len(parts) == 2:
                existing = result['qa'].get(qid)
                if old:
                    if existing is None or json.loads(old) != existing:
                        raise ValueError('QA precondition mismatch')
                elif existing is not None:
                    raise ValueError('QA ID already exists')
                if new:
                    row = json.loads(new)
                    validate_result({'title': 'QA', 'story': 'QA', 'qa': [row]}, 1)
                    result['qa'][qid] = row
                else:
                    del result['qa'][qid]
                continue
            if qid not in result['qa'] or parts[2] not in ('question', 'answer'):
                raise ValueError('unknown QA target')
            parent, key = result['qa'][qid], parts[2]
        else:
            raise ValueError('unauthorized target')
        text = parent[key]
        # Count overlapping occurrences as ambiguous too.
        if not unique(text, old):
            raise ValueError(f'exact span must occur once: {target}')
        parent[key] = text.replace(old, new, 1)
    return result


def apply_pair(base, pair):
    result = apply_edits(base, pair['kernel_edits'], stage='kernel')
    parse_kernel(result['kernel'])
    result = apply_edits(result, pair['text_edits'], stage='text')
    validate(result)
    return result


def span_diff(old, new, target):
    """Conservative conversion for existing line patches; verify exact round-trip."""
    if old == new:
        return []
    edits = []
    # Right-to-left edits retain original coordinates for earlier spans.
    old_tokens, new_tokens = re.findall(r'\w+|[^\w]', old), re.findall(r'\w+|[^\w]', new)
    old_offsets, new_offsets = [0], [0]
    for token in old_tokens:
        old_offsets.append(old_offsets[-1] + len(token))
    for token in new_tokens:
        new_offsets.append(new_offsets[-1] + len(token))
    for tag, a, b, c, d in reversed(difflib.SequenceMatcher(None, old_tokens, new_tokens, autojunk=False).get_opcodes()):
        if tag == 'equal':
            continue
        a, b, c, d = old_offsets[a], old_offsets[b], new_offsets[c], new_offsets[d]
        left, right = a, b
        while not unique(old, old[left:right]):
            if left > 0:
                left -= 1
            elif right < len(old):
                right += 1
            else:
                break
        edits.append({'target': target, 'old': old[left:right],
                      'new': old[left:a] + new[c:d] + old[b:right]})
    return edits


def field_diff(old, new, target, base, stage):
    edits = span_diff(old, new, target)
    if not edits:
        return []
    try:
        changed = apply_edits(base, edits, stage=stage)
        if target in changed and changed[target] == new:
            return edits
    except ValueError:
        pass
    # Overlapping inferred contexts: safe but less composable whole-field fallback.
    return [{'target': target, 'old': old, 'new': new}]


def make_pair(base, kernel, text_edits, cue=''):
    kernel_edits = field_diff(base['kernel'], kernel, 'kernel', base, 'kernel')
    pair = {'version': 1, 'base_sha256': digest(base), 'cue': cue,
            'kernel_edits': kernel_edits, 'text_edits': text_edits}
    revised = apply_pair(base, pair)
    if revised['kernel'] != kernel:
        raise ValueError('kernel span conversion failed exact round-trip')
    if ast.dump(parse_kernel(kernel)) == ast.dump(parse_kernel(base['kernel'])):
        raise ValueError('kernel edit is an AST no-op')
    if revised['story'] == base['story']:
        raise ValueError('pair must change story')
    pair['id'] = digest(pair)
    return pair
