"""Bounded, atomic artifact edits; no full-script replacement repair protocol."""
from copy import deepcopy
import ast
import io
import json
import re
import tokenize


def rename_key(source, old, new):
    """Rename complete state-key STRING LITERALS, including knowledge paths.

    Tokens preserve formatting and comments; code identifiers and prose remain
    unchanged. This cannot execute a model-supplied replacement expression.
    """
    if any(not re.fullmatch(r'[A-Za-z_][\w]*(?:\.[A-Za-z_]\w*)+', x) for x in (old,new)):
        raise ValueError('A state-key rename requires two dotted identifiers')
    result, count = [], 0
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.STRING:
            try: value = ast.literal_eval(token.string)
            except (ValueError, SyntaxError): value = None
            if isinstance(value,str) and (value == old or value.endswith('.knows.'+old)):
                value = value[:-len(old)] + new
                token = tokenize.TokenInfo(token.type,repr(value),token.start,token.end,token.line)
                count += 1
        result.append(token)
    if not count: raise ValueError('State-key rename target does not occur: '+old)
    return tokenize.untokenize(result)


def patch_source(source, patch):
    edits = patch['edits']
    renames = patch.get('renames',[])
    if not 1 <= len(edits)+len(renames) <= 12 or len(edits)>8 or sum(len(x['new']) for x in edits) > 14000:
        raise ValueError('Source repair exceeds patch budget')
    updated = source
    for rename in renames:
        updated = rename_key(updated,rename['old'],rename['new'])
    for edit in edits:
        old, new = edit['old'], edit['new']
        if not old or len(old) > max(500, len(source) * .75):
            raise ValueError('Repair must edit a fragment, not replace the script')
        if updated.count(old) != 1:
            raise ValueError('Repair target must match exactly once: ' + old[:150])
        updated = updated.replace(old, new, 1)
    return updated


def patch_catalog(book, patch):
    """JSON Pointer edits. Arrays append with /-, otherwise replace one item.

    Values are JSON-encoded strings in the response schema so patches can alter
    either text, conditions or whole cards without an open-ended JSON schema.
    """
    edits = patch['edits']
    if not 0 <= len(edits) <= 12 or sum(len(x['value_json']) for x in edits) > 18000:
        raise ValueError('Catalog repair exceeds patch budget')
    updated = deepcopy(book)
    for edit in edits:
        path = edit['path']
        parts = [p.replace('~1','/').replace('~0','~') for p in path.split('/')[1:]]
        if not path.startswith('/') or len(parts) < 2 or parts[0] not in book:
            raise ValueError('Repair must target individual sections/cards, not a whole catalog')
        node = updated
        for part in parts[:-1]:
            node = node[int(part)] if isinstance(node, list) else node[part]
        key = parts[-1]
        existing = (node[int(key)] if key != '-' and 0 <= int(key) < len(node) else None) if isinstance(node,list) else node.get(key)
        # The outer response is strict JSON. Inner text replacements may contain
        # literal newlines from double encoding; accepting those is data parsing,
        # not code evaluation or a change to the requested prose.
        try:
            value = json.loads(edit['value_json'], strict=False)
        except json.JSONDecodeError:
            if parts[-1] not in ('text','role','scene') and not (isinstance(existing,dict) and set(existing)=={'text','when'}):
                raise
            value = edit['value_json']  # native text for known string fields
        if isinstance(value,str) and isinstance(existing,dict) and set(existing)=={'text','when'}:
            value = dict(existing,text=value)  # text-only card edit preserves its guards
        if isinstance(node, list):
            if key != '-' and not 0 <= int(key) <= len(node):
                raise ValueError('Catalog index outside array: '+edit['path'])
            if key == '-' or int(key) == len(node): node.append(value)
            else: node[int(key)] = value
        else:
            if key not in node: raise ValueError('Unknown catalog field: ' + key)
            node[key] = value
    return updated
