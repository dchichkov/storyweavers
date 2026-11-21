"""Discrete rotation algebra, token coordinates, causal attention and grammar."""
from dataclasses import replace
import unittest

from .symbolic_heads.positions import (Position,SymbolicRotary,demo,percentages,
                                       position_tokens,positional_memory)


class SymbolicPositionTests(unittest.TestCase):
    def test_rotation_composes_and_inverts(self):
        r=SymbolicRotary();p=r.phase(37)
        self.assertEqual(r.rotate(r.rotate(p,8),13),r.rotate(p,21))
        self.assertEqual(r.rotate(r.rotate(p,8),-8),p)
        self.assertEqual(r.rotate(p,21),r.phase(58))

    def test_relative_phase_invariant_to_shared_translation(self):
        r=SymbolicRotary()
        for q,k in [(0,8),(5,1),(41,41),(200,7)]:
            expected=r.relative_phase(r.phase(q),r.phase(k))
            for offset in (3,800,20000):
                self.assertEqual(expected,r.relative_phase(r.phase(q+offset),r.phase(k+offset)))
            self.assertEqual(r.decode(expected),k-q)
            self.assertEqual(r.offset_match(r.phase(q),r.phase(k),k-q),1)

    def test_bounded_decode_and_alias_rejection(self):
        r=SymbolicRotary((5,7))
        for delta in range(-r.radius,r.radius+1):self.assertEqual(r.decode(r.phase(delta)),delta)
        self.assertEqual(r.phase(2),r.phase(2+r.cycle))
        with self.assertRaisesRegex(ValueError,'window'):
            r.relative(Position('s',0,0,0),Position('s',35,1,0))
        with self.assertRaisesRegex(ValueError,'coprime'):SymbolicRotary((4,8))

    def test_hierarchy_only_compares_local_offsets_within_sentence(self):
        r=SymbolicRotary();q=Position('s',13,3,1)
        previous=r.relative(q,Position('s',9,2,1))
        self.assertEqual(previous['token']['delta'],-4)
        self.assertEqual(previous['sentence']['delta'],-1)
        self.assertIsNone(previous['in_sentence'])
        same=r.relative(q,Position('s',12,3,0))
        self.assertEqual(same['in_sentence']['delta'],-1)
        with self.assertRaisesRegex(ValueError,'start'):r.relative(q,Position('s',12,3,5))
        with self.assertRaisesRegex(ValueError,'order'):r.relative(q,Position('s',12,4,0))
        with self.assertRaisesRegex(ValueError,'alignment'):r.relative(q,Position('other',9,2,1))

    def test_multiword_units_and_prefix_stability(self):
        first=[[{'token':'Lili'},{'token':'picked up','event':'obtain'},{'token':'the scissors'}]]
        a=position_tokens(first);b=position_tokens(first+[[{'token':'Then'},{'token':'she repaired it'}]])
        self.assertEqual(a,b[:len(a)]);self.assertEqual(a[1].position.token,1)
        self.assertEqual(a[2].position.in_sentence,2)
        self.assertEqual(len(a),3)

    def test_percentages_are_display_coordinates_not_append_stable(self):
        p=Position('s',1,0,1)
        self.assertEqual(percentages(p,story_units=3,sentence_units=3),{'text':50,'sentence':50})
        self.assertEqual(percentages(p,story_units=5,sentence_units=3)['text'],25)
        with self.assertRaises(ValueError):percentages(p,story_units=1,sentence_units=1)

    def test_attention_disambiguates_repeated_names_without_renaming(self):
        result=demo();sources=result['attention']['sources']
        self.assertEqual(len(sources),2)
        weights={result['payloads'][s['source_id']]['patient']:s['attention'] for s in sources}
        self.assertGreater(weights['tape'],weights['scissors'])
        self.assertAlmostEqual(sum(weights.values()),1)
        self.assertNotIn('glue',weights)
        self.assertEqual({result['payloads'][s['source_id']]['event'] for s in sources},{'obtain repair tool'})
        probs=result['reranked']['probabilities']
        self.assertEqual(set(probs),set(result['base']))
        self.assertAlmostEqual(sum(probs.values()),1)
        self.assertGreater(probs['patch'],probs['cut'])

    def test_mask_scope_duplicate_positions_and_sentence_gate(self):
        tokens=position_tokens([[{'token':'take','event':'obtain'}],[{'token':'repair','event':'repair'}]])
        sources,_,_=positional_memory(tokens,tokens[1].position,same_sentence=True)
        self.assertEqual(sources,[])
        sources,_,_=positional_memory(tokens,Position('elsewhere',2,2,0))
        self.assertEqual(sources,[])
        with self.assertRaisesRegex(ValueError,'duplicate'):
            positional_memory([tokens[0],tokens[0]],tokens[1].position)
        with self.assertRaisesRegex(ValueError,'window'):
            positional_memory(tokens,tokens[1].position,window=100000)

    def test_attention_weights_invariant_to_common_coordinate_shift(self):
        tokens=position_tokens([[{'token':'take','event':'obtain'}],[{'token':'repair','event':'repair'}]])
        q=Position('story',2,1,1)
        a,_,_=positional_memory(tokens,q)
        shifted=[replace(t,position=replace(t.position,token=t.position.token+100,sentence=t.position.sentence+10)) for t in tokens]
        b,_,_=positional_memory(shifted,replace(q,token=102,sentence=11))
        self.assertEqual([s.confidence for s in a],[s.confidence for s in b])


if __name__=='__main__':unittest.main()
