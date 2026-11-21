"""Subject switches are resolved in the grammar, before words are sampled."""
from collections import defaultdict
from copy import deepcopy
import unittest
from unittest.mock import patch

from .grammar import choice,expand
from .world import Frame
from .storytelling.runtime import generate,setup,replay
from .storytelling.qa import questions
from .story_memory import annotate
from .storytelling.surface import SpeechLanguage,scene,detokenize
from .storytelling.subject_coherence import cohere_scene,cohere_subjects


def surfaces(node):
    result=defaultdict(float)
    for tokens,probability,_ in expand(node):result[detokenize(tokens)]+=probability
    return dict(result)


def before_event(scenario,kind,tense):
    """Use genuine source execution to reach the event's guarded context."""
    row=generate(scenario,7,tense=tense,presentation=False)
    pack,world=setup(scenario,7)
    for saved in row['final_world']['history']:
        frame=next((f for _,f in pack.candidates(world) if f.kind==kind),None)
        if frame is not None:return pack,world,frame
        f=Frame(**{**saved['frame'],'cause_ids':tuple(saved['frame']['cause_ids'])})
        record=pack.commit(world,f,saved['sentence'])
        for key in ('referents','speakers','narrated'):record[key]=saved[key]
    raise AssertionError('event not reached: '+kind)


class SubjectCoherenceTests(unittest.TestCase):
    def test_beat_runtime_uses_subject_continuity_in_real_scenes(self):
        for source,kind,name in [('repair','rafi_holds_wheel','Ada'),
                                 ('costume','perform_together','Nia')]:
            for tense in ('past','present'):
                row=generate(source,43,tense=tense,beat_budget=6,continuations='expanded')
                replay(row);annotate(row);questions(row)
                scenes=[s['text'] for s in row['scenes'] if s['frame']['kind']==kind]
                if source=='costume':self.assertTrue(scenes)
                for sentence in scenes:
                    self.assertIn('. '+name+' ',sentence)
                    self.assertNotIn('. She ',sentence)

    def language(self,tense='past'):
        pack,w,f=before_event('repair','rafi_holds_wheel',tense)
        return SpeechLanguage(w,tense,pack.LEXICON),w

    def test_real_repair_and_costume_switches_keep_names_in_both_tenses(self):
        for scenario,kind,name in [('repair','rafi_holds_wheel','Ada'),
                                   ('costume','perform_together','Nia')]:
            for tense in ('past','present'):
                with self.subTest(scenario=scenario,tense=tense):
                    p,w,f=before_event(scenario,kind,tense)
                    before=deepcopy(w.to_dict())
                    original=p.plan(w,f,SpeechLanguage(w,tense,p.LEXICON))
                    old=surfaces(original.node);new=cohere_scene(original)
                    revised=surfaces(new.node)
                    self.assertTrue(any('. She ' in s for s in old),old)
                    self.assertTrue(all('. '+name+' ' in s and '. She ' not in s for s in revised),revised)
                    self.assertAlmostEqual(sum(revised.values()),1.)
                    self.assertEqual(new.claims,original.claims)
                    self.assertEqual(w.to_dict(),before)
                    self.assertEqual(cohere_scene(new),new)

    def test_same_subject_keeps_existing_pronoun_distribution(self):
        g,_=self.language()
        native=scene(g.s('hero',g.v('hold',g.ref('wheel'))),g.s('hero',g.v('unwind',g.ref('string'))))
        revised=cohere_scene(native)
        self.assertEqual(surfaces(revised.node),surfaces(native.node))
        self.assertTrue(any('. She ' in s for s in surfaces(revised.node)))

    def test_choices_are_independent_and_keep_branch_probability_mass(self):
        g,_=self.language()
        switched=scene(g.s('helper',g.v('hold',g.ref('wheel'))),g.s('hero',g.v('unwind',g.ref('string')))).node
        same=scene(g.s('hero',g.v('hold',g.ref('wheel'))),g.s('hero',g.v('unwind',g.ref('string')))).node
        revised=surfaces(cohere_subjects(choice('alternatives',switched,same,weights=(2,3))))
        reversed_order=surfaces(cohere_subjects(choice('alternatives',same,switched,weights=(3,2))))
        self.assertEqual(revised,reversed_order)
        self.assertAlmostEqual(sum(p for s,p in revised.items() if s.startswith('Niko')), .4)
        self.assertTrue(all('. Ada ' in s for s in revised if s.startswith('Niko')))
        self.assertTrue(any('. She ' in s for s in revised if not s.startswith('Niko')))
        self.assertAlmostEqual(sum(revised.values()),1.)

    def test_ambiguous_prior_branch_and_coordinated_subject_require_name(self):
        g,_=self.language()
        first=g.either(g.s('hero',g.v('hold',g.ref('wheel'))),g.s('helper',g.v('hold',g.ref('wheel'))))
        together=g.s(g.both(g.ref('hero'),g.ref('helper')),g.v('hold',g.ref('wheel')))
        for opening in (first,together):
            revised=cohere_scene(scene(opening,g.s('hero',g.v('unwind',g.ref('string')))))
            self.assertTrue(all('. Ada ' in s for s in surfaces(revised.node)))

    def test_unknown_subject_requires_name_and_explicit_quoted_i_is_preserved(self):
        g,_=self.language()
        unknown=g.s(g.n('nut'),g.be('locked'))
        quoted=g.line('helper',g.me(g.v('hold',g.ref('wheel'))),listener='hero')
        next_clause=g.s('hero',g.v('unwind',g.ref('string')))
        for opening in (unknown,quoted):
            revised=surfaces(cohere_scene(scene(opening,next_clause)).node)
            self.assertTrue(all('Ada unwound' in s and 'She unwound' not in s for s in revised))
        self.assertTrue(all('“I hold the wheel.”' in s for s in surfaces(cohere_scene(scene(quoted,next_clause)).node)))

    def test_scene_none_and_original_tree_are_unchanged(self):
        self.assertIsNone(cohere_scene(None))
        g,_=self.language()
        original=scene(g.s('helper',g.v('hold',g.ref('wheel'))),g.s('hero',g.v('unwind',g.ref('string'))))
        saved=deepcopy(original)
        cohere_scene(original)
        self.assertEqual(original,saved)

    def test_temporary_pipeline_hook_preserves_replay_and_grounded_qa(self):
        # The production hook is deliberately left to the measured refinement
        # round. Exercise its contract here without changing runtime.py.
        from .storytelling import runtime
        native_plan=runtime.plan
        def coherent_plan(*args,**kwargs):return cohere_scene(native_plan(*args,**kwargs))
        with patch.object(runtime,'plan',side_effect=coherent_plan):
            for scenario in ('repair','costume'):
                for tense in ('past','present'):
                    row=generate(scenario,19,tense=tense,continuations='expanded',beat_budget=2)
                    self.assertTrue(replay(row))
                    self.assertTrue(questions(row,6))
                    self.assertEqual(annotate(row)['text'],row['story'])
                    self.assertIn('ended',row['final_world']['flags'])


if __name__=='__main__':unittest.main()
