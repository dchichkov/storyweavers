"""Offline conversational QA over immutable Storyscenes traces.

This is a bounded question interpreter, not an unrestricted chatbot. Answers
come from typed changes, timed facts and causal links. Optional dialogue records
also supply exact attributed prose spans; quotes are not used to infer world
state. Unsupported questions preserve focus and abstain.
"""
from __future__ import annotations

from copy import copy, deepcopy
from dataclasses import asdict, dataclass
import hashlib
import json
import random
import re
from dialogue import DialogueMixin, collect_dialogue

VERSION = 'storyscenes_conversation_v1'


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def sentence(text):
    return text[0].upper() + text[1:].rstrip('.!? ') + '.'


def normalized(text):
    return re.sub(r'\s+', ' ', text.casefold().strip().rstrip('?!.,')).replace('’', "'")


@dataclass(frozen=True)
class Focus:
    at: int
    entity: str | None = None
    key: str | None = None
    event_id: int | None = None


@dataclass(frozen=True)
class SpeechFocus(Focus):
    utterance_id: str | None = None


class Conversation(DialogueMixin):
    def __init__(self, trace, paragraphs=None):
        self.trace = deepcopy(trace)
        self.events = self.trace['events']
        self.entities = self.trace['entities']
        self.states = [self.trace['initial']] + [e['after'] for e in self.events]
        previous = self.states[0]
        for i, event in enumerate(self.events, 1):
            if event['id'] != i or event['before'] != previous:
                raise ValueError('Conversation requires a contiguous, replayed trace')
            if any(type(c) is not int or not 0 < c < i for c in event['causes']):
                raise ValueError('Invalid causal reference')
            changes = {k: {'before': previous[k], 'after': v}
                       for k, v in event['after'].items() if previous[k] != v}
            if changes != event['changes'] or set(previous) != set(event['after']):
                raise ValueError('Invalid event changes')
            if any(a not in self.entities for a in event['actors']):
                raise ValueError('Unknown event actor')
            previous = event['after']
        if not self.events or self.trace['final'] != previous:
            raise ValueError('Missing events or mismatched final state')
        if any(k.split('.')[0] not in self.entities for k in previous):
            raise ValueError('Unembedded QA fact')
        self.trace_sha256 = fingerprint(self.trace)
        self.focus = None
        self.turns = []
        self.dialogue = collect_dialogue(self.trace, paragraphs)
        self._starters = self._build_starters() + self.dialogue_starters()

    def name(self, entity):
        item = self.entities[entity]; name = item['name']
        if item['kind'] in ('prop', 'place') and name[:1].islower() and not re.match(r'^(the|a|an) ', name):
            return 'the ' + name
        return name

    def referent(self, key):
        return key.split('.knows.', 1)[-1].split('.')[0]

    def possessive(self, entity):
        name = self.name(entity)
        return name + ("'" if name.endswith('s') else "'s")

    def fact(self, key, at):
        return dict(at=at, key=key, value=deepcopy(self.states[at][key]))

    def topic(self, key):
        entity, field = key.split('.', 1)
        if field.startswith('knows.'):
            return self.topic(field[6:])
        if field == 'want': return self.possessive(entity) + ' wishes'
        if field == 'wind': return 'the weather in ' + self.name(entity)
        if field == 'owner': return self.possessive(entity) + ' holder'
        if field == 'location': return self.possessive(entity) + ' location'
        labels = {'condition': 'condition', 'cover': 'cover', 'latch': 'latch',
                  'open': 'opening', 'ready': 'readiness', 'response': 'response',
                  'performance_style': 'performance', 'on': 'light', 'glow': 'glow',
                  'brightness': 'light', 'position': 'position', 'content': 'feelings',
                  'invited': 'invitation', 'delivered': 'delivery', 'tied': 'fastening',
                  'attached': 'attachment', 'ribboned': 'ribbons', 'promise': 'promise',
                  'performed.mode': 'performance'}
        return self.possessive(entity) + ' ' + labels[field] if field in labels else None

    def clause(self, key, value, *, at):
        """Render supported typed facts. Unknown enums/fields have no raw fallback."""
        entity, field = key.split('.', 1)
        name = self.name(entity)
        if field.startswith('knows.'):
            source = field[6:]
            if source not in self.states[at]: return None
            topic = self.topic(source)
            if value is None:
                target, attr = source.split('.', 1)
                questions = {'want': f'what {self.name(target)} wanted',
                             'owner': f'who had {self.name(target)}',
                             'location': f'where {self.name(target)} was',
                             'wind': f'what the weather in {self.name(target)} was like',
                             'condition': f'what condition {self.name(target)} was in'}
                if attr in questions: return f'{name} did not yet know {questions[attr]}'
                return f'{name} had not yet learned about {topic}' if topic else None
            content = self.clause(source, value, at=at)
            return f'{name} believed that {content}' if content else None
        if field in ('owner', 'location', 'position', 'loaned_by'):
            if value not in self.entities: return None
            if field in ('location','position'): return f'{name} was at {self.name(value)}'
            if field == 'loaned_by': return f'{name} was on loan from {self.name(value)}'
            return f'{self.name(value)} had {name}'
        if field == 'want' and isinstance(value, str):
            wishes = {'quiet': 'some quiet', 'join': 'to join in', 'signal': 'a signal'}
            if value in wishes: return f'{name} wanted {wishes[value]}'
            if not re.fullmatch(r"[A-Za-z][A-Za-z '\-]{0,100}", value): return None
            verbs = {'make', 'start', 'keep', 'deliver', 'help', 'join', 'protect',
                     'build', 'carry', 'read', 'learn', 'tell', 'play', 'invite',
                     'welcome', 'enjoy', 'give', 'find', 'get', 'have', 'be'}
            return f'{name} wanted {"to " if value.split()[0] in verbs else ""}{value}'
        if field == 'wind' and value in ('breezy', 'still', 'windy', 'calm'):
            return f'the air in {name} was {value}'
        if field == 'condition' and value in ('damaged', 'broken', 'ready', 'repaired', 'stuck', 'sturdy', 'fragile', 'torn', 'whole'):
            return f'{name} was {value}'
        if field == 'cover' and value in ('loose', 'tied', 'secured'):
            return f'{self.possessive(entity)} cover was {"tied down" if value == "tied" else value}'
        if field == 'latch' and value in ('left', 'right', 'up', 'down'):
            return f'{self.possessive(entity)} latch pointed {value}'
        if field in ('open', 'ready', 'stuck', 'damaged', 'sleeping', 'willing') and type(value) is bool:
            return f'{name} was {"" if value else "not "}{field}'
        if field in ('invited','delivered','tied','attached','ribboned') and type(value) is bool:
            if field == 'delivered' and self.entities[entity]['kind'] != 'prop': return None
            phrases={'invited':'invited','delivered':'delivered','tied':'tied in place',
                     'attached':'attached','ribboned':'tied with ribbons'}
            return f'{name} had {"" if value else "not "}been {phrases[field]}'
        if field == 'promise' and type(value) is bool:
            return f'{name} had {"" if value else "not "}made a promise'
        if field == 'on' and type(value) is bool:
            return f'{name} was switched {"on" if value else "off"}'
        if field in ('glow','brightness') and value in ('soft', 'bright', 'amber', 'off'):
            return f'{self.possessive(entity)} light was {value}'
        if field == 'performance_style' and value in ('gentle', 'soft', 'bright', 'quiet', 'loud'):
            return f'{self.possessive(entity)} performance was {value}'
        if field == 'performed.mode':
            modes={'tableau':'a still scene','song':'a song','shadow':'a shadow show','whisper':'a quiet performance'}
            if value in modes: return f'{name} had put on {modes[value]}'
        if field == 'content' and self.entities[entity]['kind'] not in ('prop','place') and value in ('shy','welcomed','happy','safe','content','pleased','scared'):
            return f'{name} felt {value}'
        if field == 'response':
            responses = {'grateful': 'felt grateful', 'delighted': 'was delighted',
                         'relieved': 'felt relieved', 'proud': 'felt proud',
                         'joined': 'joined in', 'join': 'joined in',
                         'watched': 'watched', 'smiles and listens': 'smiled and listened',
                         'smiled': 'smiled', 'cheering': 'cheered'}
            if value in responses: return f'{name} {responses[value]}'
        return None

    def changed(self, event):
        return [(k, self.clause(k, v['after'], at=event['id']))
                for k, v in event['changes'].items()]

    def event_description(self, event):
        """Return text, focus key and exact fact citations, or unsupported."""
        at = event['id']; before = at - 1; actors = event['actors']
        for key, change in event['changes'].items():
            entity, field = key.split('.', 1)
            if field.startswith('knows.') and event['kernel'] in ('Observe', 'Tell'):
                source = field[6:]; value = change['after']
                content = self.clause(source, value, at=before)
                if not content: continue
                if event['kernel'] == 'Observe':
                    if self.states[before].get(source) != value: continue
                    text = f'{self.name(entity)} found out that {content}'
                    facts = [self.fact(source, before), self.fact(key, at)]
                else:
                    if len(actors) != 2 or entity != actors[1]: continue
                    speaker_key = actors[0] + '.knows.' + source
                    if self.states[before].get(speaker_key) != value: continue
                    text = f'{self.name(actors[0])} told {self.name(entity)} that {content}'
                    facts = [self.fact(speaker_key, before), self.fact(key, at)]
                return text, key, facts
            if (field == 'owner' and event['kernel'] == 'Transfer'
                    and actors == [change['before'], change['after']]
                    and change['before'] in self.entities and change['after'] in self.entities):
                giver, receiver = change['before'], change['after']; loan = entity + '.loaned_by'
                facts = [self.fact(key, before), self.fact(key, at)]
                verb = 'gave'
                if self.states[at].get(loan) == giver and self.states[before].get(loan) is None:
                    verb = 'lent'; facts += [self.fact(loan, before), self.fact(loan, at)]
                elif self.states[before].get(loan) == receiver and self.states[at].get(loan) is None:
                    verb = 'returned'; facts += [self.fact(loan, before), self.fact(loan, at)]
                return f'{self.name(giver)} {verb} {self.name(entity)} to {self.name(receiver)}', key, facts
            if field == 'location' and change['before'] in self.entities and change['after'] in self.entities:
                # Object movement does not imply the actor moved too.
                return (f'{self.name(entity)} moved from {self.name(change["before"])} to {self.name(change["after"])}',
                        key, [self.fact(key, before), self.fact(key, at)])
        for key, text in self.changed(event):
            if text and '.knows.' not in key:
                return text, key, [self.fact(key, at)]
        return None

    def _build_starters(self):
        starters = []
        for event in self.events:
            description = self.event_description(event)
            if not description: continue
            _, key, _ = description; entity, field = key.split('.', 1)
            topic_entity = self.referent(key)
            focus = Focus(event['id'], topic_entity, key, event['id'])
            if event['kernel'] in ('Observe', 'Tell') and field.startswith('knows.'):
                topic = self.topic(field[6:])
                if not topic: continue
                if event['kernel'] == 'Observe':
                    source = field[6:]
                    if source.endswith('.owner'):
                        question = f'Who did {self.name(entity)} find out had {self.name(source.split(".")[0])}?'
                    else: question = f'What did {self.name(entity)} find out about {topic}?'
                else:
                    question = f'What did {self.name(event["actors"][0])} tell {self.name(entity)} about {topic}?'
                kind = 'knowledge'
            elif field == 'owner' and event['kernel'] == 'Transfer' and event['actors'] == [event['before'][key], event['after'][key]]:
                giver = event['before'][key]; receiver = event['after'][key]
                verb = 'give'
                loan = entity + '.loaned_by'
                if event['after'].get(loan) == giver: verb = 'lend'
                elif event['before'].get(loan) == receiver: verb = 'return'
                question = f'Who did {self.name(giver)} {verb} {self.name(entity)} to?'
                kind = 'ownership'
            elif field == 'location' and event['before'][key] in self.entities:
                question = f'Where did {self.name(entity)} go from {self.name(event["before"][key])}?'
                kind = 'location'
            else:
                topic = self.topic(key)
                if not topic: continue
                question = f'How did {topic} change?'; kind = 'change'
            starters.append(dict(question=question, kind=kind, focus=asdict(focus), mode='event'))
        for entity in self.entities:
            for field, kind, template in (
                    ('want', 'desire', 'What did {} want at the start?'),
                    ('owner', 'ownership', 'Who had {} at the end?'),
                    ('location', 'location', 'Where was {} at the end?')):
                key = entity + '.' + field; at = 0 if field == 'want' else len(self.events)
                if field == 'location' and self.last_writer(key, at) is None: continue
                if key in self.states[at] and self.clause(key, self.states[at][key], at=at):
                    starters.append(dict(question=template.format(self.name(entity)), kind=kind,
                        focus=asdict(Focus(at, entity, key, self.last_writer(key, at))), mode='state'))
        # Repeated descriptions need a disambiguating turn; do not silently pick one.
        counts = {}
        for row in starters: counts[normalized(row['question'])] = counts.get(normalized(row['question']), 0) + 1
        return [row for row in starters if counts[normalized(row['question'])] == 1]

    def starters(self):
        return deepcopy(self._starters)

    def last_writer(self, key, at):
        return next((e['id'] for e in reversed(self.events[:at]) if key in e['changes']), None)

    def context_fact(self, focus, excluded):
        keys = [focus.entity + suffix for suffix in ('.loaned_by', '.location', '.owner', '.condition')]
        for key in keys:
            if key in excluded or key not in self.states[focus.at]: continue
            if key.endswith('.location') and focus.at > 0 and self.last_writer(key, focus.at) is None:
                # Don't add a stale static location as incidental color. A
                # direct location question still answers the exact model state.
                continue
            text = self.clause(key, self.states[focus.at][key], at=focus.at)
            if text: return text, self.fact(key, focus.at)
        return None

    def state_answer(self, focus):
        text = self.clause(focus.key, self.states[focus.at][focus.key], at=focus.at)
        if not text: return None
        parts = [sentence(text)]; facts = [self.fact(focus.key, focus.at)]
        context = self.context_fact(focus, {focus.key})
        if context:
            parts.append(sentence('At that point, ' + context[0])); facts.append(context[1])
        elif focus.at and self.states[0][focus.key] != self.states[focus.at][focus.key]:
            prior = self.clause(focus.key, self.states[0][focus.key], at=0)
            if prior: parts.append(sentence('At the start, ' + prior)); facts.append(self.fact(focus.key, 0))
        return ' '.join(parts), facts, []

    def event_answer(self, focus):
        event = self.events[focus.event_id - 1]; item = self.event_description(event)
        if not item: return None
        text, key, facts = item; parts = [sentence(text)]
        if '.knows.' in key:
            old = self.clause(key, event['before'][key], at=event['id'] - 1)
            if old: parts.append(sentence('Before that, ' + old)); facts.append(self.fact(key, event['id'] - 1))
        else:
            context = self.context_fact(focus, {f['key'] for f in facts})
            if context:
                parts.append(sentence('At that point, ' + context[0])); facts.append(context[1])
            elif key in event['changes']:
                old = self.clause(key, event['before'][key], at=event['id'] - 1)
                if old: parts.append(sentence('Before that, ' + old)); facts.append(self.fact(key, event['id'] - 1))
        return ' '.join(parts), facts, [event['id']]

    def causal_answer(self, focus):
        if focus.event_id is None: return None
        event = self.events[focus.event_id - 1]
        clauses = []; facts = []
        # Prefer actual changing prerequisites; no unrecorded motives or guessed goals.
        changing = {k for c in event['causes'] for k in self.events[c - 1]['changes']}
        guards = sorted(event['requires'], key=lambda c: c['key'] not in changing)
        for guard in guards:
            key = guard['key']; value = event['before'][key]
            if key in {f['key'] for f in facts} or value is None: continue
            text = self.clause(key, value, at=event['id'] - 1)
            if text:
                clauses.append(text); facts.append(self.fact(key, event['id'] - 1))
            if len(clauses) == 2: break
        if not clauses: return None
        answer = sentence('That was possible because ' + ' and '.join(clauses))
        # Explain a distinct enabling action when the direct causal history has one.
        for cause in event['causes']:
            parent = self.events[cause - 1]; item = self.event_description(parent)
            if item and parent['kernel'] in ('Observe', 'Tell', 'Transfer'):
                answer += ' ' + sentence('Earlier, ' + item[0])
                facts += item[2]
                break
            relevant = set(parent['changes']) & {g['key'] for g in event['requires']}
            previous = next(((key, self.clause(key,parent['before'][key],at=cause-1))
                             for key in sorted(relevant)
                             if self.clause(key,parent['before'][key],at=cause-1)), None)
            if previous:
                answer += ' ' + sentence('Before that change, ' + previous[1])
                facts.append(self.fact(previous[0],cause-1))
                break
        return answer, facts, [event['id'], *event['causes']]

    def truth_answer(self, focus):
        if not focus.key or '.knows.' not in focus.key: return None
        source = focus.key.split('.knows.', 1)[1]
        belief = self.states[focus.at][focus.key]; actual = self.states[focus.at].get(source)
        if belief is None: return None
        content = self.clause(source, actual, at=focus.at)
        if not content: return None
        answer = ('Yes. ' if type(actual) is type(belief) and actual == belief else 'No. ')
        answer += sentence('At that point, ' + content)
        facts = [self.fact(focus.key, focus.at), self.fact(source, focus.at)]
        origin = self.source_answer(focus, short=True)
        if origin:
            return answer + ' ' + origin[0], facts + origin[1], origin[2]
        if actual != belief: answer += ' The belief and the actual situation were different.'
        return answer, facts, []

    def source_answer(self, focus, *, short=False):
        if not focus.key or '.knows.' not in focus.key: return None
        writer = self.last_writer(focus.key, focus.at)
        if writer is None: return None
        event = self.events[writer - 1]
        if event['kernel'] not in ('Observe', 'Tell'): return None
        item = self.event_description(event)
        if not item: return None
        key = focus.key; source = key.split('.knows.', 1)[1]
        knower = key.split('.')[0]; topic = self.topic(source)
        if event['kernel'] == 'Tell':
            text = f'{self.name(knower)} heard it from {self.name(event["actors"][0])}'
        else:
            text = f'{self.name(knower)} found out by checking {topic}'
        return sentence(text) + ('' if short else ' ' + sentence(item[0])), item[2], [writer]

    def contributor_answer(self, focus):
        if focus.event_id is None: return None
        event = self.events[focus.event_id - 1]
        for cause in reversed(event['causes']):
            parent = self.events[cause - 1]
            # Describe a recorded contribution, not a guessed helpful intention.
            if parent['kernel'] not in ('Tell', 'Transfer'): continue
            if len(parent['actors']) != 2 or parent['actors'][1] not in event['actors']: continue
            item = self.event_description(parent)
            if item:
                text, key, facts = item
                result = sentence(text)
                consequence = self.event_description(event)
                if consequence:
                    result += ' ' + sentence('Afterward, ' + consequence[0])
                    facts += consequence[2]
                return result, facts, [cause, event['id']]
        return None

    def _reply(self, question, kind, focus, answer=None, reason=None):
        if answer:
            text, facts, events = answer
            seen = set(); unique = []
            for fact in facts:
                sig = json.dumps(fact, sort_keys=True)
                if sig not in seen: unique.append(fact); seen.add(sig)
            entities = {f['key'].split('.')[0] for f in unique}
            entities |= {f['value'] for f in unique if isinstance(f['value'], str) and f['value'] in self.entities}
            if focus.entity: entities.add(focus.entity)
            row = dict(question=question, answer=text, kind=kind, answerable=True,
                       event_ids=sorted(set(events) | {f['at'] for f in unique if f['at']}),
                       entity_ids=sorted(entities), facts=unique, focus=asdict(focus),
                       source='world_trace')
            self.focus = focus
        else:
            text = reason or "This story doesn't tell us enough to answer that. I don't want to make up a reason or an extra event."
            row = dict(question=question, answer=text, kind=kind, answerable=False,
                       event_ids=[], entity_ids=[], facts=[],
                       focus=asdict(self.focus) if self.focus else None, source='world_trace')
        self.turns.append(deepcopy(row))
        return row

    def ask(self, question):
        query = normalized(question)
        matches = [s for s in self._starters if normalized(s['question']) == query]
        if matches:
            starter = matches[0]
            if starter['mode'] == 'dialogue':
                record = self.speech_record(SpeechFocus(**starter['focus']))
                return self.speech_reply(question, 'dialogue', record)
            focus = Focus(**starter['focus'])
            answer = self.event_answer(focus) if starter['mode'] == 'event' else self.state_answer(focus)
            return self._reply(question, starter['kind'], focus, answer)
        dialogue_reply = self.ask_dialogue(question)
        if dialogue_reply is not None: return dialogue_reply
        focus = self.focus
        if focus is None:
            return self._reply(question, 'clarification', focus,
                               reason='Which part of the story do you mean? Pick a question to begin our conversation.')
        if query in ('why', 'why was that possible', 'how was that possible'):
            # A desire question asks about motives, not about a later event's prerequisites.
            answer = None if focus.key and focus.key.endswith('.want') else self.causal_answer(focus)
            return self._reply(question, 'causal', focus, answer)
        if query in ('was that true', 'is that true', 'was that right'):
            return self._reply(question, 'belief_check', focus, self.truth_answer(focus))
        if query in ('how did they know', 'how did she know', 'how did he know', 'how did they find out'):
            return self._reply(question, 'knowledge_source', focus, self.source_answer(focus))
        if query in ('who helped', 'who helped with that'):
            return self._reply(question, 'contributor', focus, self.contributor_answer(focus))
        if query in ('what happened next', 'and then', 'then what', 'what happened before that'):
            delta = -1 if query == 'what happened before that' else 1
            at = focus.at + delta
            if at <= 0 or at > len(self.events):
                reason = ("That's where this story ends. It doesn't say what happened afterward." if delta == 1
                          else "That's the beginning of this story. It doesn't tell us what happened earlier.")
                return self._reply(question, 'boundary', focus, reason=reason)
            event = self.events[at - 1]; item = self.event_description(event)
            if not item: return self._reply(question, 'timeline', focus)
            key = item[1]; target = Focus(at, self.referent(key), key, at)
            return self._reply(question, 'timeline', target, self.event_answer(target))
        if query in ('where was it', 'where was that', 'where were they', 'where was she', 'where was he',
                     'who had it', 'who had it before that', 'where was it before that'):
            field = 'location' if query.startswith('where') else 'owner'
            at = focus.at - 1 if query.endswith('before that') else focus.at
            entity = focus.entity
            if query in ('where were they','where was she','where was he'):
                if focus.key and '.knows.' in focus.key: entity = focus.key.split('.')[0]
                if self.entities[entity]['kind'] in ('prop','place'):
                    return self._reply(question,'clarification',focus,reason='Which person do you mean?')
            key = f'{entity}.{field}'
            if at < 0 or key not in self.states[at]: return self._reply(question, field, focus)
            target = Focus(at, entity, key, self.last_writer(key, at))
            return self._reply(question, 'location' if field == 'location' else 'ownership', target, self.state_answer(target))
        return self._reply(question, 'unsupported', focus,
                           reason="I can't resolve that question reliably yet. Try asking why, where it was, who had it, or what happened next.")


