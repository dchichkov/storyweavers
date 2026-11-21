"""Executable guarded story data + compositional grammar; no runtime models."""
from copy import deepcopy
from functools import lru_cache
from importlib import import_module

from ...world import Entity, Fact, World, Frame, kernel
from ..operations import committed
from ..lexicon import with_shared
from ..surface import scene
from ...portable.nouns import pronoun
from ...portable.language import load_lexicon

NAMES = ('bakery','puppets','seaside','snow','picnic','market','camp','orchard',
         'costume','pond','repair','museum','laundry','trail','festival','biscuit')
# Inflection is lexical data, never guessed by a parser or model.
FORMS = {
    'welcome': ('welcomed','welcomed'), 'stay': ('stayed','stayed'),
    'pick': ('picked','picked'), 'lower': ('lowered','lowered'),
    'raise': ('raised','raised'), 'move': ('moved','moved'),
    'peg': ('pegged','pegged'), 'guide': ('guided','guided'),
    'hear': ('heard','heard'),
    'have': ('had','had'),
    'steady': ('steadied','steadied'), 'weigh': ('weighed','weighed'),
    'jam': ('jammed','jammed'), 'lock': ('locked','locked'), 'loosen': ('loosened','loosened'),
    'unwind': ('unwound','unwound'), 'tighten': ('tightened','tightened'),
    'roll': ('rolled','rolled'), 'glow': ('glowed','glowed'), 'shine': ('shone','shone'),
    'stitch': ('stitched','stitched'), 'turn': ('turned','turned'), 'shorten': ('shortened','shortened'),
    'bow': ('bowed','bowed'), 'catch': ('caught','caught'), 'clear': ('cleared','cleared'),
    'light': ('lit','lit'), 'race': ('raced','raced'), 'divide': ('divided','divided'),
    'weave': ('wove','woven'), 'tie': ('tied','tied'), 'untie': ('untied','untied'),
    'bend': ('bent','bent'), 'leave': ('left','left'), 'trim': ('trimmed','trimmed'),
    'hang': ('hung','hung'), 'drape': ('draped','draped'), 'swing': ('swung','swung'),
    'shrink': ('shrank','shrunk'), 'grow': ('grew','grown'), 'mount': ('mounted','mounted'),
    'orient': ('oriented','oriented'), 'stamp': ('stamped','stamped'), 'shelter': ('sheltered','sheltered'),
    'gather': ('gathered','gathered'), 'unhook': ('unhooked','unhooked'),
    'slice': ('sliced','sliced'), 'share': ('shared','shared'), 'rejoin': ('rejoined','rejoined'),
    'press': ('pressed','pressed'), 'bake': ('baked','baked'), 'cool': ('cooled','cooled'),
    'wash': ('washed','washed'), 'pack': ('packed','packed'), 'deliver': ('delivered','delivered'),
    'admit': ('admitted','admitted'), 'mistake': ('mistook','mistaken'),
    'retrace': ('retraced','retraced'), 'follow': ('followed','followed'),
    'float': ('floated','floated'), 'drift': ('drifted','drifted'), 'free': ('freed','freed'),
    'snag': ('snagged','snagged'), 'block': ('blocked','blocked'), 'face': ('faced','faced'),
    'swirl': ('swirled','swirled'), 'flutter': ('fluttered','fluttered'),
    'hold': ('held','held'), 'carry': ('carried','carried'), 'cut': ('cut','cut'),
    'fit': ('fitted','fitted'), 'remove': ('removed','removed'), 'test': ('tested','tested'),
    'check': ('checked','checked'), 'keep': ('kept','kept'), 'pull': ('pulled','pulled'),
    'lift': ('lifted','lifted'), 'set': ('set','set'), 'open': ('opened','opened'),
    'choose': ('chose','chosen'), 'want': ('wanted','wanted'), 'give': ('gave','given'),
    'say': ('said','said'), 'wait': ('waited','waited'), 'need': ('needed','needed'),
    'borrow': ('borrowed','borrowed'), 'return': ('returned','returned'), 'find': ('found','found'),
    'use': ('used','used'), 'help': ('helped','helped'), 'put': ('put','put'),
    'search': ('searched','searched'), 'notice': ('noticed','noticed'), 'watch': ('watched','watched'),
    'smile': ('smiled','smiled'), 'save': ('saved','saved'), 'step': ('stepped','stepped'),
    'draw': ('drew','drawn'), 'reach': ('reached','reached'), 'stand': ('stood','stood'),
    'wrap': ('wrapped','wrapped'), 'settle': ('settled','settled'), 'stop': ('stopped','stopped'),
    'rest': ('rested','rested'), 'drop': ('dropped','dropped'), 'show': ('showed','shown'),
    'work': ('worked','worked'), 'try': ('tried','tried'), 'walk': ('walked','walked'),
    'make': ('made','made'), 'promise': ('promised','promised'), 'play': ('played','played'),
    'fold': ('folded','folded'), 'repair': ('repaired','repaired'), 'fetch': ('fetched','fetched'),
    'take': ('took','taken'), 'listen': ('listened','listened'), 'spill': ('spilled','spilled'),
    'eat': ('ate','eaten'), 'push': ('pushed','pushed'), 'point': ('pointed','pointed'),
    'spin': ('spun','spun'), 'burn': ('burned','burned'), 'mark': ('marked','marked'),
}


