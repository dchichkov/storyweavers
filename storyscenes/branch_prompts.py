"""Render branch starting conditions offline; never inspect story text or outcomes."""
import re

VERSION = 'initial_branch_v1'


def branch_prompt(spec, source):
    trace = source['trace']
    entities, initial = trace['entities'], trace['initial']

    def name(entity):
        item = entities[entity]
        value = item['name']
        return 'the ' + value if item['kind'] in ('place', 'prop') and value[0].islower() and not value.startswith('the ') else value

    def words(value):
        if not isinstance(value, str) or not re.fullmatch(r"[\w '’,-]+", value):
            raise ValueError(f'Needs an authored prompt phrase: {value!r}')
        return value.replace('_', ' ')

    def clause(key, value):
        entity, field = key.split('.', 1)
        subject = name(entity)
        if field.startswith('knows.'):
            return f'{subject} knows that ' + clause(field[6:], value)
        if field in ('location', 'listener'):
            return f'{subject} is at {name(value)}' if field == 'location' else f'{subject} has {name(value)} as a listener'
        if field in ('wind', 'weather', 'garden.wind'):
            return f'the weather at {subject} is {words(value)}'
        if field == 'capacity' and type(value) is int:
            return f'{subject} can carry only {value} item' + ('s' if value != 1 else '') + ' at a time'
        if field == 'want':
            wishes = {'quiet': 'some quiet', 'join': 'to join in', 'ask_questions': 'to ask questions',
                      'ask questions': 'to ask questions', 'needs_rest': 'to rest', 'safe_shadow': 'a safe shadow',
                      'careful': 'to be careful', 'curious': 'to explore', 'gift': 'a gift', 'lesson': 'a lesson',
                      'map': 'a map', 'notice': 'to be noticed', 'recipe': 'a recipe', 'story': 'a story',
                      'warm': 'to be warm', 'biggest parade': 'to make the biggest parade',
                      'bright welcome': 'a bright welcome', 'quiet welcome': 'a quiet welcome',
                      'quiet town': 'a quiet town', 'plain bun': 'a plain bun'}
            val = wishes.get(value, words(value))
            if val.split()[0] in ('help', 'share', 'watch', 'listen', 'dance', 'trade', 'hear', 'guard', 'keep'):
                val = 'to ' + val
            return f'{subject} wants {val}'
        if field in ('fragile', 'intact', 'secured', 'shy', 'sleeping', 'paper', 'tied') and type(value) is bool:
            description = {'paper': 'made of paper', 'secured': 'secured', 'tied': 'tied in place'}.get(field, field)
            return f'{subject} is ' + ('' if value else 'not ') + description
        if field in ('text', 'label', 'label_text', 'labeled_as', 'marked_flavor'):
            label = value.split('=', 1)[1] if isinstance(value, str) and value.startswith('pie=') else words(value)
            return f'{subject} ' + ('reads' if field == 'text' else 'is labeled') + f' “{label}”'
        if field == 'performance_style':
            forms = {'wide_wings': 'plans to use wide wings', 'careful_tail': 'plans to use a careful tail',
                     'gentle_whistle': 'plans to whistle gently', 'rhythm': 'plans a rhythmic performance',
                     'whispering': 'plans to whisper', 'booming': 'plans a booming performance'}
            return subject + ' ' + forms.get(value, f'plans a {words(value)} performance')
        if field == 'rule':
            rule = {'ask_first': 'ask first', 'show_signal': 'show a signal'}.get(value, words(value))
            return f'{subject} has this rule: “{rule}”'
        if field == 'actual_kind':
            return f'{subject} is actually the {words(value)} kind'
        if field in ('flavor', 'taste'):
            return f'{subject} has a {words(value)} flavor'
        if field == 'preference':
            return f'{subject} prefers {words(value)}'
        if field == 'need':
            return f'{subject} needs ' + {'join': 'to join in', 'quiet': 'some quiet'}.get(value, words(value))
        if field in ('condition', 'mood', 'issue', 'wheel_condition', 'teacup_condition'):
            target = subject if field in ('condition', 'mood', 'issue') else subject + "'s " + field.split('_')[0]
            return f'{target} is {words(value)}'
        if field in ('length', 'light', 'shadows', 'signal', 'sign', 'volume', 'water', 'wheel', 'wheels', 'glow'):
            return f'{subject} has ' + f'{field}: {words(value)}'
        if field in ('memes.Care', 'memes.Pride', 'pride', 'proud', 'confidence', 'trust', 'comfort'):
            if isinstance(value, str):
                return f'{subject} feels {words(value)}'
            # Trait magnitudes are intentionally described qualitatively, not as implementation parameters.
            trait = {'memes.Care': 'caring', 'memes.Pride': 'proud', 'pride': 'proud', 'proud': 'proud',
                     'confidence': 'confident', 'trust': 'trusting', 'comfort': 'comfortable'}[field]
            degrees = {0: 'not at all ', 1: 'a little ', 2: 'fairly ', 3: 'very '}
            if type(value) is not int or value not in degrees: raise ValueError('Unsupported trait magnitude')
            return f'{subject} feels ' + degrees[value] + trait
        if field in ('heat', 'scraps', 'tears') and type(value) is int:
            if field == 'heat': return f'{subject} gives off ' + ('a little heat' if value <= 1 else 'a lot of heat')
            noun = 'scrap' if field == 'scraps' else 'tear'
            return f'{subject} has {value} {noun}' + ('s' if value != 1 else '')
        raise ValueError(f'No natural-language prompt renderer for {key}={value!r}')

    facts = []
    for key, value in trace['premise'].items():
        if key not in initial or type(initial[key]) is not type(value) or initial[key] != value:
            raise ValueError('Prompt condition disagrees with initial state: ' + key)
        phrase = clause(key, value)
        facts.append(dict(key=key, value=value, text=phrase[0].upper() + phrase[1:] + '.'))
    if not facts:
        raise ValueError('Branch has no explicit starting conditions')
    prompt = ('Write a short children’s story with this premise:\n' + spec['premise'] +
              '\n\nIn this version, start with these circumstances:\n' + ' '.join(f['text'] for f in facts))
    return prompt, dict(protocol=VERSION, source='trace.premise checked against trace.initial', facts=facts,
                        scope='starting conditions; does not specify every event or reveal the ending')
