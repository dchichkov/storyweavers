#!/usr/bin/env python3
"""
A small pirate-tale storyworld about an old harbor, a stubborn shutter,
friendship, and a problem solved by listening closely.

Seed tale:
---
On a historic harbor street, two friends found a shutter that would not stay
closed during a windy night. One wanted to tie it shut at once, but the other
noticed a loose hook and a bent hinge. They asked the shopkeeper for help,
worked together with a screwdriver and a strip of cloth, and fixed the shutter
before the lantern light could blow out. In the end, the friends laughed,
the street stayed snug and safe, and the old building looked proud again.
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
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "sailor", "shopkeeper"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None
    incident: int = 0
    opening: int = 0
    warning: int = 0
    turn: int = 0
    ending: int = 0


SETTINGS = {
    "harbor": Setting(place="the historic harbor", indoor=False, affords={"shutter", "rope", "lantern"}),
    "street": Setting(place="the old cobblestone street by the harbor", indoor=False, affords={"shutter", "rope", "lantern"}),
    "workshop": Setting(place="the small dockside workshop", indoor=True, affords={"shutter", "screwdriver", "cloth"}),
}

HERO_NAMES = ["Mira", "Jory", "Tessa", "Ned", "Pia", "Bram"]
FRIEND_NAMES = ["Lina", "Milo", "Sana", "Oren", "Bea", "Kellan"]

INCIDENTS = [
    {
        "problem": "a shutter that kept banging open in the wind",
        "sound": "clack-bam, clack-bam",
        "guess": "the shutter was angry like a stormy sea",
        "clue": "a loose hook dangled from the frame and a hinge had turned crooked",
        "fix": "They tightened the hook, straightened the hinge, and used a strip of cloth to cushion the wood.",
        "cause": "the old hook had worn thin and the hinge had slipped out of place",
        "ending": "The shutter settled with one soft click, and the lantern light stayed warm inside.",
    },
    {
        "problem": "a shutter that would not close because a chip of driftwood was stuck in the sill",
        "sound": "tap-tap, scrape",
        "guess": "a pirate ghost was holding the panel open",
        "clue": "a pale splinter gleamed between the frame and the sill",
        "fix": "They pried out the driftwood, brushed the sill clean, and tested the shutter twice.",
        "cause": "the driftwood had wedged itself in the groove after the tide rolled in",
        "ending": "The shutter closed at once, snug as a sail tied in a calm harbor.",
    },
    {
        "problem": "a shutter that swung loose whenever footsteps crossed the street",
        "sound": "thud, creak, thud",
        "guess": "the whole house might be waking up to march away",
        "clue": "the latch pin had nearly slipped out, and the wood shook only when the frame was bumped",
        "fix": "They asked the shopkeeper for a small nail, set the latch pin back, and tapped it secure.",
        "cause": "the latch pin had loosened over many windy seasons",
        "ending": "The house stood steady, and the shutter rested like a tired sailor at dock.",
    },
    {
        "problem": "a shutter that stuck halfway open and would not move",
        "sound": "rrrk... rrrk...",
        "guess": "something heavy had hidden behind it",
        "clue": "a rusted little screw had backed out and scratched the frame",
        "fix": "They oiled the screw, turned it gently with a screwdriver, and tried the shutter again.",
        "cause": "salt air had made the screw stiff and grumpy",
        "ending": "The shutter slid shut at last, and the room inside glowed like a lantern cabin.",
    },
    {
        "problem": "a shutter that rattled so loudly it scared the gulls",
        "sound": "rattle-rattle-rattle",
        "guess": "a tiny drum hid in the wall",
        "clue": "one side of the panel lifted when the breeze pressed the other side",
        "fix": "They wedged a folded cloth at the edge and tied a soft cord around the hook for the night.",
        "cause": "the panel had a gap where the wood had shrunk in dry weather",
        "ending": "The gulls flew on, and the shutter held still as a patient lookout.",
    },
    {
        "problem": "a shutter that was painted shut after years of sea spray",
        "sound": "skrrt, skrrt",
        "guess": "the board had grown a crust like barnacles",
        "clue": "the paint line glued the edge to the frame in a shiny white seam",
        "fix": "They asked the shopkeeper before forcing it, then eased the seam with a knife and warm water.",
        "cause": "old paint and salt had sealed the panel in place",
        "ending": "The shutter opened slowly, and the fresh sea air sailed through the room.",
    },
    {
        "problem": "a shutter that kept sliding on its own when the floorboards shook",
        "sound": "slide, clack",
        "guess": "a mouse was pushing it from below",
        "clue": "the sill leaned a little downhill toward the street",
        "fix": "They propped the sill with a wooden wedge and set the shutter back in its track.",
        "cause": "the old wood had warped over time",
        "ending": "The shutter stayed put, and the friends grinned at their sturdy little wedge.",
    },
    {
        "problem": "a shutter that would not close because a fishing net thread had tangled in the latch",
        "sound": "snip, tug",
        "guess": "someone had hidden a pirate message in the latch",
        "clue": "blue thread and a tiny shell knot looped through the metal catch",
        "fix": "They untangled the thread, rolled it into a ball, and latched the shutter carefully.",
        "cause": "a torn net had snagged on the latch during a windy unload",
        "ending": "The shell knot stayed in the ball of thread as the shutter clicked home.",
    },
    {
        "problem": "a shutter that flapped so hard it knocked dust from the beam",
        "sound": "whap-whap-whap",
        "guess": "the room was trying to beat a secret drum",
        "clue": "the top hinge had only one screw left",
        "fix": "They held the shutter steady while the shopkeeper replaced the missing screw.",
        "cause": "one screw had fallen out, leaving the top hinge lopsided",
        "ending": "The dust settled, and the shutter stood straight like a proud mast.",
    },
    {
        "problem": "a shutter that had jammed because a tiny feather wedge was stuck inside",
        "sound": "tick... tick...",
        "guess": "a bird had built a nest in the frame",
        "clue": "a pale feather and a bit of straw peeked from the corner",
        "fix": "They lifted the feather wedge out gently and swept the frame clean.",
        "cause": "nesting straw had drifted into the narrow crack",
        "ending": "The shutter moved freely, and the corner felt tidy once more.",
    },
]

OPENINGS = [
    "On a historic harbor street, {hero} and {friend} set out with a lantern like two little sailors on shore leave.",
    "When the wind began to sing through the old harbor, {hero} led {friend} toward a shutter that needed help.",
    "At the edge of the old street by the sea, {hero} and {friend} promised to solve one small problem before supper.",
    "A tide-scented breeze moved over the historic harbor as {hero} and {friend} walked past the dockside shops.",
    "Under a gray-blue sky, {hero} and {friend} visited the old workshop where a stubborn shutter would not behave.",
]

WARNINGS = [
    '"No yanking," said {hero}. "We check the problem first, like a careful captain checking the ropes."',
    '"Hold the lantern steady," {hero} told {friend}. "The clue is in the frame, not in a hurry."',
    '"If the shutter fights us, we ask why," said {hero}. "Friendship means solving it together."',
    '"Let us look with our eyes before we use our hands," {hero} said.',
    '"A pirate who rushes loses treasure," said {hero}. "A friend who watches finds the fix."',
]

TURNS = [
    "They crouched beside the shutter and listened to it chatter in the wind.",
    "The two friends peered into the gap and searched for a sign of what was wrong.",
    "Instead of pulling harder, they studied the wood like detectives on a dockside case.",
    "They took turns holding the lantern and feeling the frame with careful fingers.",
    "The problem looked tricky, but the friends stayed calm and kept thinking.",
]

ENDING_LINES = [
    '"We did it by staying patient," said {friend}. "That felt better than forcing it."',
    '"A real pirate crew would call this teamwork," laughed {hero}. "{friend}, you spotted the clue first."',
    '"I like how the shutter is quiet now," said {friend}. "It sounds as sleepy as the harbor."',
    '"We fixed the problem without breaking anything," said {hero}. "That is good problem solving."',
    '"Friends make a hard job lighter," said {friend}, and {hero} nodded at the sturdy shutter.',
]


ASP_RULES = r"""
#show valid/2.
place(harbor). place(street). place(workshop).
has(harbor,shutter). has(harbor,rope). has(harbor,lantern).
has(street,shutter). has(street,rope). has(street,lantern).
has(workshop,shutter). has(workshop,screwdriver). has(workshop,cloth).

