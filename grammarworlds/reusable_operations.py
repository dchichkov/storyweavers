"""Reviewed physical operations exposed by intact-story annotation retrieval."""
from .catalog_attachment import CatalogLines
from .storytelling.operations import Change
from .storytelling.continuations import ExpandedLanguage
from .storytelling.surface import scene


class ReusableLines(CatalogLines):
    fields = {**CatalogLines.fields,
        'put_item': {'actor', 'item', 'destination'},
        'prepare_support': {'actor', 'item', 'source'},
        'shape_clay': {'actor', 'item', 'tool'},
        'perform_solo': {'actor', 'item'},
        'repair_fixture': {'actor', 'item'}}

    def effects(self, event):
        op = event['op']
        if op == 'put_item':
            return (Change(event['item'], event['destination']),)
        if op == 'prepare_support':
            return (Change(event['item'], event['actor'], add=('steady',)),)
        if op == 'shape_clay':
            return (Change(event['item'], add=('shaped',)),)
        if op == 'perform_solo':
            return (Change(event['actor'], add=('performed_solo',)),)
        if op == 'repair_fixture':
            return (Change(event['item'], add=('repaired',), remove=('broken',)),)
        return super().effects(event)

    def reasons(self, sid, w=None):
        w = w or self.world
        e = self.events[sid]
        if e['op'] not in {'put_item', 'prepare_support', 'shape_clay', 'perform_solo', 'repair_fixture'}:
            return super().reasons(sid, w)
        if w.finished:
            return ['world is marked ended']
        if any(e[slot] not in w.entities for slot in self.fields[e['op']]):
            return ['missing carrier']
        actor, item = w.entities[e['actor']], w.entities[e['item']]
        errors = []
        def need(ok, reason):
            if not ok: errors.append(reason)
        for slot in self.fields[e['op']]:
            need(w.entities[e[slot]].kind in self.kinds[slot], 'operation role type changed: '+slot)
        need(actor.kind == 'person', 'actor must be a person')
        if e['op'] in {'put_item', 'prepare_support'}:
            need('can_hold' in actor.properties and 'portable' in item.properties, 'carrier/item cannot move object')
            place = w.entities[e.get('destination', e.get('source'))]
            need(place.kind == 'place' and 'reachable' in place.properties, 'place must be reachable')
            need(place.location == actor.location, 'place is not co-located')
            if e['op'] == 'put_item':
                need(item.location == actor.id, 'actor is not holding item')
            else:
                need('can_prepare_support' in actor.properties and 'reach' in item.properties,
                     'support preparation capability/affordance missing')
                need(item.location == place.id, 'support is not at source')
                need('steady' not in item.state, 'support already prepared')
        elif e['op'] == 'shape_clay':
            tool = w.entities[e['tool']]
            need('can_shape_clay' in actor.properties, 'actor cannot shape clay')
            need('clay' in item.properties and 'wet' in item.state and not {'shaped','bisque','fired'} & item.state,
                 'clay must be wet and unshaped')
            need('shape' in tool.properties and tool.location == actor.id, 'shaping tool is not held')
            surface = w.entities.get(item.location)
            need(item.location == actor.id or (surface is not None and surface.kind == 'place'
                 and 'reachable' in surface.properties and surface.location == actor.location), 'clay is not accessible')
        elif e['op'] == 'repair_fixture':
            need('can_repair_fixture' in actor.properties and 'repairable_fixture' in item.properties,
                 'fixture repair capability/affordance missing')
            need('broken' in item.state and 'repaired' not in item.state, 'fixture is not broken')
            need(item.location in {actor.id, actor.location}, 'fixture is not accessible')
        else:
            need('can_drum' in actor.properties and 'physics:drum' in item.properties, 'solo requires drum ability and instrument')
            need(item.location == actor.id, 'instrument is not held')
            need('practiced' in actor.state and 'performed_solo' not in actor.state, 'solo requires unperformed practice')
        return errors

    def render(self, sid):
        e = self.events[sid]
        if e['op'] not in {'put_item', 'prepare_support', 'shape_clay', 'perform_solo', 'repair_fixture'}:
            return super().render(sid)
        # Extend lexical coverage without changing any original story grammar.
        from copy import deepcopy
        from .storytelling.pottery_world import LEXICON
        lexicon = deepcopy(LEXICON)
        lexicon['verbs'].update({
            'steady': {'forms': ['steady', 'steadied', 'steadied'], 'valencies': ['V2']},
            'shape': {'forms': ['shape', 'shaped', 'shaped'], 'valencies': ['V2']},
            'play': {'forms': ['play', 'played', 'played'], 'valencies': ['V2']}})
        g = ExpandedLanguage(self.world, lexicon=lexicon)
        if e['op'] == 'put_item':
            return scene(g.s(e['actor'], g.adv(g.v('put', g.ref(e['item'])), g.pp('on', g.ref(e['destination'])))))
        if e['op'] == 'prepare_support':
            return scene(g.fetch_scene(e['actor'], e['item'], self.world.entities[e['source']].noun).node,
                         g.s(e['actor'], g.v('steady', g.ref(e['item']))))
        if e['op'] == 'shape_clay':
            return scene(g.using(e['actor'], g.v('shape', g.ref(e['item'])), g.ref(e['tool'])))
        if e['op'] == 'repair_fixture':
            return scene(g.s(e['actor'], g.v('repair', g.ref(e['item']))))
        return scene(g.s(e['actor'], g.v('play', g.ref(e['item']))))
