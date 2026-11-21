"""Canonical cached API request layout, separate from offline execution."""
from copy import deepcopy
import hashlib
import json


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def without_cache_writes(body):
    """Preserve a one-use prompt exactly, avoiding implicit cache-write fees."""
    result = deepcopy(body)
    result['prompt_cache_options'] = {'mode': 'explicit', 'ttl': '30m'}
    return result


def cached_request(body, prefix, payload, namespace):
    result = deepcopy(body)
    fingerprint = compact([prefix, body['model'], body.get('reasoning'), body.get('text')])
    result['prompt_cache_key'] = 'storyscenes:' + namespace + ':' + hashlib.sha256(fingerprint.encode()).hexdigest()[:16]
    result['prompt_cache_options'] = {'mode': 'explicit', 'ttl': '30m'}
    result['input'] = [
        {'role': 'developer', 'content': [{'type': 'input_text', 'text': prefix,
                                         'prompt_cache_breakpoint': {'mode': 'explicit'}}]},
        {'role': 'user', 'content': payload if isinstance(payload, str) else compact(payload)},
    ]
    return result


def sdk_kwargs(body):
    """SDK 2.43 lacks this top-level field; saved artifacts remain API JSON."""
    result = deepcopy(body)
    if 'prompt_cache_options' in result:
        extra = result.setdefault('extra_body', {})
        if 'prompt_cache_options' in extra:
            raise ValueError('Conflicting prompt cache transport options')
        extra['prompt_cache_options'] = result.pop('prompt_cache_options')
    return result