def expression(g, x):
    if isinstance(x,str): return x
    op,*a=x
    if op=='ref': return g.ref(a[0])
    if op=='noun': return g.n(a[0],*a[1],det=a[2],number=a[3])
    if op=='pronoun': return pronoun(a[0])
    if op=='verb': return g.v(a[0],*(expression(g,v) for v in a[1:]))
    if op=='be': return g.be(expression(g,a[0]))
    if op=='can': return g.can(expression(g,a[0]))
    if op=='sentence': return g.s(expression(g,a[0]),expression(g,a[1]),negative=a[2])
    if op=='say': return g.line(a[0],g.me(expression(g,a[1])),listener=a[2])
    if op=='pp': return g.pp(a[0],expression(g,a[1]))
    if op=='adv': return g.adv(expression(g,a[0]),*(expression(g,v) for v in a[1:]))
    if op=='either': return g.either(*(expression(g,v) for v in a))
    if op=='using': return g.using(a[0],expression(g,a[1]),expression(g,a[2]))
    if op=='both': return g.both(*(expression(g,v) for v in a))
    if op=='join': return g.join(expression(g,a[0]),expression(g,a[1]),a[2])
    if op=='possess': return g.possess(expression(g,a[0]),g.cn(a[1]))
    raise ValueError('unknown typed expression: '+op)


def lexicon(spec):
    result=with_shared({})
    base=load_lexicon()
    for e in spec['entities'].values():
        if e['kind']!='person':
            result['nouns'].setdefault(e['noun'],{})
            if e['number']=='plural': result['nouns'][e['noun']]['plural']=e['noun']
    def visit(x):
        if not isinstance(x,list) or not x: return
        op,*a=x
        if op=='noun':
            result['nouns'].setdefault(a[0],base['nouns'].get(a[0],{}))
            for adj in a[1]: result['adjectives'][adj]={}
        elif op=='possess': result['nouns'].setdefault(a[1],{})
        elif op=='be' and isinstance(a[0],str):result['adjectives'][a[0]]={}
        elif op=='pp':result['prepositions'][a[0]]={}
        elif op=='adv':
            for mod in a[1:]:
                if isinstance(mod,str):result['adverbs'][mod]={}
        elif op=='verb':
            word=a[0]; args=a[1:]
            valency=('V' if not args else 'V3' if len(args)==2 and args[1][0] in {'ref','noun','possess','both','pronoun'} else
                     'V2V' if len(args)==2 else 'VV' if args[0][0] in {'verb','adv','be','can'} else 'V2')
            entry=deepcopy(result['verbs'].get(word,base['verbs'].get(word,{})))
            if not entry:
                if word not in FORMS: raise ValueError('missing authored verb inflection: '+word)
                entry=dict(forms=[word,*FORMS[word]],valencies=[])
            entry['valencies']=sorted(set(entry.get('valencies',[]))|{valency})
            result['verbs'][word]=entry
        for child in a:
            if isinstance(child,list) and child and isinstance(child[0],str):visit(child)
    for e in spec['events']:
        for x in e['surface']:visit(x)
    return result


