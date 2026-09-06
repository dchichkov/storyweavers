#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/teller_remainder_margarita_quest_animal_story.py
=================================================================================================

A small, self-contained storyworld in the Animal Story style.

Seed tale:
- A teller, a remainder, and a margarita are part of a quest.
- The world is animal-centered, concrete, and child-facing.
- The story turns on a simple problem: the quest item is incomplete, so the
  animal heroes must decide how to finish the errand and who should carry what.

The world model tracks both physical meters and emotional memes:
- meters: distance, weight, completeness, tidiness, shine
- memes: worry, courage, trust, joy, relief

The domain's core premise is that a small animal team receives a quest from a
teller. They find a remainder of something important, and a character named
Margarita helps them finish the errand in a satisfying way.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402

SETTING_NAME = "the little river market"


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "animal" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0, "completeness": 0.0, "tidiness": 0.0, "shine": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"worry": 0.0, "courage": 0.0, "trust": 0.0, "joy": 0.0, "relief": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "she", "cat", "rabbit", "mouse", "duck"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "he", "fox", "bear", "dog", "goat", "turtle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = SETTING_NAME


@dataclass
class StoryParams:
    teller: str
    remainder: str
    margarita: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    scenario_index: int = 0
    telling_mode: int = 0
    detail_variant: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace_log: list[str] = []
        self.done: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def log(self, text: str) -> None:
        self.trace_log.append(text)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story: a teller, a remainder, and a margarita on a quest.")
    ap.add_argument("--teller")
    ap.add_argument("--remainder")
    ap.add_argument("--margarita")
    ap.add_argument("--name")
    ap.add_argument("--type")
    ap.add_argument("--sidekick")
    ap.add_argument("--sidekick-type")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    teller = args.teller or rng.choice(["Teller", "Old Teller", "River Teller"])
    remainder = args.remainder or rng.choice(["remainder", "little remainder", "lost remainder"])
    margarita = args.margarita or rng.choice(["Margarita", "Captain Margarita", "Margarita the Goat"])
    hero_name = args.name or rng.choice(["Nina", "Pip", "Milo", "Lulu", "Toby"])
    hero_type = args.type or rng.choice(["rabbit", "fox", "duck", "mouse", "bear"])
    sidekick_name = args.sidekick or rng.choice(["Mina", "Dot", "Bibi", "Sunny", "Momo"])
    sidekick_type = args.sidekick_type or rng.choice(["mouse", "duck", "cat", "goat", "turtle"])
    return StoryParams(
        teller=teller,
        remainder=remainder,
        margarita=margarita,
        hero_name=hero_name,
        hero_type=hero_type,
        sidekick_name=sidekick_name,
        sidekick_type=sidekick_type,
        scenario_index=rng.randrange(len(SCENARIOS)),
        telling_mode=rng.randrange(8),
        detail_variant=rng.randrange(10_000),
    )


def _maybe_article(text: str) -> str:
    return text if text.lower().startswith(("a ", "an ", "the ")) else f"the {text}"


