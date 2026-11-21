"""Shared operations and scene families work beyond the original role names."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import unittest

from .grammar import expand
from .world import Entity, Frame, World, kernel
from .storytelling.operations import Change, can_transfer, committed, enabled
from .storytelling.continuations import ExpandedLanguage
from .storytelling.head_adapter import StoryHeads
from .storytelling.runtime import generate, replay, setup
from .storytelling.surface import detokenize
from .storytelling.head_comparison import validate


class SharedCoreTests(unittest.TestCase):
    def fixture(self):
        return World('unfamiliar_transfer', {
            'giver': Entity('giver', 'Ada', 'person', 'room'),
            'receiver': Entity('receiver', 'Omar', 'person', 'room'),
            'parcel': Entity('parcel', 'parcel', 'object', 'giver'),
        }, hero='giver', helper='receiver', target='parcel', tool='parcel',
            setting='room', facts={}, flags={'ready'})

    def test_transfer_composes_with_unfamiliar_entities_and_rejects_stale_frames(self):
        w = self.fixture()
        k = kernel('give', requires=('ready',), excludes=('given',), adds=('given',))
        frame = Frame('give', 'giver', 'parcel', destination='receiver')
        def candidates(world):
            return [(k, frame)] if enabled(world, k) and can_transfer(world, 'parcel', 'giver', 'receiver') else []
        @committed(candidates, {'give': (Change('@patient', '@destination'),)})
        def transfer(world, event):
            pass
        g = ExpandedLanguage(w, lexicon={'nouns': {'parcel': {}}})
        sentence = g.transfer('giver', g.ref('receiver'), g.ref('parcel'))
        alternatives = {detokenize(t) for t,_,_ in expand(sentence.node)}
        self.assertIn('Ada gave the parcel to Omar', alternatives)
        before = w.snapshot()
        event = transfer(w, frame, 'Ada gave the parcel to Omar.')
        self.assertEqual(event['before'], before)
        self.assertEqual(event['after']['entities']['parcel']['location'], 'receiver')
        after = w.to_dict()
        with self.assertRaises(ValueError): transfer(w, frame, 'Repeated gift')
        self.assertEqual(after, w.to_dict())
        for change in ('remote', 'absent', 'unheld', 'abstract'):
            altered = self.fixture()
            if change == 'remote': altered.entities['receiver'].location = 'elsewhere'
            elif change == 'absent': del altered.entities['parcel']
            elif change == 'unheld': altered.entities['parcel'].location = 'room'
            else: altered.entities['receiver'].kind = 'concept'
            self.assertFalse(can_transfer(altered, 'parcel', 'giver', 'receiver'))

    def test_bad_declarative_binding_does_not_partially_apply(self):
        w = self.fixture(); before = w.to_dict(); f = Frame('give', 'giver', 'parcel', destination='receiver')
        @committed(lambda w: [(kernel('give', adds=('given',)), f)],
                   {'give': (Change('parcel', 'receiver'), Change('nonexistent', 'room'))})
        def bad(world, frame): pass
        with self.assertRaises(ValueError): bad(w, f, '')
        self.assertEqual(before, w.to_dict())

    def test_fetch_family_binds_both_prose_and_qa(self):
        w = self.fixture(); w.entities['parcel'].location = 'cupboard'
        g = ExpandedLanguage(w, lexicon={'nouns': {'parcel': {}, 'cupboard': {}}})
        result = g.fetch_scene('giver', 'parcel', 'cupboard')
        self.assertEqual(result.claims[0]['entities'], ['giver', 'parcel'])
        self.assertEqual(result.claims[0]['answer'], 'Ada fetched the parcel from the cupboard.')
        self.assertTrue(all('parcel' in t and 'cupboard' in t for t,_,_ in expand(result.node)))

    def test_ability_is_not_an_offer_and_promises_stay_explicit(self):
        pack, w = setup('pottery', 7)
        g = ExpandedLanguage(w, lexicon=pack.LEXICON)
        action = g.v('hold', g.n('bowl', det='a'))
        ability = {detokenize(t) for t,_,_ in expand(g.ability('grandpa', action, listener='hero'))}
        self.assertFalse(any('Let me' in t for t in ability))
        offers = {detokenize(t) for t,_,_ in expand(g.offer('hero', action, listener='helper'))}
        self.assertTrue(any('Let me' in t for t in offers))
        promise = {detokenize(t) for t,_,_ in expand(g.say_intent('hero', 'promise', action, listener='helper'))}
        self.assertTrue(all('promise' in t for t in promise))

    def test_attributed_speaker_is_not_confused_with_listener(self):
        _, w = setup('music', 7)
        self.assertEqual(StoryHeads.subject(w, ('Mateo','told','Nia',',','“','I')), ('partner',True))
        self.assertEqual(StoryHeads.subject(w, ('Nia','tells','Mateo',',','“','Let','me')), ('hero',True))

    def test_before_merge_physical_histories_replay_exactly(self):
        path = Path(__file__).parent/'storytelling/pins/shared_effects.json.gz'
        for row in json.load(gzip.open(path, 'rt')):
            self.assertTrue(replay(row))

    def test_tuned_profile_grounding_and_consent(self):
        for scenario in ('rescue','kite','key','music','greenhouse','library','pottery'):
            for tense in ('past','present'):
                row = generate(scenario, 20, continuations='expanded', symbolic_heads=True, head_profile='tuned', tense=tense)
                validate(row)
                self.assertEqual(row['symbolic_heads']['profile'], 'tuned')
        for seed in (0, 7):
            row = generate('music', seed, continuations='expanded', symbolic_heads=True,
                           head_profile='tuned', head_strength=10, partner_willing=False)
            validate(row)
            self.assertNotIn('private_plan', row['final_world']['flags'])


if __name__ == '__main__': unittest.main()
