"""Online causality, atomic program repair, replay protection and paid-call accounting."""

import asyncio
from copy import deepcopy
import json
import math
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from .grammar import Gap, GrammarNeuron, Rule, Seq, Token
from .learning import LearningBatch
from .neuron_review import model_fingerprint
from .neuron_spec import encode, neuron_spec
from .online import backward, choose, empty_patch, observe, packet, stage_patch
from .online_experiment import curriculum_cases, train
from .online_teacher import Budget, BudgetExceeded, Teacher
from .transformer import GrammarProjection, Storyformer


def toy():
    return Storyformer(GrammarProjection({word: GrammarNeuron(word, (Rule(Gap(4), {'pos': 'n'}),))
                                         for word in ('a', 'b')}), num_layers=1, num_heads=2, context_size=4)


def specialized(model):
    patch = empty_patch(model)
    patch['rationale'] = 'The ending category signals a reusable continuation.'
    patch['feature_definitions'] = {'noun_tail': {'type': 'boolean', 'description': 'Last input POS is n.'}}
    neuron = GrammarNeuron('noun_suffix', (Rule(Seq(Gap(4), Token(pos='n')), {'noun_tail': True}),))
    patch['heads'] = [dict(layer=0, slot=0, operation='add', neuron=neuron_spec(neuron))]
    patch['outputs'] = [dict(token='a', append=[dict(pattern=encode(Seq(Gap(4), Token(noun_tail=True))),
                                                    emit={'pos': 'n'}, weight=10.)], scale=[])]
    return patch


class OnlineTests(unittest.TestCase):
    def test_curriculum_cannot_insert_future_tokens_or_change_targets(self):
        documents = [[dict(token='a', pos='n'), dict(token='b', pos='n')]]
        entry = dict(document=0, position=1, context=documents[0][:1], target=documents[0][1])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'plan.json'
            path.write_text(json.dumps(dict(observations=[entry])))
            self.assertEqual(curriculum_cases(path, documents), [(documents[0][:1], documents[0][1])])
            entry['context'] = documents[0]
            path.write_text(json.dumps(dict(observations=[entry])))
            with self.assertRaisesRegex(ValueError, 'causal'):
                curriculum_cases(path, documents)

    def test_explicit_pair_updates_only_the_revealed_target(self):
        model = toy()
        pair = ([dict(token='a', pos='n')] * 3, dict(token='b', pos='n'))
        batch = LearningBatch(model, pairs=[pair])
        self.assertEqual(batch.targets, 1)
        self.assertAlmostEqual(batch.report()['joint_nll'], -math.log(model.predict(pair[0]).probability(pair[1])))
        batch.fit(steps=1)
        self.assertGreater(model.predict(pair[0]).probability(pair[1]), .5)
        with self.assertRaises(ValueError):
            LearningBatch(model, [[pair[1]]], pairs=[pair])

    def test_head_and_consumer_commit_together_and_generalize(self):
        model = toy()
        original = model_fingerprint(model)
        revised = stage_patch(model, specialized(model))
        self.assertEqual(original, model_fingerprint(model))

        for word in ('previous', 'another'):
            prefix = [dict(token=word, pos='n')]
            self.assertGreater(revised.predict(prefix).probability(dict(token='a', pos='n')), .9)
        self.assertEqual(revised.predict([]).to_dict(), model.predict([]).to_dict())
        with self.assertRaisesRegex(ValueError, 'stale'):
            stage_patch(revised, specialized(model))
        bad = specialized(model)
        bad['heads'][0]['neuron']['rules'][0]['emit'] = {'token': 'future'}
        with self.assertRaises(ValueError):
            stage_patch(model, bad)
        self.assertEqual(original, model_fingerprint(model))

    def test_whitespace_output_root_accepts_a_valid_rule_fragment(self):
        model = toy()
        model.projection.neurons['\n\n'] = GrammarNeuron('\n\n', (Rule(Gap(4), {'pos': 'space'}, .01),))
        patch = empty_patch(model)
        patch['outputs'] = [dict(token='\n\n', append=[dict(pattern=encode(Seq(Gap(4), Token(pos='punct'))),
                                                            emit={'pos': 'space'}, weight=10.)], scale=[])]
        revised = stage_patch(model, patch)
        self.assertEqual(revised.projection.neurons['\n\n'].name, '\n\n')
        self.assertGreater(revised.predict([dict(token='.', pos='punct')]).probability(dict(token='\n\n', pos='space')), .8)

    def test_replay_rejects_current_example_memorization(self):
        model = toy()
        pair = ([], dict(token='a', pos='n'))
        replay = [([], dict(token='b', pos='n'))]
        weighted, _ = backward(model, pair)
        patch = empty_patch(weighted)
        patch['outputs'] = [dict(token='a', append=[], scale=[dict(rule=0, factor=20.)])]
        selected, decision = choose(model, weighted, patch, pair, replay)
        self.assertEqual(decision['adopted'], 'unchanged')
        self.assertEqual(model_fingerprint(model), model_fingerprint(selected))

    def test_observed_attribute_conflicts_are_rejected(self):
        model = toy()
        pair = ([dict(token='prior', pos='n')], dict(token='a', pos='n'))
        weighted, _ = backward(model, pair)
        patch = specialized(weighted)
        patch['heads'][0]['neuron']['rules'][0]['emit'] = {'pos': 'v'}
        patch['heads'][0]['neuron']['rules'][0]['weight'] = 100.
        second = deepcopy(patch['heads'][0])
        second['slot'] = 1
        patch['heads'].append(second)
        patch['outputs'][0]['append'][0]['pattern'] = encode(Gap(4))
        selected, decision = choose(model, weighted, patch, pair, [])
        self.assertEqual(decision['scores']['teacher']['current']['conflicts'], 1)
        self.assertNotEqual(decision['adopted'], 'teacher')
        self.assertEqual(observe(selected, pair)['residual'][-1]['pos'], 'n')

    def test_async_training_resumes_without_reasking_teacher(self):
        async def experiment(folder):
            calls = []
            async def teacher(evidence, directory):
                calls.append(deepcopy(evidence))
                return deepcopy(evidence['patch_template'])
            stream = [([], dict(token='a', pos='n')),
                      ([dict(token='a', pos='n')], dict(token='b', pos='n'))]
            before = deepcopy(stream)
            _, _, report = await train(Path(folder), toy(), stream, [], teacher, steps=2)
            await train(Path(folder), toy(), stream, [], teacher, steps=2)
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0]['context'], [])
            self.assertEqual(calls[0]['replay_examples'], [])
            self.assertEqual(calls[1]['replay_examples'], [stream[0]])
            self.assertEqual(stream, before)
            self.assertAlmostEqual(calls[0]['prediction_before_update']['probability'], .5)
            self.assertEqual(report['observations'], 2)
        with tempfile.TemporaryDirectory() as folder:
            asyncio.run(experiment(folder))