valid(P,A) :- has(P,A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for item in sorted(setting.affords):
            lines.append(asp.fact("has", pid, item))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple]:
    return sorted((p, a) for p, s in SETTINGS.items() for a in s.affords)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


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


def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    setting = SETTINGS[params.place]
    world = StoryState(setting=setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type="sailor", traits=["careful", "brave"]))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="sailor", traits=["curious", "loyal"]))
    shopkeeper = world.add(Entity(id="shopkeeper", kind="character", type="shopkeeper", traits=["helpful"]))
    shutter = world.add(Entity(id="shutter", kind="thing", type="shutter", label="old shutter", owner=shopkeeper.id, caretaker=shopkeeper.id))
    tools = {
        "lantern": world.add(Entity(id="lantern", kind="thing", type="lantern")),
        "screwdriver": world.add(Entity(id="screwdriver", kind="thing", type="tool")),
        "cloth": world.add(Entity(id="cloth", kind="thing", type="cloth")),
    }

    incident = INCIDENTS[params.incident % len(INCIDENTS)]
    world.say(OPENINGS[params.opening % len(OPENINGS)].format(hero=hero.id, friend=friend.id))
    world.say(f"They found {incident['problem']}.")
    world.say(f'"Maybe {incident["guess"]}," said {friend.id}. "{hero.id}, should we pull it?"')
    world.say(WARNINGS[params.warning % len(WARNINGS)].format(hero=hero.id, friend=friend.id))

    world.para()
    world.say(TURNS[params.turn % len(TURNS)])
    world.say(f"Then they heard {incident['sound']} from the shutter itself.")
    world.say(f'"Look there," said {hero.id}. "The clue is plain: {incident["clue"]}."')
    world.say(f'"Good eyes," replied {friend.id}. "Let us fix it the gentle way."')
    world.say(f"They asked the shopkeeper for help, and the shopkeeper brought a screwdriver, a cloth, and a patient smile.")
    world.say(incident["fix"])

    world.para()
    world.say(f'"That was clever," said {shopkeeper.id}. "{incident["cause"].capitalize()}."')
    world.say(f'"So we solved it together," said {friend.id}, and {hero.id} nodded at the steady shutter.')
    world.say(ENDING_LINES[params.ending % len(ENDING_LINES)].format(hero=hero.id, friend=friend.id))
    world.say(incident["ending"])

    world.facts.update(
        hero=hero,
        friend=friend,
        shopkeeper=shopkeeper,
        shutter=shutter,
        tools=tools,
        incident=incident,
        place=setting.place,
    )
    return world


