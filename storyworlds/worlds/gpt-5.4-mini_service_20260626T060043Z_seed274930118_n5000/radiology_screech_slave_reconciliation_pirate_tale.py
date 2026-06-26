#!/usr/bin/env python3
"""
storyworlds/worlds/radiology_screech_slave_reconciliation_pirate_tale.py
========================================================================

A standalone story world: pirate tale with a radiology nook, a sharp screech,
an enslaved deckhand, and a reconciliation ending.

Premise:
- On a pirate ship, a loud screech seems to point to theft and trouble.
- A small radiology lantern-box can look inside things without breaking them.
- The captain blames a slave deckhand at first.
- The scan reveals the real cause, and the ship makes peace.

This world keeps the classical structure:
- setup: the crew, the ship, the treasured item, and the odd screech
- tension: suspicion grows, voices rise, and the captive deckhand is cornered
- turn: a radiology scan reveals the screech came from a trapped gull feather
- resolution: reconciliation, apology, and a calmer deck

The story engine uses a tiny stateful simulation with both physical meters and
emotional memes, plus an inline ASP twin for validity checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["noise", "damage", "dust", "care", "work", "risk"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "fear", "anger", "trust", "guilt", "relief", "reconcile"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captainess"}
        male = {"boy", "man", "father", "captain", "slave", "deckhand", "pirate", "sailor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the pirate ship"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    noise: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    reveals: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.current_activity: Optional[str] = None

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        c.current_activity = self.current_activity
        return c


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero: str
    captain: str
    name2: str
    seed: Optional[int] = None


SETTINGS = {
    "deck": Setting(place="the main deck", affords={"scan", "listen"}),
    "cabin": Setting(place="the lantern cabin", affords={"scan"}),
    "hold": Setting(place="the cargo hold", affords={"scan", "listen"}),
}

ACTIVITIES = {
    "screech": Activity(
        id="screech",
        verb="follow the screech",
        gerund="following the screech",
        rush="rush toward the sound",
        noise="screech",
        keyword="screech",
        tags={"sound", "bird"},
    ),
    "radiology": Activity(
        id="radiology",
        verb="use the radiology lamp",
        gerund="using the radiology lamp",
        rush="carry the radiology lamp below deck",
        noise="hum",
        keyword="radiology",
        tags={"radiology", "light"},
    ),
    "slave": Activity(
        id="slave",
        verb="ask the slave deckhand for help",
        gerund="asking the enslaved deckhand for help",
        rush="snap at the enslaved deckhand",
        noise="harsh words",
        keyword="slave",
        tags={"slave", "ship"},
    ),
}

PRIZES = {
    "key": Prize(label="key", phrase="a little brass key", type="key", region="hand"),
    "map": Prize(label="map", phrase="the captain's sea map", type="map", region="chest"),
    "ring": Prize(label="ring", phrase="a silver shell ring", type="ring", region="hand"),
}

TOOLS = [
    Tool(
        id="scanlamp",
        label="a radiology lamp",
        prep="bring the radiology lamp to the dark cabin",
        tail="held the lamp steady and looked at the glowing shape inside",
        reveals={"feather", "bone", "chip"},
    ),
]


def _char(name: str, ctype: str, label: str = "") -> Entity:
    return Entity(id=name, kind="character", type=ctype, label=label or name)


def build_world(params: StoryParams) -> World:
    w = World(SETTINGS[params.place])
    hero = w.add(_char(params.hero, "pirate", params.hero))
    captain = w.add(_char(params.captain, "captain", params.captain))
    helper = w.add(_char(params.name2, "slave", f"the slave {params.name2}"))
    prize = w.add(Entity(id="prize", type=params.prize, label=PRIZES[params.prize].label,
                         phrase=PRIZES[params.prize].phrase, owner=captain.id,
                         caretaker=captain.id, region=PRIZES[params.prize].region))
    tool = w.add(Entity(id=TOOLS[0].id, type="tool", label=TOOLS[0].label,
                        owner=hero.id, caretaker=hero.id))
    w.facts.update(hero=hero, captain=captain, helper=helper, prize=prize, tool=tool)
    return w


def predict_scanner(world: World) -> bool:
    sim = world.copy()
    sim.current_activity = "radiology"
    sim.facts["cause"] = "feather"
    return True


def tell_story(world: World) -> None:
    hero = world.facts["hero"]
    captain = world.facts["captain"]
    helper = world.facts["helper"]
    prize = world.facts["prize"]

    hero.memes["joy"] += 1
    world.say(
        f"On {world.setting.place}, {hero.id} was a little pirate with quick eyes and a brave step."
    )
    world.say(
        f"{hero.id} loved the strange glow of {TOOLS[0].label} and the way the ship could whisper in the dark."
    )
    world.say(
        f"One evening a sharp screech split the air, and everybody on deck froze."
    )
    captain.memes["fear"] += 1
    captain.memes["anger"] += 1
    helper.memes["fear"] += 1
    helper.memes["trust"] += 1

    world.para()
    world.say(
        f"{captain.id} clutched {prize.phrase} and frowned at {helper.label_word if hasattr(helper, 'label_word') else helper.id}."
    )
    world.say(
        f"\"That screech means somebody meddled with my treasure,\" {captain.id} barked."
    )
    world.say(
        f"The blame landed on {helper.label}, the enslaved deckhand, and the poor soul looked down at the boards."
    )
    helper.memes["fear"] += 1
    helper.memes["guilt"] += 0.5

    world.para()
    world.say(
        f"But {hero.id} heard the sound again and noticed it came from the lantern cabin, not from {helper.id}."
    )
    world.say(
        f"{hero.id} asked for {TOOLS[0].label} and said, \"Let's look before we shout.\""
    )
    world.say(
        f"{hero.id} and {helper.id} {TOOLS[0].prep}."
    )
    world.say(
        f"Inside the glow, they saw a tiny gull feather stuck in a crack of the old cage, and that was what had been making the screech."
    )
    world.say(
        f"The treasure was safe; the loud sound had only bounced through the metal and wood."
    )
    world.facts["cause"] = "feather"
    world.facts["resolved"] = True

    captain.memes["anger"] = 0.0
    captain.memes["relief"] += 1
    helper.memes["fear"] = 0.0
    helper.memes["guilt"] = 0.0
    helper.memes["trust"] += 1
    helper.memes["reconcile"] += 1

    world.para()
    world.say(
        f"{captain.id} went quiet, then bowed his head and said sorry to {helper.label}."
    )
    world.say(
        f"\"You were not the trouble. I was wrong to blame you,\" {captain.id} said."
    )
    world.say(
        f"{hero.id} smiled, the feather was plucked away, and the whole ship felt calmer."
    )
    world.say(
        f"By the end of the night, {captain.id}, {hero.id}, and {helper.id} stood together under the stars, reconciled at last."
    )


def generate_story_text(params: StoryParams) -> World:
    world = build_world(params)
    tell_story(world)
    return world


def gen_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a small pirate tale that includes the words "{f["tool"].label}", "screech", and "radiology".',
        f"Tell a child-friendly pirate story where {f['captain'].id} blames a slave deckhand, then learns the screech had another cause.",
        f"Write a reconciliation story aboard a pirate ship, with a glowing scan that helps the crew tell the truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, helper, prize = f["hero"], f["captain"], f["helper"], f["prize"]
    return [
        QAItem(
            question=f"Who heard the screech first on the ship?",
            answer=f"{hero.id} heard it first and paid attention before anyone else understood what it meant.",
        ),
        QAItem(
            question=f"Why did {captain.id} blame {helper.label} at first?",
            answer=f"{captain.id} thought the screech meant someone had meddled with the treasure, so the enslaved deckhand was blamed before the crew had proof.",
        ),
        QAItem(
            question=f"What did the radiology lamp reveal?",
            answer="It revealed a tiny gull feather stuck in the old cage, which was the real cause of the screech.",
        ),
        QAItem(
            question=f"How did the story end for the captain and the enslaved deckhand?",
            answer=f"They apologized, told the truth, and ended in reconciliation instead of anger.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a radiology lamp help people do?",
            answer="A radiology lamp helps people see inside things without breaking them open, so they can find hidden causes or injuries.",
        ),
        QAItem(
            question="What is a screech?",
            answer="A screech is a very sharp, high sound that can hurt your ears and make people look around quickly.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop fighting, tell the truth, and make peace again after a disagreement.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.region:
            parts.append(f"region={e.region}")
        lines.append(f"{e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for activity in ACTIVITIES:
            for prize in PRIZES:
                if activity == "radiology" and prize in {"key", "ring", "map"}:
                    out.append((place, activity, prize))
                if activity == "screech" and prize in {"key", "ring"}:
                    out.append((place, activity, prize))
                if activity == "slave" and prize in {"map"}:
                    out.append((place, activity, prize))
    return out


@dataclass
class ReasonGate:
    activity: str
    prize: str


def reasonableness_ok(activity: Activity, prize: Prize) -> bool:
    if activity.id == "radiology":
        return prize.label in {"key", "ring", "map"}
    if activity.id == "screech":
        return prize.label in {"key", "ring"}
    if activity.id == "slave":
        return prize.label in {"map"}
    return False


ASP_RULES = r"""
valid(Place,A,P) :- setting(Place), activity(A), prize(P),
    A = radiology, (P = key; P = ring; P = map).
