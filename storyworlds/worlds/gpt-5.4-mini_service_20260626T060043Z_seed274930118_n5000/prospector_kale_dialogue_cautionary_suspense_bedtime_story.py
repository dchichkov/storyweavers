#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/prospector_kale_dialogue_cautionary_suspense_bedtime_story.py
=================================================================================================================

A small bedtime-story world about a prospector, a patch of kale, a cautious
night walk, and a harmless suspenseful misunderstanding.

Seed tale:
---
A sleepy prospector followed a moonlit trail behind the cottage, hoping the
shiny leaves in the garden meant gold. Instead, he found a patch of kale.
A child wanted to taste it at once, but the prospector warned that unknown
plants should be checked first. Together they waited, listened to the crickets,
and asked the gardener, who smiled and said the leaves were good to eat after
washing. The child learned to be patient, and the little garden felt safe again.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    edible: bool = False
    safe_after_wash: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "prospector"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the garden"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero_name: str
    child_name: str
    seed: Optional[int] = None
    incident: int = 0
    opening: int = 0
    warning: int = 0
    transition: int = 0
    reflection: int = 0


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, affords={"kale"}),
    "backyard": Setting(place="the backyard", indoor=False, affords={"kale"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"kale"}),
}

HERO_NAMES = ["Milo", "Nina", "Theo", "Lina", "Owen", "Ivy"]
CHILD_NAMES = ["Pip", "Mina", "Jasper", "Bea", "Toby", "Rosa"]