def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    incident = f["incident"]
    return [
        f"Write a pirate-tale style story about {f['hero'].id} and {f['friend'].id} solving {incident['problem']}.",
        f"Tell a friendship story in {f['place']} with a shutter, a clue, and a kind helper.",
        "Write a child-friendly problem-solving adventure with dialogue, a historic harbor, and a calm ending.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    incident = f["incident"]
    return [
        QAItem(
            question="Who were the two friends in the story?",
            answer=f"The two friends were {f['hero'].id} and {f['friend'].id}. They worked together like a tiny harbor crew.",
        ),
        QAItem(
            question="What problem did they find?",
            answer=f"They found {incident['problem']}.",
        ),
        QAItem(
            question="What clue helped them understand the trouble?",
            answer=f"They noticed that {incident['clue']}. That clue showed them where to fix the shutter.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They asked the shopkeeper for help and used a screwdriver and a cloth. Then {incident['fix'].lower()}",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The shutter became quiet and secure, and the friends felt proud because they solved the problem together.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a panel that covers a window or opening to block wind, rain, or bright light.",
        ),
        QAItem(
            question="Why is a historic harbor street special?",
            answer="A historic harbor street is special because it has old buildings, docks, and a long history by the sea.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means noticing what is wrong, thinking carefully, and choosing a good way to fix it.",
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    hero_name = args.name or rng.choice(HERO_NAMES)
    friend_name = args.friend or rng.choice(FRIEND_NAMES)
    if hero_name == friend_name:
        friend_name = rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    return StoryParams(
        place=place,
        hero_name=hero_name,
        friend_name=friend_name,
        seed=args.seed,
        incident=rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        warning=rng.randrange(len(WARNINGS)),
        turn=rng.randrange(len(TURNS)),
        ending=rng.randrange(len(ENDING_LINES)),
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale story world about friendship and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
        model = asp_valid()
        print(f"{len(model)} valid combinations:\n")
        for place, item in model:
            print(f"  {place:10} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(place=place, hero_name=f"{place.title()}Hero", friend_name=f"{place.title()}Friend")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
