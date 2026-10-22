"""Quoted speech records and bounded dialogue QA.

Authored annotations are preferred. The legacy importer accepts only adjacent,
explicit NAME + speech-verb attributions; it never resolves narrator pronouns or
infers a motive, claim, listener, or reply from proximity. Quotes remain data.
"""
from copy import deepcopy
import re


QUOTES = re.compile(r'“([^“”]+)”|"([^"\n]+)"')
SPEECH_VERBS = r'(?:said|asked|replied|whispered|shouted|cried|announced|called|murmured|explained|added|told)'


def quoted(record):
    return ' … '.join('“' + span['text'] + '”' for span in record['quotes'])


def spoken(record, name):
    return (f'{quoted(record)} said {name}.' if record['quotes'][-1]['text'].endswith(',')
            else f'{name} said, {quoted(record)}')


def collect_dialogue(trace, paragraphs):
    """Build immutable span-backed records. Bad authored evidence fails closed."""
    entities = trace['entities']; events = trace['events']; records = []
    names = {}
    for key, entity in entities.items(): names.setdefault(entity['name'], []).append(key)
    names = {name: keys[0] for name, keys in names.items() if len(keys) == 1}
    name_pattern = '|'.join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    if not name_pattern: return []
    subject = '(?P<speaker>' + name_pattern + ')'
    recipient = '(?P<listener>' + name_pattern + ')'
    attribution = subject + r'\s+(?:told\s+' + recipient + '|' + SPEECH_VERBS + ')'
    prefix = re.compile(r'(?:^|[.!?][”"]?\s+)' + attribution + r'\s*[,：:]\s*$')
    suffix = re.compile(r'\s*[,—]?\s*' + attribution + r'(?=\s|[,.!?]|$)')
    for pi, paragraph in enumerate(paragraphs or []):
        text = paragraph['text']; cited = paragraph.get('event_ids', [])
        if any(type(i) is not int or not 1 <= i <= len(events) for i in cited):
            raise ValueError('Invalid dialogue paragraph event')
        matches = list(QUOTES.finditer(text))
        spans = [dict(start=m.start()+1, end=m.end()-1, text=m.group(1) or m.group(2)) for m in matches]
        annotations = paragraph.get('dialogue')
        explicit = []
        if annotations is not None:
            explicit = collect_dialogue(trace,[{k:v for k,v in paragraph.items() if k != 'dialogue'}])
        if annotations is None:
            annotations = []
            consumed = set()
            for qi, (match, span) in enumerate(zip(matches, spans)):
                if qi in consumed: continue
                left = text[:match.start()]; right = text[match.end():]
                pre = prefix.search(left); post = suffix.match(right)
                if post and qi+1 < len(matches) and span['text'].endswith(('.', '!', '?')):
                    gap = text[match.end():matches[qi+1].start()]
                    if re.fullmatch(r'\s*' + attribution + r'\s*,\s*',gap):
                        # “A parade!” Mara whispered, “It needs feet.” The first
                        # exclamation may belong to someone else; index only the
                        # next explicitly introduced quote, not a merged speech.
                        post = None
                # A leading attribution owns its quote. A following named speech
                # may start the NEXT quote: Ada said, “Hi.” Ben said, “Hello.”
                if pre and post and pre.group('speaker') != post.group('speaker'): post = None
                attribution_match = pre or post
                if not attribution_match: continue
                speaker = names[attribution_match.group('speaker')]
                listener_name = attribution_match.groupdict().get('listener')
                item = dict(speaker=speaker, listener=names.get(listener_name), quotes=[span],
                            attribution='explicit_name')
                # One interrupted utterance: “Quiet,” Ada said, “is her wish.”
                if post and qi+1 < len(matches):
                    gap = text[match.end():matches[qi+1].start()]
                    if re.fullmatch(r'\s*[,—]?\s*' + attribution + r'\s*[,.:]\s*', gap):
                        item['quotes'].append(spans[qi+1]); consumed.add(qi+1)
                    elif re.match(r'\s*[,—]?\s*' + attribution + r'\s*,',gap) and not re.search(r'[.!?]',gap):
                        # An unsupported interrupted clause could change speakers.
                        # Don't turn just the vocative (“Tomas,”) into an answer.
                        continue
                annotations.append(item)
        local = []
        for entry in annotations:
            item = deepcopy(entry); speaker = item['speaker']; listener = item.get('listener')
            if speaker not in entities or (listener is not None and listener not in entities):
                raise ValueError('Unknown dialogue participant')
            if not item.get('quotes'): raise ValueError('Dialogue needs an exact quote')
            validated = []
            for span in item['quotes']:
                start, end = span['start'], span['end']
                if type(start) is not int or type(end) is not int:
                    raise ValueError('Invalid quote offsets')
                match = next((s for s in spans if s['start']==start and s['end']==end), None)
                if match is None or ('text' in span and span['text'] != match['text']):
                    raise ValueError('Quote is not an exact spoken span')
                if validated and start <= validated[-1]['end']: raise ValueError('Overlapping dialogue spans')
                validated.append(match)
            if local and validated[0]['start'] <= local[-1]['quotes'][-1]['end']:
                raise ValueError('Dialogue records must follow nonoverlapping text order')
            for known in explicit:
                if any(a['start']==b['start'] for a in validated for b in known['quotes']):
                    if speaker != known['speaker'] or (known['listener'] is not None and listener != known['listener']):
                        raise ValueError('Authored speaker/listener contradicts the explicit attribution')
            event_id = item.get('event_id')
            if event_id is None:
                # Explicit Tell participants can identify an event within a bridge.
                candidates = [i for i in cited if events[i-1]['kernel']=='Tell'
                              and events[i-1]['actors']==[speaker, listener]] if listener else []
                if not candidates and len(cited)==1 and speaker in events[cited[0]-1]['actors']:
                    candidates = cited
                if len(candidates)==1: event_id = candidates[0]
            if event_id is not None and (type(event_id) is not int or event_id not in cited
                                        or speaker not in events[event_id-1]['actors']):
                raise ValueError('Dialogue event must cite its physical speaker')
            reason_keys = item.get('reason_keys', [])
            if reason_keys and event_id is None: raise ValueError('Dialogue reasons need a precise event')
            for key in reason_keys:
                event = events[event_id-1]
                if (key not in event['before'] or key not in {c['key'] for c in event['requires']}
                        or not (key == speaker+'.want' or key.startswith(speaker+'.knows.'))
                        or event['before'][key] is None):
                    raise ValueError('Dialogue reason must be a recorded speaker motive or belief prerequisite')
            claim = item.get('claim')
            if claim is not None:
                if (event_id is None or not {'key','value'} <= set(claim) or set(claim)-{'key','value','at'}
                        or claim.get('at','before') not in ('before','after') or claim['key'] not in events[event_id-1]['before']
                        or '.knows.' in claim['key'] or type(claim['value']) not in (str,bool,int,float)):
                    raise ValueError('Invalid dialogue claim')
            reply_to = item.get('reply_to')
            if reply_to is not None and (type(reply_to) is not int or not 0 <= reply_to < len(local)):
                raise ValueError('Reply must reference an earlier utterance in the same paragraph')
            if reply_to is not None and local[reply_to]['listener'] not in (None,speaker):
                raise ValueError('Reply speaker is not the addressed listener')
            record = dict(id=f'u{pi}:{len(local)}', paragraph=pi, speaker=speaker, listener=listener,
                          quotes=validated, event_ids=list(cited), event_id=event_id,
                          at=event_id or max(cited, default=0), reason_keys=reason_keys, claim=claim,
                          reply_to=local[reply_to]['id'] if reply_to is not None else None,
                          attribution=item.get('attribution','authored'))
            local.append(record)
        records += local
    return records


