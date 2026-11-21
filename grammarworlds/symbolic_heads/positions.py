"""Discrete symbolic rotary positions and an opt-in positional attention adapter.

Each ring is an implicit one-hot vector rotated by an integer permutation.
Relative rotations depend only on key minus query position. This is a discrete
analogue of RoPE's rotation algebra, not its learned dense-vector geometry.
"""
from dataclasses import asdict, dataclass
from itertools import combinations
import argparse
import json
import math

from .runtime import HeadContext, HeadLibrary, Source


@dataclass(frozen=True)
class Position:
    story: str
    token: int
    sentence: int
    in_sentence: int

    def __post_init__(self):
        if not isinstance(self.story,str) or not self.story:
            raise ValueError('a story namespace is required')
        if any(type(x) is not int or x<0 for x in (self.token,self.sentence,self.in_sentence)):
            raise ValueError('positions must be nonnegative integer token-unit indices')
        if self.in_sentence>self.token:
            raise ValueError('sentence-local position exceeds story position')


@dataclass(frozen=True)
class SymbolicRotary:
    periods: tuple[int,...] = (7,11,13,17)

    def __post_init__(self):
        if not self.periods or any(type(p) is not int or p<2 for p in self.periods):
            raise ValueError('positive integer ring lengths of at least two required')
        if any(math.gcd(a,b)!=1 for a,b in combinations(self.periods,2)):
            raise ValueError('ring lengths must be pairwise coprime')

    @property
    def cycle(self):return math.prod(self.periods)

    @property
    def radius(self):return (self.cycle-1)//2

    def phase(self,position):
        if type(position) is not int:raise ValueError('integer phase position required')
        return tuple(position%period for period in self.periods)

    def _validate(self,phases):
        if len(phases)!=len(self.periods) or any(type(v) is not int or not 0<=v<p for v,p in zip(phases,self.periods)):
            raise ValueError('phase vector does not match rings')

    def rotate(self,phases,shift):
        self._validate(phases)
        if type(shift) is not int:raise ValueError('integer rotation required')
        return tuple((v+shift)%p for v,p in zip(phases,self.periods))

    def relative_phase(self,query,key):
        self._validate(query);self._validate(key)
        return tuple((k-q)%p for p,q,k in zip(self.periods,query,key))

    def offset_match(self,query,key,offset):
        """Implicit one-hot dot product, averaged over rotated symbolic rings."""
        self._validate(key)
        expected=self.rotate(query,offset)
        return sum(q==k for q,k in zip(expected,key))/len(self.periods)

    def decode(self,phases):
        """Signed representative modulo cycle; callers must enforce the window."""
        self._validate(phases);period=self.cycle
        value=sum(v*(period//p)*pow(period//p,-1,p) for v,p in zip(phases,self.periods))%period
        return value-period if value>self.radius else value

    def encode(self,position):
        return {axis:list(self.phase(getattr(position,axis))) for axis in ('token','sentence','in_sentence')}

    def relative(self,query,key):
        if query.story!=key.story:raise ValueError('cross-story comparison needs explicit alignment')
        result={}
        for axis in ('token','sentence'):
            # Exact coordinates enforce the non-aliasing contract and causal
            # boundary. The returned distance is decoded from relative phases.
            if abs(getattr(key,axis)-getattr(query,axis))>self.radius:
                raise ValueError('position difference exceeds unambiguous rotary window')
            phases=self.relative_phase(self.phase(getattr(query,axis)),self.phase(getattr(key,axis)))
            result[axis]=dict(delta=self.decode(phases),phase=list(phases))
        if result['sentence']['delta']*result['token']['delta']<0 or (result['sentence']['delta'] and not result['token']['delta']):
            raise ValueError('sentence order conflicts with token order')
        if result['sentence']['delta']==0:
            if query.token-query.in_sentence!=key.token-key.in_sentence:
                raise ValueError('inconsistent sentence start')
            phases=self.relative_phase(self.phase(query.in_sentence),self.phase(key.in_sentence))
            local=self.decode(phases)
            if local!=result['token']['delta']:
                raise ValueError('inconsistent coordinates within the same sentence')
            result['in_sentence']=dict(delta=local,phase=list(phases))
        else:result['in_sentence']=None
        return result


@dataclass(frozen=True)
class PositionedToken:
    """One declared token unit, possibly multiword; annotations are supplied."""
    token: str
    position: Position
    annotations: dict

    def __post_init__(self):
        if not isinstance(self.token,str) or not self.token.strip():raise ValueError('nonempty token required')


def position_tokens(sentences,*,story='story',token_offset=0,sentence_offset=0):
    """Attach append-stable coordinates to already-tokenized annotated sentences.

    A multiword item advances one unit. No hidden whitespace tokenization or
    automatic semantic/POS annotation happens here.
    """
    result=[];offset=token_offset
    for si,sentence in enumerate(sentences,start=sentence_offset):
        for local,item in enumerate(sentence):
            data=dict(item);word=data.pop('token')
            result.append(PositionedToken(word,Position(story,offset,si,local),data));offset+=1
    return result


def percentages(position,*,story_units,sentence_units):
    """Optional 0..100 endpoint coordinates for a completed text version."""
    if (type(story_units) is not int or type(sentence_units) is not int
            or story_units<=position.token or sentence_units<=position.in_sentence
            or sentence_units>story_units):raise ValueError('completed lengths must contain this token')
    return {'text':100*position.token/max(1,story_units-1),
            'sentence':100*position.in_sentence/max(1,sentence_units-1)}


def positional_memory(tokens,query,*,scope='generation',rotary=None,past_only=True,window=128,same_sentence=False):
    """Adapter into the existing table-head API; preserve annotated payloads.

    A transparent authored gate 1/(1+distance) weights eligible memories.
    Causality and distance preferences are additional rules, not properties
    magically supplied by rotation. Repeated event names remain valid keys.
    """
    rotary=rotary or SymbolicRotary()
    if type(window) is not int or not 0<=window<=rotary.radius:raise ValueError('invalid window')
    ids=set();sources=[];audit=[];payloads={}
    for token in tokens:
        p=token.position;identity=(p.story,p.token)
        if identity in ids:raise ValueError('duplicate token occurrence position')
        ids.add(identity)
        reason=None
        if p.story!=query.story:reason='different story'
        elif abs(p.token-query.token)>window:reason='outside window'
        elif past_only and p.token>=query.token:reason='not strictly earlier'
        elif same_sentence and p.sentence!=query.sentence:reason='different sentence'
        event=token.annotations.get('event')
        if not reason and not event:reason='no event annotation'
        if reason:
            audit.append(dict(position=asdict(p),excluded=reason));continue
        relative=rotary.relative(query,p)
        weight=1/(1+abs(relative['token']['delta']))
        # JSON tuple encoding avoids delimiter collisions in story/position IDs.
        source_id=json.dumps(identity,separators=(',',':'))
        patient=token.annotations.get('patient','')
        key=json.dumps([event,patient],separators=(',',':'))
        source=Source(source_id,'positioned_semantics',scope,key,weight)
        sources.append(source);payloads[source_id]=dict(token=token.token,**token.annotations)
        audit.append(dict(source_id=source_id,key=key,relative=relative,position_weight=weight))
    return sources,audit,payloads


def demo():
    sentences=[
        [{'token':'Lili'},{'token':'took','pos':'VERB','event':'obtain repair tool','actor':'lili','patient':'scissors'},
         {'token':'scissors','entity':'scissors','location':'lili','state_scope':'after acquisition'},{'token':'.'}],
        [{'token':'Lili'},{'token':'repaired','event':'repair','actor':'lili','patient':'kite'},{'token':'the kite'},{'token':'.'}],
        [{'token':'Lili'},{'token':'picked up','pos':'VERB','event':'obtain repair tool','actor':'lili','patient':'tape'},
         {'token':'tape','entity':'tape','location':'lili','state_scope':'after acquisition'},{'token':'.'}],
        [{'token':'Lili'},{'token':'fixed','event':'repair','actor':'lili','patient':'kite'},{'token':'the kite'},{'token':'.'}],
        [{'token':'Lili'},{'token':'fetched','event':'obtain repair tool','actor':'lili','patient':'glue'},{'token':'glue'},{'token':'.'}],
    ]
    tokens=position_tokens(sentences,story='repair_demo');query=tokens[13].position;rotary=SymbolicRotary()
    sources,audit,payloads=positional_memory(tokens,query,rotary=rotary)
    keys={patient:json.dumps(['obtain repair tool',patient],separators=(',',':')) for patient in ('scissors','tape','glue')}
    spec=dict(id='symbolic_rotary_demo',status='table',input_channel='positioned_semantics',receiver_mode='multipliers',
        selection=[dict(tokens=['repair',key],weight=1) for key in keys.values()],
        projection=[dict(tokens=[key,'tool:'+patient],weight=1) for patient,key in keys.items()],
        receiver=[dict(tokens=['tool:scissors','cut'],weight=4),dict(tokens=['tool:tape','patch'],weight=4)])
    library=HeadLibrary([spec]);context=HeadContext('symbolic_rotary_demo','repair','generation')
    attention=library.activate(context,sources)
    base={'patch':.25,'cut':.25,'ask':.25,'wait':.25}
    received=library.rerank(base,[context],sources)
    return dict(description='Hand-annotated multiword token units; repeated event names, relative lookup, four-word grammar prior.',
        periods=rotary.periods,unambiguous_radius=rotary.radius,query=asdict(query),query_rotations=rotary.encode(query),
        tokens=[dict(token=t.token,position=asdict(t.position),**t.annotations) for t in tokens],
        attention=attention,position_audit=audit,payloads=payloads,base=base,reranked=received)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--demo',action='store_true');parser.parse_args()
    print(json.dumps(demo(),indent=2))