def conversations_from_trace(trace, *, seed=0, limit=6, pairs=3, paragraphs=None):
    """Balanced, reproducible conversations; selection never changes the story."""
    if limit < 1 or not 2 <= pairs <= 5: raise ValueError('Need a positive limit and two to five QA pairs')
    prototype = Conversation(trace, paragraphs); candidates = prototype.starters(); rng = random.Random(seed)
    rng.shuffle(candidates)
    # Round-robin kinds before sampling another of the same kind.
    groups = {}
    for row in candidates: groups.setdefault(row['kind'], []).append(row)
    ordered = []
    while any(groups.values()):
        for group in groups.values():
            if group: ordered.append(group.pop())
    results = []
    for starter in ordered:
        dialog = Conversation(trace, paragraphs); dialog.ask(starter['question'])
        nodes = 0
        def extend(current, used):
            nonlocal nodes
            nodes += 1
            if len(current.turns) == pairs or nodes > 128: return current
            person = current.entities[current.focus.entity]['kind'] not in ('prop', 'place')
            options = ['Why?', 'What happened next?', 'Where were they?' if person else 'Where was it?', 'Who had it?',
                       'How did they know?', 'Was that true?', 'What happened before that?', 'Who helped?']
            if current.speech_record():
                # The starter answer already identifies the speaker/listener.
                # Sample a new fact instead of re-asking those identities.
                options = ['Why did they say that?',
                           'What was said next?', 'What did they reply?', 'Was that true?', 'What happened next?',
                           'How did they know?']
            rng.shuffle(options); best = current; boundaries = []
            for question in options:
                if normalized(question) in used: continue
                # The trace is read-only; branch only the conversation's focus/history.
                probe = copy(current); probe.turns = deepcopy(current.turns)
                answer = probe.ask(question)
                if answer['answerable'] and answer['answer'] not in [t['answer'] for t in current.turns]:
                    candidate = extend(probe, used | {normalized(question)})
                    if len(candidate.turns) > len(best.turns): best = candidate
                    if len(best.turns) == pairs: return best
                elif answer['kind'] == 'boundary': boundaries.append(probe)
                if nodes > 128: break
            if len(best.turns) == len(current.turns) and boundaries: return boundaries[0]
            return best
        dialog = extend(dialog, {normalized(starter['question'])})
        if len(dialog.turns) < 2: continue
        results.append(dict(id=f'c{len(results):03d}', protocol=VERSION, trace_sha256=dialog.trace_sha256,
                            turns=deepcopy(dialog.turns)))
        if len(results) == limit: break
    return results
