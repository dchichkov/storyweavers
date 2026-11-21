"""All twenty source stories covered, with physical, annotation and reuse gates."""
from copy import deepcopy
from pathlib import Path
import gzip
import json
import tempfile
import unittest

from .storytelling.runtime import SCENARIOS, LEGACY_SCENARIOS, generate, replay, setup, build_forest
from .storytelling.seed_worlds.engine import NAMES, pack
from .storytelling.seed_worlds.catalog import SEED_SCENARIOS, source_record
from .storytelling.qa import questions
from .storytelling.surface import detokenize
from .story_memory import annotate, retrieve, generate_retrieved, validate, load_documents
from .event_line_replay import paper_world
from .world import Frame

# These are story-specific conclusions, not just flags saying the engine ended.
END_STATES = {
 'bakery': [('window','open')], 'puppets':[('star','secure')],
 'seaside':[('book','sea_drawing'),('anemone','open')], 'snow':[('stove','warm'),('sled','free')],
 'picnic':[('blanket','folded'),('basket','safe')], 'market':[('bag','correct_weight'),('scale','zeroed')],
 'camp':[('rabbit','free')], 'orchard':[('branch','unbent'),('pear','trimmed')],
 'costume':[('cape','intact'),('hero','performed'),('helper','performed')],
 'pond':[('boat','tethered'),('net','intact')], 'repair':[('cart','repaired'),('wheel','smooth')],
 'museum':[('torch','fixed'),('shadow','small')], 'laundry':[('sheet','secured'),('sheet','clean')],
 'trail':[('card','complete'),('book','salamander_drawing'),('leni','included')],
 'festival':[('gate','clear'),('cart','passed_gate')], 'biscuit':[('biscuit','cool'),('biscuit','star_mark')],
}


class SeedWorldTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows={name:generate(name,3000,continuations='expanded',symbolic_heads=True) for name in NAMES}

 def test_full_twenty_sources_and_distinct_original_prototypes(self):
  self.assertEqual(len(SEED_SCENARIOS),20)
  self.assertEqual(set(SCENARIOS),set(SEED_SCENARIOS)|{'rescue','kite','key'})
  self.assertEqual(len(NAMES),16)
  self.assertEqual(set(LEGACY_SCENARIOS)&set(SEED_SCENARIOS),{'music','greenhouse','library','pottery'})
  for name in SEED_SCENARIOS:
   record=source_record(name)
   self.assertTrue(Path(record['path']).is_file())
   self.assertGreater(len(Path(record['path']).read_text().split()),500)

 def test_all_new_worlds_replay_and_meet_story_specific_conclusions(self):
  for name,row in self.rows.items():
   self.assertTrue(replay(row))
   for entity,state in END_STATES[name]:
    self.assertIn(state,row['final_world']['entities'][entity]['state'],name)
   self.assertIn('ended',row['final_world']['flags'])
   self.assertEqual(row['source_story'],source_record(name))

 def test_intact_annotation_preserves_all_tokens_and_source_provenance(self):
  for name,row in self.rows.items():
   doc=annotate(row);self.assertTrue(validate(doc))
   self.assertEqual(doc['source_story'],row['source_story'])
   self.assertEqual(doc['text'],row['story'])
   self.assertEqual(detokenize([t['token'] for t in doc['tokens']]),row['story'])
   self.assertTrue(all(t['candidates'] for t in doc['tokens']))
   self.assertEqual(len(doc['events']),len(row['final_world']['history']))
   self.assertTrue(any(e['mapping_rules'] and e['token_ids'] for e in doc['events']),name)

 def test_each_new_world_can_supply_a_live_underdefined_continuation(self):
  for name,row in self.rows.items():
   doc=annotate(row);world=paper_world()
   # A book on the bench permits the shared object-fetch variants too.
   world.entities['book'].location='bench'
   candidates=retrieve([doc],world,operations=['fetch'])
   self.assertTrue(candidates['candidates'],name)
   result=generate_retrieved([doc],world,operations=['fetch'],seed=7)
   self.assertEqual(result['status'],'complete')
   self.assertTrue(result['attribute_generation']['tokens'])

 def test_guards_fail_without_mutation_for_each_recorded_event(self):
  count=0
  for name,row in self.rows.items():
   p,w=setup(name,3000)
   for saved in row['final_world']['history']:
    frame=Frame(**{**saved['frame'],'cause_ids':tuple(saved['frame']['cause_ids'])})
    spec=p.events[frame.kind]
    variants=[]
    for entity in {frame.actor,frame.patient,frame.instrument} - {''}:
     altered=w.clone();del altered.entities[entity];variants.append(altered)
    for guard in spec['guards']:
     op,*args=guard;altered=w.clone()
     if op=='location':altered.entities[args[0]].location='absent_place'
     elif op=='state':altered.entities[args[0]].state.discard(args[1])
     elif op=='property':altered.entities[args[0]].properties.discard(args[1])
     elif op=='together':altered.entities[args[0]].location='absent_place'
     variants.append(altered)
    for altered in variants:
     before=altered.to_dict()
     with self.assertRaises(ValueError,msg=(name,frame.kind)):p.commit(altered,frame,'')
     self.assertEqual(altered.to_dict(),before);count+=1
    p.commit(w,frame,saved['sentence'])
  self.assertGreater(count,500)

 def test_prediction_purity_and_dialogue_qa(self):
  for name,row in self.rows.items():
   p,w=setup(name);before=w.to_dict();build_forest(p,w,predict_attributes=True)
   self.assertEqual(w.to_dict(),before)
   self.assertGreaterEqual(len({e for s in row['scenes'] for e in s['speakers']}),2)
   qa=questions(row)
   self.assertGreaterEqual(len(qa),5)
   self.assertGreaterEqual(len({q['kind'] for q in qa}),3)
   self.assertTrue(all(q['answer'].count('.')>=2 for q in qa))
   for q in qa:
    self.assertTrue(q['entity_ids'] and q['event_ids'])
    for evidence in q['evidence']:
     self.assertEqual(row['story'][evidence['start']:evidence['end']],evidence['text'])

 def test_authored_branches_really_change_entity_state(self):
  for name in NAMES:
   p=pack(name);groups={}
   for event in p.events.values():
    for flag in event['adds']:
     if flag.endswith('_done'):groups.setdefault(flag,[]).append(event)
   forks=[es for es in groups.values() if len(es)>1]
   self.assertTrue(forks,name)
   for alternatives in forks:
    self.assertEqual(len({str(e['effects']) for e in alternatives}),len(alternatives),name)

 def test_present_tense_and_no_attribute_mode_still_replay(self):
  for name in NAMES:
   row=generate(name,7,tense='present',predict_attributes=False)
   self.assertTrue(replay(row));self.assertNotIn('attribute_generation',row)

 def test_memory_loader_keeps_branches_missing_from_a_single_preview(self):
  docs=[annotate(generate('kite',seed,continuations='expanded',symbolic_heads=True))
        for seed in (3000,3007)]
  self.assertTrue(any(e['kind']=='mend' for e in docs[0]['events']))
  self.assertFalse(any(e['kind']=='mend' for e in docs[1]['events']))
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   preview=root/'kite.memory.json';preview.write_text(json.dumps(docs[1]))
   self.assertEqual(load_documents(root),[docs[1]])
   archive=root/'stories.memory.jsonl.gz'
   with gzip.open(archive,'wt') as f:
    for doc in docs:f.write(json.dumps(doc)+'\n')
   loaded=load_documents(root)
   self.assertEqual(loaded,docs)
   self.assertEqual(load_documents(archive),docs)
   self.assertTrue(any(e['kind']=='mend' for doc in loaded for e in doc['events']))
   archive.unlink();preview.unlink()
   with self.assertRaises(ValueError):load_documents(root)


if __name__=='__main__':unittest.main()
