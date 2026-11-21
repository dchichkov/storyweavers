"""Joint normalization, correlated uncertainty, causal scope and live consumption."""
from collections import defaultdict
from copy import deepcopy
import unittest

from .grammar import Derivation, expand
from .world import Frame
from .storytelling.attribute_sampler import AttributeForest
from .storytelling.attribute_grammar import expand_attributes, candidate_attributes
from .storytelling.runtime import generate, setup, build_forest, SCENARIOS
from .storytelling.surface import SpeechLanguage
from .storytelling.continuations import ExpandedLanguage
from .storytelling.head_adapter import StoryHeads
from .storytelling.qa import questions


def ambiguous_forest():
    rows, annotations = [], []
    for item, probability in [('scissors', .4), ('tape', .25), ('kite', .2), ('dad', .15)]:
        word = 'took' if item in {'scissors', 'tape'} else 'examined' if item == 'kite' else 'asked'
        frame = Frame('obtain tool' if word == 'took' else word, 'lili', item)
        rows.append(Derivation((word, item), probability, frame, ()))
        annotations.append((dict(pos='VERB', actor='lili', patient=item), dict(pos='NOUN', entity=item)))
    return AttributeForest(rows, {}, annotations)


class AttributeGenerationTests(unittest.TestCase):
    def test_joint_marginal_and_conditioned_uncertainty(self):
        forest = ambiguous_forest()
        p = forest.predict()
        probs = {c['word']: c['probability'] for c in p['choices']}
        self.assertAlmostEqual(probs['took'], .65)
        self.assertEqual(len(p['annotated_choices']), 4)
        selected = forest.observe('took', p)
        self.assertEqual(len(selected), 2)
        posterior = {forest.attribute_table[r['attributes']]['patient']: r['probability'] for r in selected}
        self.assertAlmostEqual(posterior['scissors'], .4/.65)
        self.assertAlmostEqual(posterior['tape'], .25/.65)
        next_p = forest.predict(('took',))
        self.assertEqual(set(c['word'] for c in next_p['choices']), {'scissors', 'tape'})
        forest.observe('tape', next_p)
        forest.observe('<END>', forest.predict(('took', 'tape')))
        self.assertEqual(list(forest.event_posterior(('took', 'tape')))[0].patient, 'tape')

    def test_binding_changes_next_prediction_not_only_export(self):
        forest = ambiguous_forest()
        p = forest.predict()
        tape = next(c['attributes'] for c in p['annotated_choices']
                    if forest.attribute_table[c['attributes']].get('patient') == 'tape')
        forest.observe('took', p, attribute_id=tape)
        self.assertEqual([(c['word'], c['probability']) for c in forest.predict(('took',))['choices']], [('tape', 1.)])
        self.assertEqual(forest.attribute_memory()[0]['attributes']['patient'], 'tape')
        with self.assertRaises(ValueError):
            forest.observe('took', p)  # stale prediction cannot be reapplied

    def test_word_heads_preserve_conditional_annotation_ratios(self):
        forest = ambiguous_forest()
        p = forest.predict()
        for c in p['choices']:
            c['probability'] = .8 if c['word'] == 'took' else .1
        forest.reconcile_word_weights(p)
        self.assertAlmostEqual(sum(c['probability'] for c in p['annotated_choices']), 1.)
        took = [c for c in p['annotated_choices'] if c['word'] == 'took']
        self.assertAlmostEqual(took[0]['probability']/took[1]['probability'], .4/.25)
        forest.observe('took', p)
        self.assertAlmostEqual(forest.predict(('took',))['choices'][0]['probability'], .4/.65)

    def test_attribute_receiver_reweights_same_word_and_future_continuation(self):
        forest = ambiguous_forest()
        p = forest.predict()
        tape = next(c['attributes'] for c in p['annotated_choices']
                    if forest.attribute_table[c['attributes']].get('patient') == 'tape')
        forest.rerank_attributes(p, {tape: 2.})
        self.assertAlmostEqual(next(c['probability'] for c in p['choices'] if c['word'] == 'took'), .9/1.25)
        forest.observe('took', p)
        next_p = {c['word']: c['probability'] for c in forest.predict(('took',))['choices']}
        self.assertAlmostEqual(next_p['tape'], .5/.9)
        self.assertAlmostEqual(next_p['scissors'], .4/.9)

    def test_same_surface_different_semantics_survive_end(self):
        frames = [Frame('obtain', 'lili', obj) for obj in ('tape', 'scissors')]
        forest = AttributeForest([Derivation(('took',), p, f, ()) for p, f in zip((.3, .7), frames)], {},
                                 [(dict(patient=f.patient),) for f in frames])
        forest.observe('took', forest.predict())
        forest.observe('<END>', forest.predict(('took',)))
        self.assertAlmostEqual(forest.event_posterior(('took',))[frames[0]], .3)
        self.assertAlmostEqual(forest.event_posterior(('took',))[frames[1]], .7)

    def test_typed_scope_and_precommit_state(self):
        pack, world = setup('kite', 7)
        g = SpeechLanguage(world)
        scene = g.line('hero', g.me(g.v('want', g.v('repair', g.ref('target')))), listener='helper')
        before = world.to_dict()
        frame = Frame('notice', 'hero', 'target')
        tokens, _, _, annotations = next(expand_attributes(scene))
        attrs = candidate_attributes(tokens, annotations, frame, world)
        repair = attrs[tokens.index('repair')]
        self.assertEqual(repair['action']['lemma'], 'repair')
        self.assertEqual(repair['assertion'], 'hypothetical')
        self.assertEqual(repair['clause']['subject']['entity'], 'hero')
        self.assertEqual(attrs[tokens.index('I')]['entity'], 'hero')
        target = next(a for t, a in zip(tokens, attrs) if t == 'kite')
        self.assertIn('torn', target['entity_features']['state'])
        self.assertNotIn('repaired', target['entity_features']['state'])
        self.assertEqual(world.to_dict(), before)
        negative = g.s('hero', g.v('repair', g.ref('target')), negative=True)
        tokens, _, _, annotations = next(expand_attributes(negative.node))
        attrs = candidate_attributes(tokens, annotations, frame, world)
        self.assertEqual(attrs[tokens.index('repair')]['assertion'], 'negated')

    def test_expanded_intentions_and_dative_keep_bindings(self):
        _, world = setup('music', 7)
        g = ExpandedLanguage(world)
        frame = Frame('give', 'hero', 'drum', destination='partner')
        sentence = g.s('hero', g.v('give', g.ref('partner'), g.ref('drum')))
        for tokens, _, _, annotations in expand_attributes(sentence.node):
            attrs = candidate_attributes(tokens, annotations, frame, world)
            verb = next(a for t, a in zip(tokens, attrs) if t in {'gave', 'handed'})
            self.assertEqual(verb['action']['arguments']['recipient']['entity'], 'partner')
            self.assertEqual(verb['action']['arguments']['object']['entity'], 'drum')
        intention = g.say_intent('hero', 'promise', g.v('play', g.ref('drum')), listener='partner')
        for tokens, _, _, annotations in expand_attributes(intention):
            attrs = candidate_attributes(tokens, annotations, frame, world)
            self.assertTrue(all(a['assertion'] == 'hypothetical' for t, a in zip(tokens, attrs) if t == 'play'))

    def test_all_worlds_joint_normalization_support_and_legacy_parity(self):
        for scenario in SCENARIOS:
            for tense, mode in [('past', 'original'), ('present', 'expanded')]:
                with self.subTest(scenario=scenario, tense=tense):
                    row = generate(scenario, 7, tense=tense, continuations=mode)
                    old = generate(scenario, 7, tense=tense, continuations=mode, predict_attributes=False)
                    self.assertEqual(row['story'], old['story'])
                    self.assertEqual(row['final_world'], old['final_world'])
                    self.assertEqual(questions(row), questions(old))
                    stream = row['attribute_generation']['tokens']
                    self.assertEqual(len(stream), sum(len(t['word_trace'])-1 for t in row['trace']))
                    for event, old_event in zip(row['trace'], old['trace']):
                        self.assertEqual(event['frame'], old_event['frame'])
                        for p, old_p in zip(event['word_trace'], old_event['word_trace']):
                            joint = defaultdict(float)
                            for c in p['annotated_choices']:
                                self.assertIn(c['attributes'], event['attribute_table'])
                                self.assertGreater(c['probability'], 0)
                                joint[c['word']] += c['probability']
                            self.assertAlmostEqual(sum(joint.values()), 1.)
                            self.assertAlmostEqual(sum(c['probability'] for c in p['selected_attributes']), 1.)
                            self.assertEqual(set(joint), {c['word'] for c in old_p['choices']})
                            for c in p['choices']:
                                self.assertAlmostEqual(c['probability'], joint[c['word']])
                    self.assertEqual([t['position']['token'] for t in stream], list(range(len(stream))))

    def test_compiler_preserves_derivation_weights_and_prediction_is_pure(self):
        for scenario in SCENARIOS:
            pack, world = setup(scenario, 7)
            before = world.to_dict()
            forest, plans = build_forest(pack, world, predict_attributes=True, continuations='expanded')
            for plan in plans.values():
                if plan:
                    self.assertEqual(list(expand(plan.node)), [(t,p,r) for t,p,r,_ in expand_attributes(plan.node)])
            forest.predict()
            self.assertEqual(world.to_dict(), before)

    def test_head_reads_ambiguous_annotated_subject_distribution(self):
        _, world = setup('music', 7)
        # The visible word cannot identify this actor by itself. Posterior binding
        # weights, not a guessed pronoun referent, control the head sources.
        memory = [dict(probability=p, attributes=dict(entity=e, syntax_role='subject', pos='PRON', quoted=False))
                  for e, p in [('hero', .7), ('partner', .3)]]
        heads = StoryHeads(world, head_ids=['P001'])
        _, sources = heads.inputs(world, ('she',), tense='past', available=[], attribute_memory=memory)
        self.assertEqual(sorted(s.confidence for s in sources), [.3, .7])
        self.assertTrue(all('annotated_subject' in s.id for s in sources))
        memory[0]['probability'], memory[1]['probability'] = .2, .8
        _, sources2 = heads.inputs(world, ('she',), tense='past', available=[], attribute_memory=memory)
        self.assertEqual(sorted(s.confidence for s in sources2), [.2, .8])

    def test_heads_change_joint_but_cannot_create_support(self):
        changed = 0
        for scenario in SCENARIOS:
            row = generate(scenario, 7, symbolic_heads=True)
            for event in row['trace']:
                for p in event['word_trace']:
                    mass = defaultdict(float)
                    for c in p['annotated_choices']:
                        mass[c['word']] += c['probability']
                    for c in p['choices']:
                        self.assertAlmostEqual(mass[c['word']], c['probability'])
                    changed += p['head_total_variation'] > 1e-10
        self.assertGreater(changed, 0)


if __name__ == '__main__':
    unittest.main()