SCENARIOS = [
    {
        "quest": "restore the last page of the moon-moth picture book before story hour",
        "place": "the reed-lined reading dock",
        "obstacle": "A gust had scattered scraps among lily pads, and one wet scrap showed the wrong ending.",
        "mistake": "The friends first chased the largest scrap, but its painted sun belonged to another book.",
        "clue": "Margarita noticed a silver wing-tip reflected in a puddle beneath the dock.",
        "action": "She held a flower-stem hook while the two friends steadied a basket and lifted the dry scrap from below.",
        "result": "The remainder completed a moon moth whose wings pointed home.",
        "lesson": "careful looking can matter more than grabbing the biggest answer",
        "image": "moon-moth wings gleamed across the joined page as young otters gathered close",
        "dialogue": "The smallest glimmer can finish the biggest tale",
    },
    {
        "quest": "deliver the remainder of the winter seed packets before rain reached the garden",
        "place": "the market's crooked greenhouse",
        "obstacle": "A wheelbarrow blocked the narrow door while dark drops began tapping the glass.",
        "mistake": "The team tried to squeeze through together, and the packets nearly spilled into a drain.",
        "clue": "Margarita saw that a loose side panel could open if its wooden peg was lifted.",
        "action": "One friend held the packets high, one raised the peg, and Margarita guided everyone through in a patient line.",
        "result": "The remaining seeds stayed dry and filled the final empty planting tray.",
        "lesson": "sharing one tight space takes order as well as courage",
        "image": "three neat rows of seed labels stood beneath rain-bright glass",
        "dialogue": "One careful step each, and none of our seeds will swim",
    },
    {
        "quest": "return the remainder of a baker's berry tokens before the ovens cooled",
        "place": "the warm cobblestone bakery lane",
        "obstacle": "The token pouch had snagged above a sleepy badger's awning.",
        "mistake": "A hurried jump shook flour over the lane but did not loosen the pouch.",
        "clue": "Margarita heard its wooden tokens click whenever the awning rope went slack.",
        "action": "The friends pulled the rope gently in rhythm while Margarita caught the pouch in an empty bread basket.",
        "result": "The baker counted the remainder and could give every helper a fair berry bun.",
        "lesson": "fair shares are worth a calm and clever effort",
        "image": "berry buns cooled in a circle while floury pawprints crossed the stones",
        "dialogue": "Let the rope whisper instead of making the awning shout",
    },
    {
        "quest": "find the remainder of the bridge markers before the duckling parade",
        "place": "the willow bridge approach",
        "obstacle": "Mud covered every arrow, and the parade path split in three directions.",
        "mistake": "The heroes followed the brightest mark until it ended at a wheel-rut full of water.",
        "clue": "Margarita found tiny blue paint flecks on the dry side of a willow root.",
        "action": "They brushed the roots with reeds, matched the flecks, and set the recovered arrows where small feet could see them.",
        "result": "The remainder of the markers made one safe path over the bridge.",
        "lesson": "evidence is a better guide than whatever looks brightest",
        "image": "a line of ducklings crossed beneath blue arrows and nodding willow leaves",
        "dialogue": "A true clue should lead somewhere, not merely sparkle",
    },
    {
        "quest": "complete the wind-chime notes needed to call the ferry home",
        "place": "the market's foggy ferry bell",
        "obstacle": "Fog swallowed the river, and the final copper chime was tangled in a kite tail.",
        "mistake": "Calling louder only sent echoes bouncing toward the wrong bank.",
        "clue": "Margarita felt the breeze change whenever the kite dipped toward the bell post.",
        "action": "She timed the breeze while the friends lowered the kite with a spool and tied the recovered chime in its proper place.",
        "result": "The complete tune carried straight across the water and guided the ferry home.",
        "lesson": "listening can solve what shouting cannot",
        "image": "four copper chimes swayed above the ferry's single golden lamp",
        "dialogue": "Wait for the wind to answer before we call again",
    },
    {
        "quest": "recover the remainder of a mosaic sign before visitors arrived",
        "place": "the sunny fountain court",
        "obstacle": "Several colored tiles lay mixed with smooth pebbles at the fountain's edge.",
        "mistake": "The friends chose tiles by color alone and made the painted fish face backward.",
        "clue": "Margarita compared the tiny grooves and found that only three pieces continued the wave pattern.",
        "action": "They dried each piece, turned it until the grooves met, and pressed the true remainder into soft clay.",
        "result": "The sign once again showed a fish pointing toward the market gate.",
        "lesson": "a part belongs when its edges and purpose both agree",
        "image": "the repaired blue fish flashed beside a fountain rainbow",
        "dialogue": "Color gives us a guess, but the little lines give us proof",
    },
    {
        "quest": "bring back the remainder of the lantern oil before the twilight puppet show",
        "place": "the shadow-puppet tent",
        "obstacle": "The small sealed flask had rolled into a maze of folded benches.",
        "mistake": "Crawling after it pushed the flask farther whenever a bench leg bumped the floor.",
        "clue": "Margarita watched its round shadow pause beside a gap under the back curtain.",
        "action": "The friends made a soft ramp from two playbills, and Margarita coaxed the flask into a padded basket.",
        "result": "The remaining oil lit the lamp without a spill, and the show could begin safely.",
        "lesson": "a gentle path can work better than a forceful chase",
        "image": "a paper fox danced across the curtain in a steady amber circle",
        "dialogue": "We do not have to catch it if we can give it a safe road",
    },
    {
        "quest": "locate the remainder of the quilt squares promised to the nursery",
        "place": "the upstairs sewing loft",
        "obstacle": "A trail of threads ended beneath a cabinet too low for the larger animals.",
        "mistake": "Pulling one loose thread tightened a knot around the missing bundle.",
        "clue": "Margarita spotted a polished spoon that could reflect the dark space under the cabinet.",
        "action": "One friend aimed the spoon, another loosened the knot with a knitting needle, and Margarita drew out the bundle.",
        "result": "The remainder formed the quilt's soft green border.",
        "lesson": "different sizes and skills make a team stronger",
        "image": "the finished quilt hung like a square meadow above three sleeping kits",
        "dialogue": "Your eyes, my steady hoof, and that slim needle make one excellent team",
    },
    {
        "quest": "restore the remainder of the orchard's watering schedule before noon",
        "place": "the apple-cart notice board",
        "obstacle": "A juice stain hid the times for the youngest trees.",
        "mistake": "Guessing from yesterday's heat would have given the saplings too much water.",
        "clue": "Margarita found a clean copy pressed faintly onto the blotting paper behind the schedule.",
        "action": "They held the paper toward the sun, copied each faint time, and checked it against the gardener's numbered rows.",
        "result": "The remainder completed the schedule, so every tree received the right amount.",
        "lesson": "checking a record protects others from a confident guess",
        "image": "silver drops rested on the smallest apple leaves at exactly noon",
        "dialogue": "A faint fact is still better than a loud guess",
    },
    {
        "quest": "find the remainder of a shell necklace meant for the river museum",
        "place": "the low-tide counting table",
        "obstacle": "A magpie had arranged many shiny shells around one missing numbered tag.",
        "mistake": "The first shell fit the string but made the count skip from seven to nine.",
        "clue": "Margarita noticed an eight-shaped chalk mark beneath a dull spiral shell.",
        "action": "The friends counted from both ends, thanked the magpie for guarding the pieces, and tied the correct shell between seven and nine.",
        "result": "The remainder made the museum necklace complete and correctly ordered.",
        "lesson": "counting carefully can settle a puzzle without blaming anyone",
        "image": "ten shells curved across blue cloth like a quiet river wave",
        "dialogue": "Let us count the story the shells are already telling",
    },
    {
        "quest": "deliver the remainder of the medicine labels to the animal clinic",
        "place": "the market's breezy herb stall",
        "obstacle": "Labels had fluttered into baskets of mint, thyme, and harmless yellow daisies.",
        "mistake": "Matching a label by smell nearly paired it with the wrong jar.",
        "clue": "Margarita found tiny stamped shapes that matched marks on the clinic's sealed boxes.",
        "action": "They sorted by stamp, asked the clinic keeper to verify every match, and carried the labels in a lidded tray.",
        "result": "The remainder completed the records without anyone guessing about medicine.",
        "lesson": "health instructions must be checked by a responsible grown-up",
        "image": "the labeled boxes stood in a locked cabinet beside a vase of yellow daisies",
        "dialogue": "For medicine, we check twice and let the clinic keeper decide",
    },
    {
        "quest": "recover the remainder of the flower garland for the market's welcome arch",
        "place": "the riverside flower stand",
        "obstacle": "The last chain of white margarita flowers had slipped onto a branch above the current.",
        "mistake": "A long reach bent the branch and sent one blossom spinning downstream.",
        "clue": "Margarita the goat saw that the garland's ribbon was looped, not knotted, around a twig.",
        "action": "The friends held a broad basket below while she nudged the ribbon free with a padded pole.",
        "result": "The flower remainder completed the arch, and the rescued loose blossom floated in a water bowl.",
        "lesson": "protecting delicate things requires preparation, not a desperate grab",
        "image": "white margarita flowers framed the gate while one blossom circled a blue bowl",
        "dialogue": "Basket first, gentle nudge second, and the flowers get home whole",
    },
]