valid(Place,A,P) :- setting(Place), activity(A), prize(P),
    A = screech, (P = key; P = ring).
valid(Place,A,P) :- setting(Place), activity(A), prize(P),
    A = slave, P = map.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with radiology, screech, slave, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--captain")
    ap.add_argument("--name2")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.activity and args.prize:
        if not reasonableness_ok(ACTIVITIES[args.activity], PRIZES[args.prize]):
            raise StoryError("Invalid story: that activity cannot honestly affect that prize.")
    picks = [c for c in combos
             if (args.place is None or c[0] == args.place)
             and (args.activity is None or c[1] == args.activity)
             and (args.prize is None or c[2] == args.prize)]
    if not picks:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(picks))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        hero=args.hero or rng.choice(["Ari", "Mina", "Tess", "Jory"]),
        captain=args.captain or rng.choice(["Red Jack", "Captain Brine", "Old Mara"]),
        name2=args.name2 or rng.choice(["Ned", "Jem", "Wren"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_story_text(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=gen_prompts(world),
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid_combos()
        print(f"{len(vals)} compatible combos:")
        for v in vals:
            print(v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, activity, prize in valid_combos():
            params = StoryParams(place=place, activity=activity, prize=prize,
                                 hero="Ari", captain="Captain Brine", name2="Ned")
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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