INCIDENTS = [
    {
        "glimmer": "a row of silver flashes trembling across the kale",
        "guess": "a seam of moon-silver had pushed up through the soil",
        "urge": "rub one bright leaf to see whether treasure dust came off",
        "sound": "a quick click-click answered from beneath the leaves",
        "clue": "round drops clung to the leaf edges, and a loose sprinkler ticked nearby",
        "test": "They held the lantern low and caught one drop on a clean spoon instead of touching the plant.",
        "cause": "dew was reflecting the moon while the sprinkler cooled",
        "repair": "The gardener tightened the sprinkler, then helped them rinse a basket of kale at the pump.",
        "lesson": "shine can invite a guess, but clues deserve a careful look",
        "ending": "Beside the quiet sprinkler, clean kale leaves shone like little green moons.",
    },
    {
        "glimmer": "one pale shape bobbing between two dark rows of kale",
        "guess": "a tiny cave lantern was signaling from underground",
        "urge": "crawl through the narrow rows and grab the mysterious light",
        "sound": "the shape scraped, paused, and scraped again",
        "clue": "a wooden handle leaned from the leaves, with damp soil on its end",
        "test": "They stayed on the path and called for the gardener rather than squeezing into the dark patch.",
        "cause": "a white garden scoop was rocking on a loose irrigation hose",
        "repair": "Together they moved the hose, returned the scoop, and washed the kale it had splashed.",
        "lesson": "a moving shadow is not proof of danger or treasure",
        "ending": "The scoop rested by the shed while the straight kale rows slept under the stars.",
    },
    {
        "glimmer": "green sparks winking above the crinkled kale leaves",
        "guess": "emerald nuggets were floating out of a secret mine",
        "urge": "wave a jar through the leaves and capture every spark",
        "sound": "something hummed close to the jar and vanished",
        "clue": "the lights rose on tiny wings and blinked only when the air grew still",
        "test": "They set the jar down, counted the flashes, and watched without chasing them.",
        "cause": "fireflies were resting above the cool kale patch",
        "repair": "The gardener showed them a safe path around the plants and picked kale from the far row.",
        "lesson": "wonder is better observed gently than snatched in haste",
        "ending": "Fireflies blinked over the rinsed kale, and nobody disturbed their soft green dance.",
    },
    {
        "glimmer": "a golden corner peeking from under the largest kale plant",
        "guess": "a lost claim map had finally surfaced",
        "urge": "yank the corner free before anyone else spotted it",
        "sound": "paper crackled, followed by a low rustle along the fence",
        "clue": "the corner bore a painted carrot and was tied to a garden stake",
        "test": "They loosened no knots and read the visible words by lantern light.",
        "cause": "the gardener's planting label had folded beneath a leaf",
        "repair": "The gardener retied the label, showed them the word KALE, and let them harvest an outer leaf.",
        "lesson": "finding something does not make it yours to pull apart",
        "ending": "The straightened label stood guard while a washed kale leaf dried on a blue cloth.",
    },
    {
        "glimmer": "a coppery gleam circling the stems at ground level",
        "guess": "a buried bracelet marked the mouth of a mine",
        "urge": "dig beside the stems with the prospector's small trowel",
        "sound": "dry leaves gave a long shiver although the wind had stopped",
        "clue": "a thin trail curved around the plants and disappeared under a watering board",
        "test": "They put the trowel away and traced the trail from the path with the lantern.",
        "cause": "a harmless snail trail was catching the moonlight",
        "repair": "The gardener moved the board without hurting the snail and showed them which kale leaves were ready.",
        "lesson": "careful tracking protects small lives as well as gardens",
        "ending": "A snail crossed the silver path as the three friends carried clean kale home.",
    },
    {
        "glimmer": "a bright rim flashing inside a fallen flowerpot beside the kale",
        "guess": "a gold pan had been hidden there by another prospector",
        "urge": "reach into the pot before the scraping sound returned",
        "sound": "scritch-scratch came from the pot, then stopped when they spoke",
        "clue": "two dry kale leaves poked from the rim and moved whenever the breeze slipped under them",
        "test": "They tapped the ground beside the pot with a stick and waited at arm's length.",
        "cause": "wind was turning a loose metal plant marker inside the pot",
        "repair": "The gardener lifted the pot, secured the marker, and composted the dry leaves.",
        "lesson": "waiting and testing from a safe distance can shrink a frightening mystery",
        "ending": "The marker lay snug in its tray, and the kale made only a sleepy leafy hush.",
    },
    {
        "glimmer": "inky drops sparkling on one edge of the kale bed",
        "guess": "dark ore was leaking from a crack below",
        "urge": "taste a drop to learn whether it was bitter mineral water",
        "sound": "a bucket knocked softly somewhere beyond the gate",
        "clue": "the drops smelled earthy, and a tipped watering pail stood beside a sack marked COMPOST",
        "test": "They touched nothing, stepped back, and told the gardener exactly what they had noticed.",
        "cause": "safe compost tea had spilled while feeding the soil, but the leaves still needed washing",
        "repair": "The gardener righted the pail and rinsed the harvested kale twice under clean water.",
        "lesson": "even familiar garden things should be identified before tasting",
        "ending": "The empty pail drained upside down while clean kale curled in a white bowl.",
    },
    {
        "glimmer": "tiny crystals whitening the tips of the kale",
        "guess": "a frost mine had opened during the night",
        "urge": "snap off a crystal-covered leaf as a treasure sample",
        "sound": "a brittle little crack ran down the row",
        "clue": "their breath clouded, the path glittered too, and every crystal melted on the lantern glass",
        "test": "They covered one leaf with a mitten and waited to see whether its crystals vanished.",
        "cause": "the first light frost had silvered the whole garden",
        "repair": "The gardener checked the leaves, harvested the sound ones, and washed them in the warm kitchen.",
        "lesson": "several matching clues can correct an exciting first guess",
        "ending": "Outside, frost twinkled untouched; inside, green kale steamed beside three drowsy cups.",
    },
    {
        "glimmer": "a trembling pool of light beneath a leaning kale plant",
        "guess": "water had filled an abandoned mine shaft",
        "urge": "step off the stones and measure the shining pool",
        "sound": "drip, pause, drip came from under the soil",
        "clue": "one stepping stone was darker than the others and the nearby leaves drooped",
        "test": "They marked the wet stone with the lantern and fetched the gardener without crossing it.",
        "cause": "a split irrigation tube had made a slippery puddle and thirsty plants",
        "repair": "They held the lantern while the gardener joined the tube and propped the kale upright.",
        "lesson": "a cautious warning matters most when excitement hides an ordinary hazard",
        "ending": "The repaired tube gave one final plip, and the upright kale cast a calm shadow.",
    },
    {
        "glimmer": "three bright marks leading from the gate toward the kale",
        "guess": "another prospector had stamped a secret trail",
        "urge": "follow the marks between the beds before they faded",
        "sound": "a bell at the gate gave one lonely ting",
        "clue": "each mark had the same crescent edge as the gardener's muddy boot",
        "test": "They compared the marks from the path and called out instead of following into the beds.",
        "cause": "the gardener had carried a lantern through wet soil while checking the kale",
        "repair": "The gardener brushed the path, latched the gate, and invited them to pick kale together.",
        "lesson": "asking the person who made a clue can be wiser than inventing a chase",
        "ending": "Three clean bootprints pointed home beneath a lantern hanging safely on its hook.",
    },
    {
        "glimmer": "a silver ribbon curling from the kale toward the shed",
        "guess": "a mapmaker had drawn a shining road to treasure",
        "urge": "race along the ribbon before the moon went behind a cloud",
        "sound": "the shed latch clacked twice in the gathering dark",
        "clue": "the ribbon was wet, narrow, and broken wherever the soil was dry",
        "test": "They stood together, lit a second lantern, and followed it only from the firm path.",
        "cause": "a watering can had dribbled a moonlit trail after the gardener filled it",
        "repair": "The gardener closed the loose latch, wiped the can, and washed a handful of kale.",
        "lesson": "staying together keeps a curious investigation from becoming a risky one",
        "ending": "The dry watering can gleamed on its shelf while the moonlit ribbon faded away.",
    },
    {
        "glimmer": "a brass-colored disk swinging just above the kale",
        "guess": "a prospector's medal was warning them away from a claim",
        "urge": "duck under the garden cord and catch the swinging disk",
        "sound": "ting-a-ling rang out whenever the disk brushed a stake",
        "clue": "the disk hung from the gate cord, and one broad kale leaf had pulled the cord tight",
        "test": "They stayed outside the cord and shone the lantern along it from end to end.",
        "cause": "the gardener's little gate bell had snagged on a fallen kale leaf",
        "repair": "The gardener freed the leaf, tested the bell, and washed the leaf before adding it to supper.",
        "lesson": "boundaries remain important even when the thing beyond them looks harmless",
        "ending": "The gate clicked shut, the bell was still, and one clean kale leaf waited on a starry plate.",
    },
]