OPENINGS = [
    "Just after the market awnings opened",
    "Before the first ferry bell",
    "On a morning when river mist curled around every stall",
    "As the market clock clicked toward its busiest hour",
    "While swallows skimmed the bright river",
    "Near the end of a bustling market day",
    "When a brisk wind rattled the price cards",
    "Under strings of paper flags",
]


def _pick(options: list[str], variant: int, offset: int) -> str:
    return options[(variant // (offset + 1) + offset) % len(options)]


def tell(params: StoryParams) -> World:
    w = World(Setting())
    hero = w.add(Entity(id=params.hero_name, kind="animal", type=params.hero_type, label=params.hero_name))
    sidekick = w.add(Entity(id=params.sidekick_name, kind="animal", type=params.sidekick_type, label=params.sidekick_name))
    teller = w.add(Entity(id="teller", kind="animal", type="turtle", label=params.teller))
    remainder = w.add(Entity(id="remainder", kind="thing", type="thing", label=params.remainder, phrase=f"the {params.remainder}", owner=teller.id))
    margarita = w.add(Entity(id="margarita", kind="animal", type="goat", label=params.margarita))
    quest = w.add(Entity(id="quest", kind="thing", type="thing", label="quest", phrase="the quest", plural=False))
    scenario = SCENARIOS[params.scenario_index % len(SCENARIOS)]

    w.facts.update(
        hero=hero,
        sidekick=sidekick,
        teller=teller,
        remainder=remainder,
        margarita=margarita,
        quest=quest,
        scenario=scenario,
    )

    hero.memes["joy"] += 1
    sidekick.memes["trust"] += 1

    opening = OPENINGS[params.telling_mode % len(OPENINGS)]
    summons = [
        f'{teller.label} lowered a careful voice. "I need you to {scenario["quest"]}," the teller said.',
        f'A blank space in {teller.label}\'s ledger announced the morning\'s quest: {scenario["quest"]}.',
        f'{hero.label} had expected an ordinary errand until {teller.label} asked the friends to {scenario["quest"]}.',
        f'Beside a red quest ribbon, {teller.label} explained the task: {scenario["quest"]}.',
    ]
    w.say(f"{opening}, {hero.label} the {hero.type} and {sidekick.label} the {sidekick.type} met {teller.label} at {w.setting.place}.")
    w.say(_pick(summons, params.detail_variant, 1))
    w.say(f"Only the {remainder.label} was still missing, so finishing the quest depended on finding and using that remainder correctly.")
    w.para()

    hero.memes["worry"] += 1
    arrivals = [
        f"At {scenario['place']}, {scenario['obstacle'][0].lower() + scenario['obstacle'][1:]}",
        f"The trail led to {scenario['place']}. There, {scenario['obstacle'][0].lower() + scenario['obstacle'][1:]}",
        f"Their first surprise waited at {scenario['place']}: {scenario['obstacle'][0].lower() + scenario['obstacle'][1:]}",
    ]
    w.say(_pick(arrivals, params.detail_variant, 3))
    w.say(f"{hero.label} worried that they would return empty-pawed. Then {margarita.label}, a helpful goat named for a cheerful flower, joined the animal quest.")
    w.para()

    remainder.meters["distance"] = 1.0
    hero.memes["courage"] += 1
    sidekick.memes["courage"] += 1
    reactions = [
        f'"We can fix this fastest if we rush," {sidekick.label} said. {scenario["mistake"]}',
        f"Their first idea sounded sensible, yet it failed. {scenario['mistake']}",
        f"Before anyone had checked the evidence, {scenario['mistake'][0].lower() + scenario['mistake'][1:]}",
        f"A quick attempt made the puzzle harder: {scenario['mistake'][0].lower() + scenario['mistake'][1:]}",
    ]
    w.say(_pick(reactions, params.detail_variant, 5))
    w.say(f'"{scenario["dialogue"]}," {margarita.label} said. {scenario["clue"]}')
    w.say(scenario["action"])
    w.para()

    remainder.meters["completeness"] = 1.0
    remainder.meters["tidiness"] = 1.0
    margarita.memes["joy"] += 1
    teller.memes["relief"] += 1
    hero.memes["joy"] += 1
    remainder.carried_by = margarita.id
    w.say(f"Together they brought the {remainder.label} to the right place. {scenario['result']}")
    resolutions = [
        f"{teller.label} checked their work and declared the quest complete.",
        f'"That is the finish we needed," {teller.label} said after checking every part.',
        f"When {teller.label} inspected the result, worry gave way to relief.",
        f"The completed task earned three warm thanks from {teller.label}, one for each helper.",
    ]
    w.say(_pick(resolutions, params.detail_variant, 7))
    w.para()

    reflections = [
        f"{hero.label} understood that {scenario['lesson']}.",
        f"On the walk back, {sidekick.label} repeated the lesson: {scenario['lesson']}.",
        f"Their wrong first attempt had taught them that {scenario['lesson']}.",
        f"Margarita's patient help proved that {scenario['lesson']}.",
    ]
    w.say(_pick(reflections, params.detail_variant, 9))
    endings = [
        f"That evening, {scenario['image']}.",
        f"The friends paused before leaving; {scenario['image']}.",
        f"Behind them, {scenario['image']}, proof that the quest had truly changed something.",
        f"As the river market settled, {scenario['image']}.",
    ]
    w.say(_pick(endings, params.detail_variant, 11))
    w.log(f"scenario={params.scenario_index % len(SCENARIOS)}")
    w.log(f"result={scenario['result']}")
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    sidekick: Entity = f["sidekick"]  # type: ignore[assignment]
    teller: Entity = f["teller"]  # type: ignore[assignment]
    remainder: Entity = f["remainder"]  # type: ignore[assignment]
    margarita: Entity = f["margarita"]  # type: ignore[assignment]
    scenario: dict[str, str] = f["scenario"]  # type: ignore[assignment]
    return [
        f'Write a short Animal Story about {hero.label} and {sidekick.label} on a quest to {scenario["quest"]}.',
        f"Tell a child-friendly story where {teller.label} needs the {remainder.label}, and {margarita.label} helps solve the problem at {scenario['place']}.",
        f'Write a gentle animal quest story that includes the words "{teller.label}", "{remainder.label}", and "{margarita.label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    sidekick: Entity = f["sidekick"]  # type: ignore[assignment]
    teller: Entity = f["teller"]  # type: ignore[assignment]
    remainder: Entity = f["remainder"]  # type: ignore[assignment]
    margarita: Entity = f["margarita"]  # type: ignore[assignment]
    scenario: dict[str, str] = f["scenario"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What quest did {teller.label} give the animal friends?",
            answer=f"{teller.label} asked them to {scenario['quest']}. The missing {remainder.label} had to be found and used correctly.",
        ),
        QAItem(
            question=f"Why did the friends' first attempt at {scenario['place']} fail?",
            answer=f"Their first attempt failed because {scenario['mistake'][0].lower() + scenario['mistake'][1:]} They had to stop and examine better evidence.",
        ),
        QAItem(
            question=f"What clue did {margarita.label} notice?",
            answer=f"{scenario['clue']} That clue helped {hero.label} and {sidekick.label} choose a safer, more useful action.",
        ),
        QAItem(
            question=f"How did the friends complete the quest with the {remainder.label}?",
            answer=f"{scenario['action']} {scenario['result']}",
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn from the quest?",
            answer=f"{hero.label} learned that {scenario['lesson']}. The completed task showed why that lesson mattered.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or errand where someone goes out to find, deliver, or fix something important.",
        ),
        QAItem(
            question="What is a remainder?",
            answer="A remainder is what is left after something is used, split, or taken apart; it can also mean the missing part that is still left to find.",
        ),
        QAItem(
            question="What does a teller do?",
            answer="A teller is a person or helper who gives information, keeps track of things, or helps at a counter or desk.",
        ),
        QAItem(
            question="What is a margarita?",
            answer="Margarita can be a person's or character's name, and margarita is also a common name for a daisy-like flower. In this story, Margarita is the helpful goat's name and never refers to alcohol.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        parts = [f"type={e.type}"]
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{e.id}: " + ", ".join(parts))
    return "\n".join(lines)


ASP_RULES = r"""
entity(hero).
entity(sidekick).
entity(teller).
entity(remainder).
entity(margarita).

quest_complete :- found(remainder), returned(remainder), helped(margarita).
happy_end :- quest_complete.
#show quest_complete/0.
#show happy_end/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("found", "remainder"),
            asp.fact("returned", "remainder"),
            asp.fact("helped", "margarita"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show quest_complete/0. #show happy_end/0."))
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    expected = {"quest_complete/0", "happy_end/0"}
    if atoms == expected:
        print("OK: ASP parity check passed.")
        return 0
    print(f"MISMATCH: {sorted(atoms)} != {sorted(expected)}")
    return 1


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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(teller="Teller", remainder="remainder", margarita="Margarita", hero_name="Nina", hero_type="rabbit", sidekick_name="Momo", sidekick_type="mouse"),
    StoryParams(teller="River Teller", remainder="little remainder", margarita="Captain Margarita", hero_name="Pip", hero_type="fox", sidekick_name="Dot", sidekick_type="duck"),
    StoryParams(teller="Old Teller", remainder="lost remainder", margarita="Margarita the Goat", hero_name="Lulu", hero_type="bear", sidekick_name="Bibi", sidekick_type="cat"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_complete/0. #show happy_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show quest_complete/0. #show happy_end/0."))
        print("ASP model:", " ".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