class TeacherTests(unittest.TestCase):
    def test_shared_prefix_stays_identical_and_live_calls_request_flex(self):
        with tempfile.TemporaryDirectory() as folder:
            teacher = Teacher(None, folder, 'gpt-6-luna', [])
            a, b = teacher.request({'target': 'a'}), teacher.request({'target': 'b'})
            self.assertEqual(a['input'][0], b['input'][0])
            self.assertEqual(a['prompt_cache_key'], b['prompt_cache_key'])
            self.assertNotEqual(a['input'][1], b['input'][1])
            self.assertEqual(a['service_tier'], 'flex')
            self.assertEqual(a['prompt_cache_options'], {'mode': 'explicit', 'ttl': '30m'})
            self.assertEqual(a['input'][0]['content'][0]['prompt_cache_breakpoint'], {'mode': 'explicit'})
            self.assertGreater(len(teacher.prefix.split()), 1024)

    def test_parallel_reservations_and_unknown_outcome_survive_restart(self):
        async def check(folder):
            budget = Budget(Path(folder) / 'budget.json', .06)
            body = {'input': 'x', 'max_output_tokens': 8192}
            results = await asyncio.gather(budget.reserve('a', body), budget.reserve('b', body), return_exceptions=True)
            self.assertEqual(sum(isinstance(value, BudgetExceeded) for value in results), 1)
            restored = Budget(budget.path, .06)
            self.assertEqual(restored.data, budget.data)
            winner = next(iter(restored.data['calls']))
            await restored.reserve(winner, body)
            self.assertEqual(len(restored.data['calls']), 1)
            with self.assertRaisesRegex(ValueError, 'changed'):
                await restored.reserve(winner, {**body, 'input': 'different'})
            with self.assertRaises(ValueError):
                Budget(budget.path, 11)
        with tempfile.TemporaryDirectory() as folder:
            asyncio.run(check(folder))

    def test_invalid_teacher_json_is_still_billed_and_not_redispatched(self):
        async def check(folder):
            calls = []
            raw = dict(id='r1', model='gpt-6-luna', service_tier='flex', status='completed',
                       usage=dict(input_tokens=12000, output_tokens=100,
                                  input_tokens_details=dict(cached_tokens=9000, cache_write_tokens=2000)),
                       output=[dict(type='message', content=[dict(type='output_text', text='{invalid')])])
            async def create(**kwargs):
                calls.append(kwargs)
                return SimpleNamespace(model_dump=lambda **kwargs: deepcopy(raw))
            teacher = Teacher(SimpleNamespace(responses=SimpleNamespace(create=create)), folder, 'gpt-6-luna', [])
            for _ in range(2):
                with self.assertRaises(ValueError):
                    await teacher({}, Path(folder) / 'step_000')
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0]['service_tier'], 'flex')
            entry = teacher.budget.data['calls']['step_000']
            self.assertEqual(entry['state'], 'settled')
            self.assertAlmostEqual(entry['estimated_cost_usd'], .000245)
            self.assertGreaterEqual(entry['accounted_usd'], entry['estimated_cost_usd'])
            self.assertTrue((Path(folder) / 'step_000/receipt.json').exists())
        with tempfile.TemporaryDirectory() as folder:
            asyncio.run(check(folder))

    def test_usage_above_reservation_halts_and_is_not_hidden(self):
        async def check(folder):
            budget = Budget(Path(folder) / 'budget.json')
            await budget.reserve('a', {'input': 'x', 'max_output_tokens': 10})
            with self.assertRaises(BudgetExceeded):
                await budget.settle('a', dict(model='gpt-6-luna', service_tier='flex',
                    usage=dict(input_tokens=10, output_tokens=1_000_000)))
            saved = json.loads(budget.path.read_text())['calls']['a']
            self.assertEqual(saved['state'], 'reservation_exceeded')
            self.assertGreater(saved['accounted_usd'], .25)
        with tempfile.TemporaryDirectory() as folder:
            asyncio.run(check(folder))


if __name__ == '__main__':
    unittest.main()
