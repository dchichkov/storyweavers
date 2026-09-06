#!/usr/bin/env python3
"""
A small animal-story world about a county day, a moisture mix-up, and teamwork.

Seed words: toe-pl, moisture, county
Style: Animal Story
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

ANIMALS = ["fox", "badger", "rabbit", "duck", "goat", "raccoon", "mouse", "otter"]
NAMES = ["Pip", "Milo", "Nina", "Toby", "Clover", "Ruby", "Penny", "Junie"]
COUNTY_PLACES = [
    "the county barn",
    "the county orchard",
    "the county lane",
    "the county market shed",
]
MOISTURE_KINDS = ["dew", "rain", "mud", "pond-water"]
HELP_ITEMS = ["dry towel", "big leaf", "clean cloth", "warm blanket"]
MOISTURE_SCENES = {
    "dew": "dew shining on the grass",
    "rain": "fresh rain dripping from the roofs",
    "mud": "water held in patches of soft mud",
    "pond-water": "pond-water splashed beside the lane",
}

# In this county, "toe-pl" is the friendly shorthand painted beside a
# "toe-place line": the mark where each small participant waits for a turn.
INCIDENTS = [
    {
        "title": "seed-table scramble",
        "goal": "deliver labeled seed packets to the county garden table",
        "problem": "a dark wet trail curled from the toe-pl line toward three spilled packets",
        "guess": "the hero had stepped on the packets with muddy toes",
        "clue": "the prints were pointed, not paw-shaped, and stopped beneath a dripping watering can",
        "truth": "a loose can spout had sprinkled the table and knocked the packets down",
        "failed": "blotting the nearest packet only pushed its seeds toward the table edge",
        "roles": "one held the can upright, one sorted the labels, and one spread the seeds on a clean cloth",
        "solution": "They tightened the spout, matched every seed to its picture, and made a dry tray together",
        "ending": "By sunset, twelve neat seed rows made a green promise beside the bright toe-pl line",
        "safe": "the sorted seed packets",
    },
    {
        "title": "library-page alarm",
        "goal": "carry a picture book to the county reading tent",
        "problem": "round moisture spots appeared on the cover just after the hero crossed the toe-pl line",
        "guess": "the hero had splashed through a puddle while holding the book",
        "clue": "the spots smelled like mint and formed a circle exactly the size of a tea cup",
        "truth": "a wobbly refreshment table had tipped a cup onto the closed cover",
        "failed": "rubbing the cover quickly made the damp patch spread",
        "roles": "one steadied the table, one fetched absorbent paper, and one turned a quiet fan",
        "solution": "They pressed the cover gently, moved the drinks away, and built a level book stand",
        "ending": "That evening, dry pages rustled beneath lantern light while listeners curled around the toe-pl line",
        "safe": "the county picture book",
    },
    {
        "title": "berry-banner mystery",
        "goal": "hang a berry-colored banner above the county parade lane",
        "problem": "purple drops dotted the toe-pl line and the rolled banner looked damp",
        "guess": "the hero had hidden a squashed berry inside the banner",
        "clue": "the drops fell at even spaces beneath a nest tucked into the rain gutter",
        "truth": "rainwater tinted by old berries in the gutter had dripped onto the roll",
        "failed": "lifting the banner alone sent another gutter drop sliding down its edge",
        "roles": "one sheltered the roll, one cleared the gutter with a long brush, and one tied the dry end high",
        "solution": "They moved the banner, cleared the blocked gutter, and raised it together from both ends",
        "ending": "The clean banner snapped above the parade as tiny rain beads shone beyond the toe-pl line",
        "safe": "the berry-colored parade banner",
    },
    {
        "title": "map-case mix-up",
        "goal": "bring a trail map to the county nature walk",
        "problem": "the map case was moist and a winding line showed through its clear lid",
        "guess": "the hero had drawn a new path with a wet toe",
        "clue": "the winding line moved slowly and left no ink behind",
        "truth": "a tiny earthworm had sheltered beneath the case after the rain",
        "failed": "tilting the case toward the grass made the frightened worm curl tighter",
        "roles": "one shaded the worm, one lifted the lid, and one prepared a leafy patch of soil",
        "solution": "They opened the case flat, guided the worm onto a leaf, and dried the map without tearing it",
        "ending": "At dusk, the map led everyone home while a silver worm trail glimmered past the toe-pl line",
        "safe": "the county trail map",
    },
    {
        "title": "bell-rope puzzle",
        "goal": "ring the county lunch bell from behind the toe-pl line",
        "problem": "the bell rope felt wet and would not slide through its wooden guide",
        "guess": "the hero had soaked the rope by dragging it through a trough",
        "clue": "only the section beneath the barn eave held moisture, and bits of moss clung there",
        "truth": "an overflowing rain barrel had splashed the eave and swollen the rope fibers",
        "failed": "one hard tug tightened the swollen rope into a knot",
        "roles": "one loosened the knot, one moved the barrel spout, and one brought a spare dry cord",
        "solution": "They lowered the rope, dried it in loops, and threaded the spare cord through the guide",
        "ending": "The bell rang clear, and lunch baskets opened in a cheerful row behind the toe-pl line",
        "safe": "the county bell rope",
    },
    {
        "title": "painted-track confusion",
        "goal": "finish animal tracks for the county learning path",
        "problem": "one painted track had blurred into a wet blue oval beside the toe-pl line",
        "guess": "the hero had stepped on fresh paint before it dried",
        "clue": "the hero's toes were clean, but a blue feather rested against a sprinkler peg",
        "truth": "a bird had bumped the sprinkler, which sprayed moisture across the paint",
        "failed": "adding more blue paint made the oval wider and hid the track completely",
        "roles": "one shut the sprinkler, one outlined the old print, and one mixed a matching color",
        "solution": "They dried the board, traced the original stencil, and repainted the track in thin layers",
        "ending": "Morning sun revealed a crisp blue footprint and three proud helpers at the toe-pl line",
        "safe": "the painted learning path",
    },
    {
        "title": "picnic-cracker case",
        "goal": "set out crisp crackers for the county picnic",
        "problem": "one cracker box sagged with moisture near the toe-pl line",
        "guess": "the hero had left the lid open in the rain",
        "clue": "the lid was latched, while a trail of melting ice led from the lemonade tub",
        "truth": "the crowded ice tub had leaned against the box and soaked it from below",
        "failed": "stacking the box higher caused the soft bottom to bend",
        "roles": "one supported the box, one moved the ice tub, and one lined a basket with dry leaves",
        "solution": "They rescued the sealed cracker sleeves, rebuilt the table, and gave wet crumbs to the compost",
        "ending": "At picnic time, crisp crunches traveled down the blanket beyond the freshly dried toe-pl line",
        "safe": "the sealed picnic crackers",
    },
    {
        "title": "wool-ribbon riddle",
        "goal": "judge braided ribbons at the county craft show",
        "problem": "the hero's ribbon felt damp and shorter beside the toe-pl line",
        "guess": "the hero had secretly wetted it to make its colors brighter",
        "clue": "every damp strand came from the same end of the display rack",
        "truth": "mist from a nearby fern display had made the wool fibers curl",
        "failed": "pulling the ribbon straight stretched one braid unevenly",
        "roles": "one moved the fern mister, one measured the braid, and one pinned it loosely to a towel",
        "solution": "They let the wool dry naturally, compared it fairly, and marked a dry zone for every entry",
        "ending": "The ribbon kept its gentle curl, glowing red and gold above the toe-pl line",
        "safe": "the braided wool ribbon",
    },
    {
        "title": "lantern-flicker question",
        "goal": "light the safe path to the county evening concert",
        "problem": "a lantern flickered as moisture gathered on its glass by the toe-pl line",
        "guess": "the hero had sprayed the lantern while washing the path",
        "clue": "the path was dusty, but cool air puffed from a cracked cellar vent below the lamp",
        "truth": "warm air around the lantern met the cool vent air and formed condensation",
        "failed": "wiping the glass without moving the lantern made the fog return",
        "roles": "one covered the vent safely, one dried the cool glass, and one shifted the lantern stand",
        "solution": "They moved the light away from the draft and checked every lantern as a team",
        "ending": "A steady chain of golden lights guided families past the toe-pl line under the first star",
        "safe": "the county path lanterns",
    },
    {
        "title": "flour-print surprise",
        "goal": "carry a flour sack to the county baking booth",
        "problem": "damp toe-shaped marks crossed the sack beside the toe-pl line",
        "guess": "the hero had climbed onto the flour with wet feet",
        "clue": "the marks had no claws and repeated exactly like the toe-shaped stamp at the sign booth",
        "truth": "a wet sign-maker's stamp had fallen and bounced across the sack",
        "failed": "brushing the marks scattered flour through a tiny loosened seam",
        "roles": "one pinched the seam closed, one found the stamp, and one brought a clean outer sack",
        "solution": "They nested the flour in the clean sack, repaired the seam, and returned the stamp",
        "ending": "Soon warm rolls rose like little clouds, and the clean stamp dried beside the toe-pl line",
        "safe": "the county flour sack",
    },
    {
        "title": "nest-box misunderstanding",
        "goal": "mount a wooden nest box for the county bird garden",
        "problem": "the box floor held moisture and two wood shavings clung to the hero's toes",
        "guess": "the hero had waded through the pond while carrying the box",
        "clue": "the outside stayed dry, but a leaf was wedged beneath the roof hinge",
        "truth": "the leaf had funneled overnight dew through the hinge into the box",
        "failed": "shaking the box freed the leaf but splashed water onto the nesting straw",
        "roles": "one saved the dry straw, one cleared the hinge, and one tested the roof with a cup of water",
        "solution": "They dried the floor, fitted a tiny rain guard, and replaced the straw together",
        "ending": "A wren inspected the snug box while the team watched quietly from the toe-pl line",
        "safe": "the wooden nest box",
    },
    {
        "title": "race-card reversal",
        "goal": "deliver numbered cards for the county relay",
        "problem": "card six was damp and stuck to card nine at the toe-pl line",
        "guess": "the hero had mixed the cards after stepping in a puddle",
        "clue": "the hero's feet were dry, while a leaky flower vase stood over the card tray",
        "truth": "the vase had dripped between the cards and joined the two numbers together",
        "failed": "pulling the cards apart at once began to peel a corner",
        "roles": "one emptied the vase, one slid clean paper between the cards, and one copied the numbers",
        "solution": "They dried the cards under light boards, checked the order, and moved flowers to another table",
        "ending": "The relay began on time, with cards fluttering cleanly and toes lined up at the toe-pl mark",
        "safe": "the numbered relay cards",
    },
]

OPENINGS = [
    "County Day began with carts squeaking along the lane and flags waking in the breeze.",
    '"Places, please!" called the steward as neighbors gathered for County Day.',
    "A patch of moisture became the day's first mystery before County Day had properly begun.",
    "Just beyond the county gate, every helper had a job and every job had a careful place.",
    "The little painted toe-pl mark looked ordinary, but it would soon help solve an important mix-up.",
    "Clouds had cleared over the county grounds, leaving beads of moisture on every rail.",
    "County Day was meant for sharing work, stories, and lunch, not for blaming anyone in a hurry.",
    "A bell, a busy lane, and one puzzling wet mark started a surprising County Day adventure.",
]

REACTIONS = [
    '"Please ask before deciding it was me," the hero said, taking one slow breath.',
    'The hero felt a hot prickle of hurt, then said, "Let us inspect the clues together."',
    '"Wet toes are not proof," the hero replied. "We need to learn where the moisture began."',
    'The helper noticed the hero grow quiet and said, "I may have guessed too quickly."',
    'Instead of arguing, the hero drew a small circle around each clue so nobody would lose it.',
    '"We can fix the problem after we understand it," said the hero, and the helper nodded.',
    'The accusation stung, but the hero asked everyone to compare the marks carefully.',
    'The helper lowered their ears. "I saw only the wet part, not the whole story," they admitted.',
]

APOLOGIES = [
    '"I am sorry I guessed instead of asking," said the helper. "Thank you for solving it with me."',
    'The helper apologized plainly, and the hero accepted after they agreed to check evidence next time.',
    '"You deserved a question, not an accusation," the helper said, and offered the first helping paw.',
    'The hero explained how the guess had hurt; the helper listened, apologized, and helped make it right.',
    'They replaced blame with a promise: pause, ask, inspect, and then act together.',
    'The helper admitted the mistake in front of the team, and the hero invited everyone into the repair.',
    '"A damp clue can point the wrong way," the helper said. "Next time I will listen first."',
    'Once the truth was clear, the helper apologized and wrote ASK FIRST on the team checklist.',
]

LESSONS = [
    "They learned that teamwork begins with listening, especially when the first guess feels obvious.",
    "The team discovered that clues explain more when friends examine them from different sides.",
    "No one animal had solved everything; careful questions and shared jobs had changed the outcome.",
    "They remembered that moisture can travel, so a wet mark does not always reveal who caused it.",
    "The best repair was not merely drying the object, but repairing trust after the misunderstanding.",
    "From then on, County Day helpers checked the cause before choosing the cure.",
    "Their work proved that an apology matters most when it is followed by helpful action.",
    "A mistaken idea had divided two friends for a moment; evidence and teamwork brought them together.",
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    species: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    wears: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords_moisture: bool = True


@dataclass
class Mood:
    misunderstanding: bool = True
    teamwork: bool = True


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_species: str
    helper_name: str
    helper_species: str
    moisture: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mood: Mood) -> None:
        self.setting = setting
        self.mood = mood
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


def tell(params: StoryParams) -> World:
    world = World(Setting(params.place), Mood())
    hero = world.add(Entity(id=params.hero_name, kind="character", species=params.hero_species))
    helper = world.add(Entity(id=params.helper_name, kind="character", species=params.helper_species))
    rng_seed: object = params.seed
    if rng_seed is None:
        rng_seed = "|".join(
            [params.place, params.hero_name, params.hero_species, params.helper_name, params.helper_species, params.moisture]
        )
    rng = random.Random(rng_seed)
    incident = {
        key: value.replace("the hero", hero.id).replace("The hero", hero.id)
        for key, value in rng.choice(INCIDENTS).items()
    }
    opening = rng.choice(OPENINGS)
    reaction = rng.choice(REACTIONS).replace("the hero", hero.id).replace("The hero", hero.id)
    reaction = reaction.replace("the helper", helper.id).replace("The helper", helper.id)
    apology = rng.choice(APOLOGIES).replace("the hero", hero.id).replace("The hero", hero.id)
    apology = apology.replace("the helper", helper.id).replace("The helper", helper.id)
    lesson = rng.choice(LESSONS)
    help_item = rng.choice(HELP_ITEMS)
    moisture_scene = MOISTURE_SCENES[params.moisture]
    clue_order = rng.choice(
        [
            "looked low, then high",
            "worked backward from the wettest spot",
            "compared dry and damp edges",
            "paused to hear every witness",
        ]
    )

    prize = world.add(
        Entity(
            id="toe-pl",
            kind="thing",
            species="county marker",
            label="toe-place line",
            owner="county",
        )
    )
    hero.meters[params.moisture] = 2.0
    hero.memes.update(hope=1.0, hurt=1.0)
    helper.memes.update(worry=1.0, misunderstanding=1.0)

    world.say(opening)
    world.say(
        f"At {world.setting.place}, toe-pl meant the painted toe-place line where each small participant waited for a turn."
    )
    world.say(
        f"Around the grounds, moisture showed in {moisture_scene}, leaving some surfaces damp and others dry."
    )
    world.say(
        f"{hero.id}, a careful young {hero.species}, hoped to {incident['goal']}; {helper.id}, a lively {helper.species}, checked the line nearby."
    )
    world.para()
    world.say(f"The trouble began when {incident['problem']}.")
    world.say(f"Noticing the damp scene, {helper.id} assumed {incident['guess']}.")
    world.say(reaction)
    world.para()
    world.say(
        f"Their first idea failed: {incident['failed']}. Instead of hiding the mistake, they {clue_order}."
    )
    world.say(f"The deciding clue was this: {incident['clue']}.")
    world.say(f"That showed what had really happened: {incident['truth']}.")
    world.say(
        "The misunderstanding loosened as each animal shared what they knew; now teamwork could begin."
    )
    world.para()
    world.say(apology)
    world.say(f"They called in two more county helpers and brought a {help_item} for the damp work. Then {incident['roles']}.")
    world.say(f"{incident['solution']}.")
    world.say(lesson)
    world.para()
    world.say(f"{incident['ending']}.")

    hero.memes.update(calm=1.0, trust=1.0)
    helper.memes.update(teamwork=1.0, understanding=1.0)
    prize.meters.update(dry=1.0, visible=1.0)
    hero.meters[params.moisture] = 0.0
    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        moisture=params.moisture,
        moisture_scene=moisture_scene,
        incident=incident,
        help_item=help_item,
        lesson=lesson,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    incident = world.facts["incident"]
    return [
        f"Write an animal story set in the county about {world.facts['moisture']} and teamwork.",
        "Tell a gentle story where a misunderstanding gets fixed when the animals work together.",
        f"Make the story child-friendly and concrete: the animals need to {incident['goal']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    moisture_scene = world.facts["moisture_scene"]
    incident = world.facts["incident"]
    help_item = world.facts["help_item"]
    return [
        QAItem(
            question=f"Why did {helper.id} blame {hero.id} at first?",
            answer=f"{helper.id} noticed moisture in {moisture_scene} and assumed {incident['guess']}. That guess came before the team checked the evidence.",
        ),
        QAItem(
            question=f"Which clue changed {hero.id} and {helper.id}'s understanding?",
            answer=f"They discovered that {incident['clue']}. It showed them that {incident['truth']}.",
        ),
        QAItem(
            question=f"How did {hero.id}'s team solve the real problem?",
            answer=f"The animals shared jobs and used a {help_item}. {incident['solution']}.",
        ),
        QAItem(
            question=f"What was safe or ready when {helper.id}'s team finished?",
            answer=f"{incident['safe'].capitalize()} was safe or ready again. {incident['ending']}.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} and {helper.id} carry away?",
            answer=world.facts["lesson"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is moisture?",
            answer="Moisture is a little bit of wetness on things like grass, paws, or leaves.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people or animals help each other and do a job together.",
        ),
        QAItem(
            question="What is a county?",
            answer="A county is a part of a state or country, and it can have towns, roads, farms, and barns.",
        ),
    ]


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {ent.id} ({ent.species}) {' '.join(bits)}")
    return "\n".join(out)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about county moisture and teamwork.")
    ap.add_argument("--place", choices=COUNTY_PLACES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(COUNTY_PLACES)
    hero_species = rng.choice(ANIMALS)
    helper_species = rng.choice([a for a in ANIMALS if a != hero_species])
    hero_name = rng.choice(NAMES)
    helper_name = rng.choice([n for n in NAMES if n != hero_name])
    moisture = rng.choice(MOISTURE_KINDS)
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_species=hero_species,
        helper_name=helper_name,
        helper_species=helper_species,
        moisture=moisture,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts() -> str:
    return "\n".join(
        [
            'setting(county).',
            'feature(misunderstanding).',
            'feature(teamwork).',
            'word("toe-pl").',
            'word("moisture").',
            'word("county").',
        ]
    )


ASP_RULES = r"""
valid_story(county, misunderstanding, teamwork) :- setting(county), feature(misunderstanding), feature(teamwork).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    vals = set(asp.atoms(model, "valid_story"))
    expected = {("county", "misunderstanding", "teamwork")}
    if vals == expected:
        print("OK: ASP facts and Python world agree.")
        return 0
    print("MISMATCH:", vals, expected)
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = resolve_params(args, random.Random(base_seed))
        params.seed = base_seed
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### story {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