class SeedPack:
    def __init__(self,spec):
        self.spec=deepcopy(spec);self.LEXICON=lexicon(spec)
        self.events={e['name']:e for e in spec['events']}
        if len(self.events)!=len(spec['events']):raise ValueError('duplicate event names')
        self.KERNELS={name:kernel(name,e['after'],e['excludes'],e['adds'],base=e['base'],
            query=e['tags'] or ['goal','planning']) for name,e in self.events.items()}
        self.commit=committed(self.candidates)(self._effects)
        for e in self.events.values():
            for slot in ('actor','patient','instrument','destination'):
                if e[slot] and e[slot] not in spec['entities']:raise ValueError('unbound '+slot)
            if spec['entities'][e['actor']]['kind']!='person':raise ValueError('event actor must be physical person')
            for change in e['effects']:
                if change['entity'] not in spec['entities']:raise ValueError('unbound effect carrier')
                if change['location'] and change['location'] not in spec['entities']:raise ValueError('unbound destination')

    def make_world(self,seed=0,**options):
        if options:raise ValueError('unknown seed-world options: '+str(sorted(options)))
        data=self.spec
        entities={i:Entity(id=i,**{**e,'properties':set(e['properties']),'state':set(e['state'])})
                  for i,e in deepcopy(data['entities']).items()}
        return SeedWorld(data['name'],entities,'hero',data['helper'],data['target'],data['tool'],'work',{
            'problem':Fact('problem',data['premise'],('problem','goal')),
            'helper_available':Fact('helper_available',entities[data['helper']].noun+' is nearby.',('helper','trust'))})

    def reasons(self,w,e):
        errors=[]
        # Authoring-time fixed casts must remain physically grounded, including
        # carriers mentioned in compound effects rather than the coarse frame.
        for entity, expected in self.spec['entities'].items():
            if entity not in w.entities or w.entities[entity].kind != expected['kind']:
                errors.append('missing or mistyped carrier: '+entity)
        if errors:return errors
        if w.finished:errors.append('ended')
        k=self.KERNELS[e['name']]
        if not k.requires<=w.flags or k.excludes&w.flags:errors.append('event dependencies')
        for slot in ('actor','patient','instrument','destination'):
            if e[slot] and e[slot] not in w.entities:errors.append('missing '+slot)
        if errors:return errors
        for guard in e['guards']:
            op,*a=guard
            if any(i not in w.entities for i in (a if op=='together' else a[:1])):
                errors.append('missing guard carrier');continue
            if op=='location':ok=w.entities[a[0]].location==a[1]
            elif op=='state':ok=a[1] in w.entities[a[0]].state
            elif op=='property':ok=a[1] in w.entities[a[0]].properties
            elif op=='together':ok=len({w.entities[i].location for i in a})==1
            else:raise ValueError('unknown guard '+op)
            if not ok:errors.append(str(guard))
        return errors

    def candidates(self,w):
        return [(self.KERNELS[name],Frame(name,e['actor'],e['patient'],e['instrument'],e['destination'],
            tuple(('state:' if g[0]=='state' else 'loc:')+g[1] for g in e['guards'] if g[0] in {'state','location'})))
            for name,e in self.events.items() if not self.reasons(w,e)]

    def _effects(self,w,f):
        for effect in self.events[f.kind]['effects']:
            ent=w.entities[effect['entity']]
            if effect['location'] is not None:ent.location=effect['location']
            ent.state.difference_update(effect['remove']);ent.state.update(effect['add'])
            ent.memes.update(effect['memes'])

    def plan(self,w,f,g):
        e=self.events[f.kind]
        return scene(*(expression(g,x) for x in e['surface']),qa=deepcopy(e['qa'])) if e['surface'] else None


class SeedWorld(World):
    def facts_for_attention(self):
        facts=super().facts_for_attention()
        for entity in self.entities.values():
            facts.append(Fact('loc:'+entity.id,entity.noun+' is at '+entity.location,
                              ('physical',entity.id,'location')))
            facts.append(Fact('state:'+entity.id,entity.noun+': '+', '.join(sorted(entity.state)),
                              ('physical',entity.id,'state')))
        return facts


@lru_cache(maxsize=None)
def pack(name):
    if name not in NAMES:raise ValueError(name)
    return SeedPack(import_module('.'+name,__package__).SPEC)
