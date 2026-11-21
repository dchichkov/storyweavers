"""Story framing preserves native execution and exposes normalized word choices."""
from copy import deepcopy
import unittest
from contextlib import redirect_stdout
import io
from unittest.mock import patch

from .plot_continuation import catalogue,run
from .story_memory import annotate
from .story_presentation import present,add_presentation
from .storytelling.runtime import generate,replay,SCENARIOS
from .storytelling.qa import questions


class PresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pool=catalogue([annotate(generate('pottery',3006))])
        cls.raw=run(cls.pool,'adapt_gift',seed=7,presentation=False)

    def test_default_presentation_preserves_native_story_and_replay(self):
        framed=run(self.pool,'adapt_gift',seed=7)
        for key in ('rows','decisions','final_world','plot','summary','units','raw_story'):
            self.assertEqual(framed[key],self.raw[key])
        self.assertEqual(framed,present(self.raw))
        self.assertEqual(framed,present(framed))
        self.assertTrue(framed['story'].startswith(framed['title']+'\n\n'))
        for row in framed['rows']:self.assertTrue(replay(row))

    def test_normalized_joint_choices_and_grounded_references(self):
        original=deepcopy(self.raw);seen={role:set() for role in ('title','opening','closing')}
        for seed in range(24):
            r=present(self.raw,seed=seed)
            for role in seen:
                section=r['presentation'][role];seen[role].update(section['styles'])
                self.assertAlmostEqual(sum(a['probability'] for a in section['alternatives']),1.)
                for step in section['trace']:
                    self.assertAlmostEqual(sum(c['probability'] for c in step['choices']),1.)
                    self.assertAlmostEqual(sum(c['probability'] for c in step['annotated_choices']),1.)
                    self.assertAlmostEqual(sum(c['probability'] for c in step['selected_attributes']),1.)
                for attrs in section['attributes'].values():
                    self.assertEqual(attrs['narration_role'],role)
                    self.assertLessEqual(set(attrs['referents']),self.raw['final_world']['entities'].keys())
                    if attrs['entity']:self.assertIn(attrs['entity'],attrs['referents'])
        self.assertEqual(self.raw,original)
        self.assertGreaterEqual(len(seen['title']),3)
        self.assertEqual(seen['opening'],{'traditional','everyday','storyteller','immediate'})
        self.assertEqual(seen['closing'],{'the_end','storyteller','final_image'})

    def test_explicit_and_native_boundary_forms(self):
        classic=present(self.raw,opening_style='traditional',closing_style='the_end')
        self.assertIn('\n\nOnce upon a time, Nia was at the workshop.\n\n',classic['story'])
        self.assertTrue(classic['story'].endswith('\n\nThe End.'))
        direct=present(self.raw,opening_style='immediate',closing_style='final_image')
        self.assertEqual(direct['story'],direct['title']+'\n\n'+self.raw['story'])
        ending=direct['presentation']['closing']
        self.assertEqual({a['source_event'] for a in ending['attributes'].values()},
                         {self.raw['rows'][-1]['scenes'][-1]['event_id']})

    def test_unfinished_and_empty_runs_cannot_claim_an_ending(self):
        pool=catalogue([annotate(generate('costume',3007))])
        partial=run(pool,'adapt_gift',seed=7,lookahead=False)
        self.assertFalse(partial['summary']['success'])
        self.assertEqual(partial['presentation']['status'],'unfinished')
        self.assertEqual({a['style'] for a in partial['presentation']['closing']['alternatives']},
                         {'continued','unfinished'})
        with self.assertRaises(ValueError):present(partial,closing_style='the_end')
        empty=run([],'adapt_gift')
        self.assertEqual(empty['story'],'')
        self.assertEqual(empty['presentation']['status'],'no_narrative')

    def test_opening_uses_initial_state_title_can_use_final_object(self):
        r=deepcopy(self.raw);obj=r['plot']['bindings']['object']
        r['final_world']['entities']['nia']['location']='elsewhere'
        r['final_world']['entities'][obj]['noun']='bowl'
        framed=present(r,title_style='object',opening_style='traditional')
        self.assertEqual(framed['title'],'The Bowl')
        self.assertEqual(framed['presentation']['opening']['text'],
                         'Once upon a time, Nia was at the workshop.')
        with self.assertRaises(ValueError):present(r,opening_style='rainy_morning')

    def test_source_attachment_preserves_tokens_qa_and_display_offsets(self):
        row=generate('pottery',7,beat_budget=2,token_annotations=True)
        original=deepcopy(row);qa=questions(row,6);memory=annotate(row)
        framed=add_presentation(row,opening_style='traditional',closing_style='the_end')
        self.assertEqual(row,original)
        for key in original:
            if key not in {'title','presentation','presented_story'}:
                self.assertEqual(framed[key],original[key],key)
        self.assertEqual(questions(framed,6),qa)
        self.assertEqual(annotate(framed),memory)
        self.assertTrue(replay(framed))
        offset=framed['presentation']['body_offset']
        self.assertEqual(framed['presented_story'][offset:offset+len(row['story'])],row['story'])
        for scene in row['scenes']:
            self.assertEqual(framed['presented_story'][offset+scene['start']:offset+scene['end']],scene['text'])
        self.assertTrue(framed['presented_story'].endswith('The End.'))
        self.assertEqual(add_presentation(row),add_presentation(add_presentation(row)))

    def test_all_source_worlds_frame_without_inventing_plot_success(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                row=generate(scenario,7)
                framed=add_presentation(row)
                self.assertNotIn('plot',framed)
                self.assertEqual(framed['presentation']['completion_basis'],'native_ended_flag')
                self.assertEqual(framed['presentation']['status'],'complete')
                self.assertTrue(framed['presented_story'].startswith(framed['title']+'\n\n'))
                self.assertEqual(framed['story'],row['story'])

    def test_present_tense_does_not_gain_a_past_tense_opening(self):
        row=generate('repair',7,tense='present')
        framed=add_presentation(row)
        openings=framed['presentation']['opening']['alternatives']
        self.assertNotIn('traditional',{x['style'] for x in openings})
        self.assertTrue(all(' was ' not in x['text'] and 'Once upon' not in x['text'] for x in openings))
        with self.assertRaises(ValueError):present(row,opening_style='traditional')
        # A physical place admits a grounded present-tense setting sentence.
        initial=row['initial_world'];hero=initial['hero']
        initial['entities']['workshop']=dict(noun='workshop',kind='place')
        initial['entities'][hero]['location']='workshop'
        opening=present(row,opening_style='everyday')['presentation']['opening']['text']
        self.assertEqual(opening,'Ada is at the workshop.')

    def test_unrepresented_place_uses_identity_and_plural_mass_titles(self):
        row=generate('pottery',7)
        hero=row['initial_world']['hero'];place=row['initial_world']['entities'][hero]['location']
        self.assertNotIn(place,row['initial_world']['entities'])
        opening=present(row,opening_style='traditional')['presentation']['opening']['text']
        self.assertEqual(opening,'Once upon a time, there was someone named Bea.')
        for noun,number,expected in [('tomato seedling','plural','Tomato Seedlings'),('clay','mass','Clay')]:
            target=row['final_world']['entities'][row['initial_world']['target']]
            target.update(noun=noun,number=number)
            title=present(row,title_style='object')['title']
            self.assertEqual(title,'The '+expected)

    def test_real_plural_titles_use_authored_noun_forms(self):
        greenhouse=generate('greenhouse',701)
        target=greenhouse['final_world']['entities'][greenhouse['initial_world']['target']]
        self.assertEqual((target['noun'],target['number']),('tomato seedling','plural'))
        self.assertEqual(present(greenhouse,title_style='object')['title'],'The Tomato Seedlings')
        self.assertEqual(present(greenhouse,title_style='hero_and_object')['title'],'Nia and the Tomato Seedlings')
        # Seed source nouns may already be plural; their explicit lexical form
        # must win over the regular inflector.
        festival=generate('festival',701)
        festival['initial_world']['target']='flags'
        target=festival['final_world']['entities'][festival['initial_world']['target']]
        self.assertEqual(target['number'],'plural')
        self.assertEqual(present(festival,title_style='object')['title'],'The '+target['noun'].title())

    def test_source_final_image_requires_authored_last_visible_event(self):
        row=generate('pottery',7)
        framed=present(row,opening_style='immediate',closing_style='final_image')
        self.assertEqual(framed['story'],framed['title']+'\n\n'+row['story'])
        self.assertEqual({a['source_event'] for a in framed['presentation']['closing']['attributes'].values()},
                         {row['scenes'][-1]['event_id']})
        # A terminal flag by itself does not classify any prior scene as an image.
        row['scenes']=row['scenes'][:-1]
        with self.assertRaises(ValueError):present(row,closing_style='final_image')
        # An intentionally silent terminal event remains physically complete;
        # the ordinary text sign-off is available, without inventing an image.
        music=present(generate('music',7),closing_style='the_end')
        self.assertEqual(music['presentation']['status'],'complete')
        self.assertNotIn('final_image',{x['style'] for x in music['presentation']['closing']['alternatives']})

    def test_gift_title_requires_authored_gift_purpose_not_recipient_ownership(self):
        market=generate('market',41)
        self.assertEqual(market['final_world']['entities']['bag']['location'],'customer')
        with self.assertRaises(ValueError):present(market,title_style='gift')
        bakery=present(generate('bakery',41),title_style='gift')
        self.assertEqual(bakery['title'],'A Gift for Mr Hobb')

    def test_source_partial_empty_and_joined_fragment_endings(self):
        row=generate('repair',7)
        row['final_world']['flags'].remove('ended')
        partial=add_presentation(row)
        self.assertEqual(partial['presentation']['status'],'unfinished')
        with self.assertRaises(ValueError):present(row,closing_style='the_end')
        row['story']='';row.pop('raw_story',None);row['scenes']=[]
        empty=add_presentation(row)
        self.assertEqual(empty['presented_story'],'')
        self.assertEqual(empty['presentation']['status'],'no_narrative')
        fragment=self.raw['rows'][0]
        self.assertIn('ended',fragment['final_world']['flags'])
        self.assertEqual(add_presentation(fragment)['presentation']['status'],'unfinished')

    def test_cli_frames_by_default_with_raw_escape_hatch(self):
        from .storytelling.__main__ import main
        def invoke(*extra):
            output=io.StringIO()
            with patch('sys.argv',['storytelling','--scenario','pottery','--seed','7',*extra]),redirect_stdout(output):
                main()
            return output.getvalue()
        framed=invoke();raw=invoke('--raw')
        self.assertIn('\n\n',framed)
        self.assertIn(generate('pottery',7)['story'],framed)
        self.assertLess(len(raw),len(framed))


if __name__=='__main__':unittest.main()