OPENINGS = [
    "The moon had climbed above {place} when {hero}, a careful prospector, promised {child} one last quiet walk before bed.",
    "Just before bedtime, {child} carried a lantern beside {hero}, the prospector, along the safest path through {place}.",
    "A cool night settled over {place}. {hero}, an old prospector at heart, showed {child} how to walk slowly and notice small things.",
    "While the house grew sleepy, prospector {hero} and {child} took a final lantern round through {place}.",
    '"Ten careful minutes, then pillows," said prospector {hero} as {child} joined the moonlit walk through {place}.',
    "Crickets tuned their night song around {place} as {hero}, the prospector, led {child} between the garden markers.",
    "Bedtime was near, but {hero} the prospector had promised {child} a calm look at {place} beneath the moon.",
    "With one lantern and two pairs of boots, prospector {hero} and {child} entered {place} for a short bedtime stroll.",
]

WARNINGS = [
    '"Stop at the path," {hero} said. "A sparkle tells us where to look, not what is safe."',
    '"Curiosity may ask the first question," warned {hero}, "but caution chooses our next step."',
    '"Let our eyes investigate before our hands do," {hero} said, drawing {child} back.',
    '"No tasting, grabbing, or stepping closer until we know," said {hero}.',
    '"A good prospector checks a clue twice," {hero} reminded {child}. "Stay beside me."',
    '"We can solve this without rushing," whispered {hero}. "First, tell me what you notice."',
    '"Unknown does not mean terrible," {hero} said, "but it does mean we pause and check."',
    '"Treasure can wait," said {hero}. "Safety cannot, so we gather clues from here."',
]

TRANSITIONS = [
    "For a moment, neither of them moved.",
    "The lantern flame dipped, and the shadows seemed to lean closer.",
    "They listened through one long cricket song.",
    "A cloud crossed the moon, making the mystery look larger than before.",
    "Their brave plan was simply to be still and pay attention.",
    "The garden held its breath while they considered the evidence.",
    "Instead of filling the silence with guesses, they searched for one more clue.",
    "They counted three slow breaths before deciding what to do.",
]