class DialogueMixin:
    """Conversation extension; a speech focus is separate from a belief focus."""
    def speech_focus(self, record):
        # Local import avoids a module cycle with Conversation's shared Focus.
        from conversation import SpeechFocus
        return SpeechFocus(record['at'], record['speaker'], None, record['event_id'], record['id'])

    def speech_record(self, focus=None):
        uid = getattr(focus or self.focus, 'utterance_id', None)
        return next((u for u in self.dialogue if u['id']==uid), None)

    def dialogue_starters(self):
        from dataclasses import asdict
        result = []
        for record in self.dialogue:
            peers = [u for u in self.dialogue if u['speaker']==record['speaker']]
            target = self.name(record['speaker'])
            if len(peers)==1: question = f'What did {target} say?'
            else: question = f'What did {target} say in speech {peers.index(record)+1}?'
            result.append(dict(question=question,kind='dialogue',focus=asdict(self.speech_focus(record)),mode='dialogue'))
        return result

    def speech_reply(self, question, kind, record, text=None, facts=(), events=(), extra=()):
        if text is None:
            text = spoken(record,self.name(record['speaker']))
            if record['listener']:
                text += f' {self.name(record["speaker"])} was speaking to {self.name(record["listener"])}.'
        if not re.search(r'[.!?][”"]?$', text): text += '.'
        focus = self.speech_focus(record)
        turn = self._reply(question,kind,focus,(text,list(facts),list(events)))
        evidence = [record, *extra]
        turn['utterances'] = deepcopy(evidence)
        turn['source'] = 'story_dialogue'
        turn['entity_ids'] = sorted(set(turn['entity_ids']) | {u[k] for u in evidence for k in ('speaker','listener') if u[k]})
        self.turns[-1] = deepcopy(turn)
        return turn

    def dialogue_reason(self, question, record):
        from conversation import sentence
        event = self.events[record['event_id']-1] if record['event_id'] else None
        facts = []; clauses = []
        if event:
            for key in record['reason_keys']:
                clause = self.clause(key,event['before'][key],at=event['id']-1)
                if clause: clauses.append(clause); facts.append(self.fact(key,event['id']-1))
        if clauses:
            text = sentence(self.name(record['speaker'])+' said that because '+' and '.join(clauses))
            source_key = next((f['key'] for f in facts if '.knows.' in f['key']),None)
            if source_key:
                from conversation import Focus
                origin = self.source_answer(Focus(event['id']-1,record['speaker'],source_key))
                if origin: text += ' '+origin[0]; facts += origin[1]
            return self.speech_reply(question,'dialogue_reason',record,text,facts,[event['id']])
        # Context is not a psychological explanation or a semantic quote parse.
        if event and event['kernel']=='Tell' and event['actors']==[record['speaker'],record['listener']]:
            item = self.event_description(event)
            if item:
                listener_key=item[1]; source=listener_key.split('.knows.',1)[1]
                speaker_key=record['speaker']+'.knows.'+source; at=event['id']-1
                text=sentence(self.clause(speaker_key,event['before'][speaker_key],at=at))
                facts=[self.fact(speaker_key,at)]
                prior=self.clause(listener_key,event['before'][listener_key],at=at)
                if prior: text+=' '+sentence(prior); facts.append(self.fact(listener_key,at))
                text+=" The story does not state a more specific reason for those words."
                return self.speech_reply(question,'dialogue_context',record,text,facts,[event['id']])
        return self._reply(question,'dialogue_reason',self.focus,
                           reason="The story records those words, but it doesn't say why they were spoken.")

    def ask_dialogue(self, question):
        """Return a handled turn or None; never guess which of several speeches."""
        from conversation import normalized, sentence
        query = normalized(question); record = self.speech_record()
        # Exact named questions can start a conversation; names come from entities.
        for entity in self.entities:
            name = normalized(self.name(entity))
            for listener in self.entities:
                other = normalized(self.name(listener))
                if query in (f'what did {name} say to {other}',f'what did {name} tell {other}'):
                    candidates=[u for u in self.dialogue if u['speaker']==entity and u['listener']==listener]
                    if len(candidates)==1: return self.speech_reply(question,'dialogue',candidates[0])
                    return self._reply(question,'clarification',self.focus,
                        reason='Choose a listed speech; that question does not identify one attributed quote.')
            if query in (f'what did {name} say', f'what did {name} say next'):
                candidates = [u for u in self.dialogue if u['speaker']==entity]
                if query.endswith(' next'):
                    if record is None: return self._reply(question,'clarification',self.focus,reason='Which speech should I start from?')
                    candidates = [u for u in candidates if self.dialogue.index(u)>self.dialogue.index(record)][:1]
                if len(candidates)==1: return self.speech_reply(question,'dialogue',candidates[0])
                if len(candidates)>1:
                    return self._reply(question,'clarification',self.focus,reason=f'{self.name(entity)} speaks more than once. Choose one of the numbered speech questions.')
                return self._reply(question,'dialogue',self.focus,reason=f'I cannot identify a recorded speech by {self.name(entity)} there.')
        match = re.fullmatch(r'who said [“"](.+)[”"]',question.strip().rstrip('?').strip(),re.I)
        if match:
            candidates = [u for u in self.dialogue if any(normalized(s['text'])==normalized(match[1]) for s in u['quotes'])]
            if len(candidates)==1:
                item=candidates[0]
                return self.speech_reply(question,'dialogue_speaker',item,spoken(item,self.name(item['speaker'])))
            return self._reply(question,'clarification',self.focus,reason='I cannot identify a unique speaker for that quote. Choose a listed speech.')
        if record is None: return None
        if query in ('why','why did they say that','why did she say that','why did he say that',
                     f'why did {normalized(self.name(record["speaker"]))} say that'):
            return self.dialogue_reason(question,record)
        if query in ('what did they say','what did she say','what did he say','what were the exact words'):
            return self.speech_reply(question,'dialogue',record)
        if query in ('who said that','who was speaking'):
            return self.speech_reply(question,'dialogue_speaker',record,spoken(record,self.name(record['speaker'])))
        if query in ('who were they talking to','who was she talking to','who was he talking to','who did they say that to',
                     f'who was {normalized(self.name(record["speaker"]))} talking to'):
            if record['listener']:
                return self.speech_reply(question,'dialogue_listener',record,
                    f'{self.name(record["speaker"])} was speaking to {self.name(record["listener"])}. '+spoken(record,self.name(record['speaker'])))
            return self._reply(question,'dialogue_listener',self.focus,reason='The dialogue does not identify who those words were addressed to.')
        if query in ('what was said next','what did they say next','what was said before that','what did they reply','what was the reply'):
            index=self.dialogue.index(record); candidate=None
            if 'reply' in query:
                candidates=[u for u in self.dialogue if u['reply_to']==record['id']]
                if len(candidates)==1: candidate=candidates[0]
            else:
                index += -1 if query.endswith('before that') else 1
                if 0 <= index < len(self.dialogue): candidate=self.dialogue[index]
            if candidate: return self.speech_reply(question,'dialogue_sequence',candidate)
            return self._reply(question,'dialogue_boundary',self.focus,
                               reason='There is no clearly attributed speech recorded for that follow-up.')
        if query in ('was that true','is that true','was that right'):
            claim=record['claim']
            if not claim:
                return self._reply(question,'dialogue_truth',self.focus,
                    reason="Those are the character's words. The story has no linked factual claim that lets me check them as true or false.")
            at=record['event_id']-(claim.get('at','before')=='before'); actual=self.states[at][claim['key']]
            clause=self.clause(claim['key'],actual,at=at)
            if clause:
                text=('Yes. ' if type(actual) is type(claim['value']) and actual==claim['value'] else 'No. ')
                text+=sentence('When those words were spoken, '+clause)
                return self.speech_reply(question,'dialogue_truth',record,text,[self.fact(claim['key'],at)])
        if query in ('why was that possible','how was that possible','what happened next','and then','then what','what happened before that') and record['event_id'] is None:
            return self._reply(question,'clarification',self.focus,
                               reason='That speech is not tied to a single event. Choose an event question to follow the action.')
        if query in ('how did they know','how did she know','how did he know','how did they find out'):
            event=self.events[record['event_id']-1] if record['event_id'] else None
            if event and record['reason_keys']:
                from conversation import Focus
                keys=[k for k in record['reason_keys'] if '.knows.' in k]
                if len(keys)==1:
                    origin=self.source_answer(Focus(event['id']-1,record['speaker'],keys[0]))
                    if origin: return self.speech_reply(question,'dialogue_source',record,*origin)
            return self._reply(question,'dialogue_source',self.focus,reason='The dialogue has no unambiguous link to how the speaker learned that.')
        if query in ('where was it','where was that','where were they','where was she','where was he',
                     'who had it','who had it before that','where was it before that','who helped','who helped with that'):
            return self._reply(question,'clarification',self.focus,
                reason='Choose an event or object question to check that. The quote alone does not identify that state or contribution.')
        return None
