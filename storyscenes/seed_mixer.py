#!/usr/bin/env python3
"""Ten hand-authored pools for reproducible storyworld design briefs.

Extends the pool-sampling approach in storyworlds/seed.py with a local copy of
its CHILDES vocabulary. Classic references are structural hints, not copied passages.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random

VERSION = 'classic_mix_v5'
VOCAB_PATH = Path(__file__).with_name('childes_eng_na_vocab.txt')


def load_words(path):
    words = tuple(dict.fromkeys(line.split('\t', 1)[0] for line in path.read_text().splitlines()
                                if line.strip() and not line.startswith('#')))
    if len(words) < 3:
        raise ValueError('CHILDES vocabulary must contain at least three distinct words')
    return words


WORDS = load_words(VOCAB_PATH)
VOCAB_SHA256 = hashlib.sha256(VOCAB_PATH.read_bytes()).hexdigest()

# Each entry has a stable name and enough meaning to guide a small author model.
POOLS = {
    'references': [
        ('Stone Soup', 'An apparently useless ingredient draws reluctant people into making something together.'),
        ('The Tortoise and the Hare', 'An underestimated contender exploits the favorite’s mistaken assumptions.'),
        ('The Emperor’s New Clothes', 'Public agreement conceals private doubt until someone names the obvious.'),
        ('The Three Little Pigs', 'Different preparations meet the same test; vary who is actually at fault.'),
        ('The Town Musicians of Bremen', 'Unwanted companions combine their peculiar abilities into an unexpected advantage.'),
        ('The Lion and the Mouse', 'A tiny helper can repay a favor in a way the powerful character cannot manage.'),
        ('The Sorcerer’s Apprentice', 'A useful shortcut keeps working after its user wants it to stop.'),
        ('The Fisherman and His Wife', 'Each granted wish changes what the requester thinks is enough.'),
        ('The Princess and the Pea', 'An apparently trivial detail becomes decisive evidence in an unusual test.'),
        ('The Golden Goose', 'An accumulating, absurd procession accomplishes what solemn attempts could not.'),
        ('The Elves and the Shoemaker', 'Someone investigates a mysterious kindness and finds a way to reciprocate.'),
        ('The Ugly Duckling', 'A supposed defect changes meaning when the character finds a different context.'),
        ('The Fox and the Crow', 'Flattery persuades someone to demonstrate the very ability that costs them their prize.'),
        ('The Wind and the Sun', 'Rivals discover that their competing methods change another person’s response.'),
        ('The Boy Who Cried Wolf', 'Earlier inventions change whether later evidence is believed.'),
        ('Alice’s Adventures in Wonderland', 'A curious child tests the logic of a world that takes strange rules seriously.'),
    ],
    'motives': [
        ('prove_it', 'Prove a supposedly impossible claim.'),
        ('belong', 'Join a group without giving up a peculiar identity.'),
        ('outdo', 'Outdo a friendly rival at an absurdly specific skill.'),
        ('conceal', 'Keep an embarrassing but harmless mistake secret.'),
        ('investigate', 'Find out why an ordinary thing has begun behaving strangely.'),
        ('repay', 'Repay a favor when the benefactor insists they need nothing.'),
        ('liberate', 'Free someone or something from a foolish restriction.'),
        ('invent', 'Build something nobody has thought worth building.'),
        ('recognition', 'Get credit for an achievement everyone misunderstands.'),
        ('surprise', 'Arrange a surprise without being caught arranging it.'),
        ('bargain', 'Win an apparently hopeless bargain.'),
        ('keep_promise', 'Keep an extravagant promise whose difficulty was overlooked.'),
    ],
    'kernels': [
        ('Detective', 'An observable clue distinguishes rival explanations; a character tests one.'),
        ('Cautionary', 'A tempting choice creates a consequence the chooser must live with or repair; no closing sermon.'),
        ('Trickster', 'Someone exploits another character’s assumption; let the target have agency.'),
        ('LiteralWish', 'A wish is fulfilled literally, exposing a gap between its wording and intent.'),
        ('RoleReversal', 'The helper needs help, the judge is tested, or the underestimated character sets the terms.'),
        ('BoastAndTest', 'A public boast attracts a concrete test the speaker did not anticipate.'),
        ('MistakenIdentity', 'A plausible misidentification changes behavior until physical evidence overturns it.'),
        ('UnlikelyAlliance', 'Two incompatible wants temporarily align around one problem.'),
        ('Escalation', 'Repeating an initially useful move makes its consequences grow.'),
        ('Reciprocity', 'A small earlier favor becomes consequential in an unexpected form.'),
        ('ForbiddenQuestion', 'Asking a discouraged question exposes why the rule exists.'),
        ('Transformation', 'A changed ability or form creates both an advantage and a new difficulty.'),
        ('Rescue', 'The obstacle to freeing someone requires an unconventional use of an established ability.'),
        ('ContestOfWits', 'Success depends on reframing the terms of a contest.'),
    ],
    'themes': [
        ('FireAndLaughter', 'Let warmth, sparks, or fire interact causally with laughter or comic surprise.'),
        ('SunAndMoon', 'Day and night, borrowed light, or celestial rivalry matters to the incident.'),
        ('NamesAndPromises', 'A name, title, or exact promise changes what someone can claim.'),
        ('ShadowsAndReflections', 'A shadow or reflection becomes a clue, disguise, or misleading witness.'),
        ('SmallAndGreat', 'Scale makes an apparent weakness useful and an apparent strength inconvenient.'),
        ('GiftsAndDebts', 'Receiving something changes a relationship or obligation.'),
        ('DoorsAndThresholds', 'Crossing a boundary changes a rule or reveals a different viewpoint.'),
        ('HungerAndAbundance', 'Too much and too little create different problems around the same resource.'),
        ('VoicesAndSilence', 'A missing sound, an echo, or an unexpected voice changes what is believed.'),
        ('LostAndFound', 'Finding what was sought changes what the seeker actually wants.'),
        ('WeatherAndWishes', 'A wish for different weather has an unforeseen beneficiary or cost.'),
        ('DreamAndWaking', 'A dream inspires a testable waking ambition; distinguish dream events from physical ones.'),
    ],
    'casts': [
        ('dragon_sibling', 'A young dragon and a skeptical younger sibling.'),
        ('fox_tortoise', 'A persuasive fox and a literal-minded tortoise.'),
        ('inventor_magpie', 'A child inventor and a magpie who claims to be an expert.'),
        ('giant_mouse', 'A considerate young giant and a mouse with enormous plans.'),
        ('apprentice_cat', 'An impatient apprentice and a cat with its own research project.'),
        ('rival_siblings', 'Two affectionate siblings who disagree about what counts as winning.'),
        ('mayor_child', 'A theatrical mayor and a child who asks inconveniently precise questions.'),
        ('moth_owl', 'A curious moth and an owl who is tired of being called wise.'),
        ('donkey_poet', 'A practical donkey and a would-be poet with a magnificent boast.'),
        ('newcomer_keeper', 'An audacious newcomer and a keeper who knows the local rules too well.'),
    ],
    'settings': [
        ('cloud_harbor', 'A harbor where small clouds are moored.'),
        ('night_market', 'A market that opens only after sunset.'),
        ('clocktower', 'A clocktower with an unreliable reputation for punctuality.'),
        ('orchard', 'An orchard at the edge of a talkative village.'),
        ('tiny_museum', 'A museum of things adults consider unimportant.'),
        ('rooftops', 'Connected rooftops above a busy town.'),
        ('forest_inn', 'An inn at a crossroads in the forest.'),
        ('tide_island', 'A little island accessible only at low tide.'),
        ('workshop', 'A workshop preparing for an invention fair.'),
        ('library', 'A library with an especially peculiar lending rule.'),
        ('walk_to_school', 'Walking to school with a friend and noticing something along the way.'),
        ('school_bus', 'Riding the school bus and choosing where to sit.'),
        ('first_school_day', 'Arriving at a new school and meeting classmates.'),
        ('school_bag', 'Packing a school bag and deciding what deserves a place in it.'),
        ('show_and_tell', 'Choosing something to bring for show-and-tell.'),
        ('class_project', 'Making a classroom project with a partner who has a different idea.'),
        ('recess', 'Deciding what to play during recess.'),
        ('school_lunch', 'Opening lunchboxes and talking around the lunch table.'),
        ('class_photo', 'Getting ready for the class photograph.'),
        ('lost_property', 'Looking through the school lost-property box.'),
        ('school_play', 'Practicing a small part in a school play.'),
        ('after_school', 'Meeting friends after school with an afternoon still to plan.'),
        ('grocery_trip', 'Going to the grocery store with a short shopping list.'),
        ('choose_snack', 'Choosing a snack from several equally tempting possibilities.'),
        ('buy_present', 'Looking for a birthday present with a small amount of money.'),
        ('bakery_queue', 'Waiting at a bakery and choosing something from the display.'),
        ('market_stall', 'Browsing a neighborhood market and talking with a stallholder.'),
        ('try_shoes', 'Trying on new shoes and comparing how they feel.'),
        ('toy_shop', 'Visiting a toy shop with a friend who likes very different toys.'),
        ('return_purchase', 'Taking a purchase back to a shop with its receipt.'),
        ('hide_and_seek', 'Playing hide-and-seek in a familiar place.'),
        ('tag', 'Organizing a game of tag with children of different speeds.'),
        ('hopscotch', 'Drawing a hopscotch course in chalk and trying it out.'),
        ('jump_rope', 'Playing jump rope while inventing a counting song.'),
        ('tic_tac_toe', 'Playing tic-tac-toe and trying to predict the next move.'),
        ('checkers', 'Playing checkers with someone who has a favorite strategy.'),
        ('chess', 'Learning a new chess move and trying it in a friendly game.'),
        ('card_game', 'Playing a familiar card game with a newly invented house rule.'),
        ('board_game', 'Setting up a board game and choosing who goes first.'),
        ('charades', 'Acting out clues in a game of charades.'),
        ('simon_says', 'Taking turns leading a game of Simon Says.'),
        ('scavenger_hunt', 'Making clues for a small scavenger hunt.'),
        ('video_coop', 'Playing a cooperative videogame where the players have different abilities.'),
        ('video_level', 'Trying a tricky videogame level with a friend watching.'),
        ('video_build', 'Building a shared house or town in a creative videogame.'),
        ('video_race', 'Playing a racing videogame and experimenting with different routes.'),
        ('video_puzzle', 'Solving a videogame puzzle by testing competing ideas.'),
        ('video_avatar', 'Choosing an avatar and giving it an elaborate name.'),
        ('video_controller', 'Sharing one controller and deciding when to swap players.'),
        ('video_real_world', 'Trying to adapt a favorite videogame into a backyard game; distinguish game rules from reality.'),
        ('choose_book', 'Choosing a book when its cover and title suggest different things.'),
        ('read_aloud', 'Reading aloud together and giving the characters different voices.'),
        ('library_visit', 'Visiting the local library to look for a particular kind of book.'),
        ('bedtime_reading', 'Reading at bedtime and trying to guess what happens on the next page.'),
        ('lend_book', 'Lending a favorite book to a friend and wondering what they will think.'),
        ('comic_reading', 'Reading a comic together and noticing different details in the pictures.'),
        ('make_book', 'Making a little book with drawings, folded pages, and a title.'),
        ('book_club', 'Talking about a book when everyone has a different favorite character.'),
        ('make_breakfast', 'Making breakfast together and choosing what goes on the table.'),
        ('bake_cookies', 'Baking cookies and choosing shapes for the dough.'),
        ('tidy_room', 'Tidying a bedroom and rediscovering something under the bed.'),
        ('blanket_fort', 'Building a blanket fort with an ambitious floor plan.'),
        ('sock_pairs', 'Matching socks from the laundry and investigating an odd one.'),
        ('set_table', 'Setting the table for a visitor with a surprise to announce.'),
        ('pet_care', 'Looking after a familiar pet with its own daily preferences.'),
        ('houseplant', 'Choosing a place for a houseplant and watching it over several days.'),
        ('birthday_party', 'Planning games for a birthday party.'),
        ('visit_grandparent', 'Visiting a grandparent and asking about an unfamiliar old object.'),
        ('sleepover', 'Having a first sleepover and comparing bedtime routines.'),
        ('rainy_afternoon', 'Finding something to do together on a rainy afternoon indoors.'),
        ('bike_ride', 'Going on a bike ride and choosing a destination.'),
        ('playground_visit', 'Meeting a new playmate at the playground.'),
        ('sandcastle', 'Building neighboring sandcastles at the beach.'),
        ('ball_game', 'Starting a ball game with an improvised team.'),
        ('bus_ride', 'Taking a local bus to visit someone.'),
        ('train_trip', 'Taking a train trip and watching the view change.'),
        ('family_walk', 'Going on a family walk with different ideas about the best route.'),
        ('swimming_lesson', 'Attending a swimming lesson and recognizing someone from elsewhere.'),
        ('music_practice', 'Practicing an instrument while someone nearby tries to guess the tune.'),
        ('park_picnic', 'Having a picnic in the park beside another family.'),
        ('puddle_walk', 'Taking a walk after rain and inspecting puddle reflections.'),
        ('garden_seeds', 'Planting seeds and deciding how to label the little pots.'),
        ('doctor_checkup', 'Going to the doctor for a checkup with a question of one’s own.'),
        ('doctor_waiting_room', 'Waiting for a doctor’s appointment and meeting another child.'),
        ('doctor_describe_symptoms', 'Visiting the doctor and finding words to explain how something feels.'),
        ('doctor_instruments', 'Noticing the unfamiliar instruments in a doctor’s room and asking about them.'),
        ('vaccination_visit', 'Going with a parent to a vaccination appointment and deciding what to bring along.'),
        ('dentist_checkup', 'Visiting the dentist for a checkup and comparing the chair to other kinds of seats.'),
        ('loose_tooth', 'Showing a loose tooth to a grown-up and wondering when it will come out.'),
        ('eye_test', 'Going for an eye test and looking at the pictures and letters.'),
        ('choose_glasses', 'Trying on glasses and deciding which pair feels like oneself.'),
        ('hearing_test', 'Going to a hearing appointment and noticing the different sounds.'),
        ('physiotherapy_visit', 'Going to a physiotherapy appointment with a familiar practitioner.'),
        ('hospital_visit', 'Visiting a family member in hospital with a drawing and some news from home.'),
        ('pharmacy_pickup', 'Accompanying a parent to collect a prescription from the pharmacy.'),
        ('vet_checkup', 'Taking a pet to the vet and watching how it reacts to the waiting room.'),
        ('haircut', 'Getting a haircut and explaining the hairstyle one has in mind.'),
        ('post_parcel', 'Taking a parcel to the post office and imagining its journey.'),
        ('shoe_repair', 'Bringing a favorite pair of shoes to be repaired.'),
        ('bike_repair', 'Taking a bicycle to a repair shop and describing an odd noise.'),
        ('laundromat', 'Visiting a laundromat and watching the clothes turn behind the round windows.'),
        ('tailor_visit', 'Having a costume adjusted before a special occasion.'),
        ('passport_photo', 'Having a photograph taken for an official document.'),
        ('community_class', 'Trying a new class at the community center.'),
        ('meet_neighbor', 'Welcoming a new neighbor and learning how to pronounce their name.'),
        ('family_appointment', 'Accompanying a grown-up on an appointment and bringing something to do while waiting.'),
    ],
    'props': [
        ('bell', 'A bell whose sound is easily mistaken for something else.'),
        ('map', 'A map with one apparently impossible landmark.'),
        ('boots', 'A pair of boots with a disputed history.'),
        ('lantern', 'A lantern with an unusual but consistent limitation.'),
        ('spoon', 'A spoon someone insists is valuable.'),
        ('ribbon', 'A ribbon that serves as a title, token, or proof.'),
        ('key', 'A key that fits something unexpected.'),
        ('mirror', 'A small mirror that shows an easily overlooked detail.'),
        ('basket', 'A basket whose contents are not what its owner expects.'),
        ('hat', 'A hat that people recognize before they recognize its wearer.'),
    ],
    'complications': [
        ('wrong_credit', 'The wrong person gets credit, and initially likes it.'),
        ('both_right', 'Two apparently incompatible accounts are both partly right.'),
        ('help_backfires', 'A sincere attempt to help makes the central problem more interesting.'),
        ('witness', 'The only witness is normally considered unreliable.'),
        ('success_cost', 'The first success makes the original goal less desirable.'),
        ('repeated_failure', 'Two attempts fail differently; their evidence enables a third approach.'),
        ('unexpected_owner', 'The disputed object belongs to someone neither rival considered.'),
        ('secret_agreement', 'An apparent opponent is secretly trying to achieve part of the same goal.'),
        ('deadline', 'An approaching event changes which solutions remain possible.'),
        ('literal_rule', 'Someone obeys a rule exactly and produces a result its author never intended.'),
    ],
    'styles': [
        ('dialogue', 'Dialogue-led prose: competing voices carry the action; keep speakers identifiable.'),
        ('rhyme', 'Short rhyming couplets with clear causal meaning and concrete details.'),
        ('refrain', 'Prose with a short repeated refrain whose meaning changes at the end.'),
        ('tall_tale', 'A cheerful tall tale; establish exaggerated rules and keep them consistent.'),
        ('deadpan', 'Understated, matter-of-fact narration of an increasingly absurd situation.'),
        ('fireside', 'An inviting oral-tale voice with one well-timed aside to the listener.'),
        ('mystery', 'A playful mystery voice that lets the reader notice the clue before the explanation.'),
        ('comic_fable', 'A compact comic fable with vivid actions; leave the moral unstated.'),
        ('sound_play', 'Rhythmic prose with purposeful sound effects and occasional internal rhyme.'),
        ('first_person', 'A first-person participant with a distinctive voice; preserve who actually knows each fact.'),
    ],
    'endings': [
        ('reversal', 'The apparent loser gets something the winner now envies.'),
        ('small_victory', 'A smaller but more personally meaningful ambition succeeds.'),
        ('comic_cost', 'The plan works, with a harmless comic cost its author cannot deny.'),
        ('shared_secret', 'Former rivals share a secret that changes their relationship.'),
        ('reframed_prize', 'The disputed prize becomes useful for an unexpected purpose.'),
        ('earned_surprise', 'An overlooked earlier detail supplies the final surprise.'),
        ('repair', 'A mistake is repaired through a clever action, without a speech about the lesson.'),
        ('new_question', 'The immediate problem resolves and leaves a delightful new question.'),
        ('generous_trick', 'A trick produces a benefit even its target can appreciate.'),
        ('exposed_boast', 'The boast is exposed, but its owner finds a funny, face-saving way forward.'),
    ],
}


def sample(seed, index=0):
    rng = random.Random(seed)
    mix = {}
    for pool in rng.sample(list(POOLS), 3):
        key, hint = rng.choice(POOLS[pool])
        mix[pool] = [dict(id=key, hint=hint)]
    words = rng.sample(WORDS, rng.randint(1, 3))
    lines = ['Compose one fresh storyworld from these three ingredients.']
    for pool, items in mix.items():
        item = items[0]
        lines.append(pool.upper() + ': ' + item['id'] + ': ' + item['hint'])
    lines.append('Connect these ingredients in one coherent situation. Invent the remaining details. '
                 'Keep it warm, playful and understandable to ages 5–8.')
    lines.append('Required words: ' + ', '.join(words) + '. Use each naturally in every generated story.')
    return dict(index=index, seed=seed, theater=f'mix_{index:05d}', world_id=f'mix_{index:05d}',
                seed_protocol=VERSION, seed_mix=mix, words=words,
                vocabulary_sha256=VOCAB_SHA256, premise='\n'.join(lines))


def briefs_for(seed, count):
    rng = random.Random(seed)
    return [sample(rng.getrandbits(64), i) for i in range(count)]


def prose_directions(brief):
    mix = brief.get('seed_mix')
    words = brief.get('words', [])
    if not mix and not words:
        return ''
    return ('\nSEED STYLE AND STORY INTENT (retain within the validated mechanics). '
            'Use every required word naturally in each generated story:\n' + json.dumps(
                dict(ingredients=mix or {}, required_words=words), ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=20260909)
    parser.add_argument('-n', '--count', type=int, default=10)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.count < 1: parser.error('count must be positive')
    rows = briefs_for(args.seed, args.count)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
        args.out.with_suffix('.md').write_text('\n\n'.join('## '+r['world_id']+'\n\n'+r['premise'] for r in rows)+'\n')
        print(f'Wrote {len(rows)} mixed briefs to {args.out}')
    else:
        for row in rows: print(json.dumps(row, ensure_ascii=False))


if __name__ == '__main__': main()