REFLECTIONS = [
    '"The sound made me want to hurry," {child} admitted, "but hurrying would not have explained it."',
    '"Our first guess was exciting," said {child}, "and the real answer fits all the clues better."',
    '"I am glad we protected the kale while we investigated," {child} said.',
    '"Being cautious did not spoil the mystery," {child} observed. "It helped us solve it."',
    '"Next time I will ask what the evidence shows," promised {child}.',
    '"We were brave enough to wait," {child} said, holding the lantern steady.',
    '"A clue is more useful when we do not disturb it," {child} decided.',
    '"We found an answer without turning a small puzzle into a big problem," said {child}.',
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/2.
setting(garden). setting(backyard). setting(kitchen).
indoor(kitchen).
affords(garden,kale). affords(backyard,kale). affords(kitchen,kale).

valid(P, A) :- affords(P, A).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    return sorted((p, a) for p, s in SETTINGS.items() for a in s.affords)


def asp_verify() -> int:
    a, p = set(asp_valid()), set(python_valid())
    if a == p:
        print(f"OK: clingo gate matches python gate ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> StoryState:
    setting = SETTINGS[params.place]
    world = StoryState(setting=setting)
    incident = INCIDENTS[params.incident % len(INCIDENTS)]
    story_place = (
        "the garden just beyond the kitchen door"
        if setting.indoor else setting.place
    )

    hero = world.add(Entity(
        id=params.hero_name, kind="character", type="prospector",
        traits=["sleepy", "careful"],
    ))
    child = world.add(Entity(
        id=params.child_name, kind="character", type="child",
        traits=["curious", "small"],
    ))
    gardener = world.add(Entity(
        id="Gardener", kind="character", type="gardener",
        traits=["gentle"],
    ))
    kale = world.add(Entity(
        id="kale", type="kale", label="kale", phrase="a patch of kale",
        owner=gardener.id, caretaker=gardener.id, edible=True, safe_after_wash=True,
    ))

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(
        place=story_place, hero=hero.id, child=child.id
    ))
    world.say(f"Near the kale, they noticed {incident['glimmer']}.")
    world.say(
        f'"Perhaps {incident["guess"]}," {hero.id} murmured. '
        f'"Or perhaps it is something ordinary," {child.id} replied.'
    )

    world.para()
    world.say(
        f"Then {incident['sound']}. {child.id} wanted to {incident['urge']}."
    )
    world.say(WARNINGS[params.warning % len(WARNINGS)].format(
        hero=hero.id, child=child.id
    ))
    child.memes["impulse"] = 1
    hero.memes["caution"] = 1
    world.facts["tension"] = True
    world.facts["possible_danger"] = incident["urge"]
    world.say(TRANSITIONS[params.transition % len(TRANSITIONS)])
    world.say(f"From the safe path, they saw that {incident['clue']}.")
    world.say(incident["test"])
    world.say(REFLECTIONS[params.reflection % len(REFLECTIONS)].format(
        child=child.id
    ))

    world.para()
    world.say(
        f'The gardener arrived and listened to every clue. "You investigated wisely," '
        f'the gardener said. "{incident["cause"].capitalize()}."'
    )
    world.say(incident["repair"])
    world.say(
        f'"Tonight I learned that {incident["lesson"]}," {child.id} told {hero.id}. '
        f"The prospector nodded, glad their suspenseful mystery had ended safely."
    )
    world.say(f"Then {child.id} yawned, and they turned home toward bedtime.")
    world.say(incident["ending"])

    world.facts.update(
        hero=hero,
        child=child,
        gardener=gardener,
        kale=kale,
        place=story_place,
        incident=incident,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    incident = f["incident"]
    return [
        f'Write a bedtime story about a prospector investigating {incident["glimmer"]}.',
        f"Tell a gentle suspense story where {f['hero'].id} helps {f['child'].id} investigate safely before acting.",
        f'Write a child-friendly story set in {f["place"]} with dialogue, kale, a cautionary turn, and a peaceful ending.',
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    child = f["child"]
    gardener = f["gardener"]
    place = f["place"]
    incident = f["incident"]
    return [
        QAItem(
            question=f"Who was the prospector in the story?",
            answer=f"The prospector was {hero.id}. {hero.id} helped {child.id} examine the nighttime mystery without rushing.",
        ),
        QAItem(
            question=f"What risky thing did {child.id} first want to do?",
            answer=f"{child.id} wanted to {incident['urge']}. {hero.id} asked the child to pause and investigate from a safe place instead.",
        ),
        QAItem(
            question=f"What clue helped solve the suspenseful mystery at {place}?",
            answer=f"They noticed that {incident['clue']}. That evidence helped the gardener explain that {incident['cause']}.",
        ),
        QAItem(
            question="How did the gardener help make things right?",
            answer=incident["repair"],
        ),
        QAItem(
            question=f"What lesson did {child.id} learn before bedtime?",
            answer=f"{child.id} learned that {incident['lesson']}. The careful choice kept the child, the kale, and the garden safe.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="What is kale?",
            answer="Kale is a leafy green vegetable that people can wash and eat.",
        ),
        QAItem(
            question="Why should someone check a plant before tasting it?",
            answer="Someone should check a plant first because some wild plants are not safe to eat, and a careful adult can help tell the difference.",
        ),
        QAItem(
            question="What is a prospector?",
            answer="A prospector is a person who looks for valuable things like gold or minerals.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.edible:
            bits.append("edible=True")
        if e.safe_after_wash:
            bits.append("safe_after_wash=True")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    hero_name = args.name or rng.choice(HERO_NAMES)
    child_name = args.child or rng.choice(CHILD_NAMES)
    if hero_name == child_name:
        child_name = rng.choice([n for n in CHILD_NAMES if n != hero_name])
    return StoryParams(
        place=place,
        hero_name=hero_name,
        child_name=child_name,
        incident=rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        warning=rng.randrange(len(WARNINGS)),
        transition=rng.randrange(len(TRANSITIONS)),
        reflection=rng.randrange(len(REFLECTIONS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a prospector, kale, caution, and suspense."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--child")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp_valid()
        print(f"{len(model)} valid combinations:\n")
        for place, act in model:
            print(f"  {place:10} {act}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [(p, f"{p.title()}Prospector", f"{p.title()}Child") for p in SETTINGS]
        for place, hero_name, child_name in combos:
            params = StoryParams(place=place, hero_name=hero_name, child_name=child_name)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
