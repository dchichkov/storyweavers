#!/usr/bin/env python3
"""
A small fable-like storyworld about curiosity, repetition, and inner monologue.

Seed tale:
- A little creature named Pip lives by a narrow path and loves to scootch.
- Pip is told not to open a shady gate because it leads to a windy hill.
- Curiosity keeps returning; Pip repeats a small approach, listening and edging closer.
- The turning point comes when Pip uses the careful way instead of the bold way.
- The ending proves the change: the gate stays shut, the lesson sticks, and Pip learns that
  wonder is good when it walks beside patience.

This script models a tiny classical simulation where:
- physical meters matter: distance, gate position, wind exposure, fatigue
- emotional memes matter: curiosity, caution, worry, resolve, pride, relief
- repetition matters as a repeated action that can raise caution or fatigue
- inner monologue matters as a narrated private thought that influences choices

The tone aims for a child-facing fable: simple, concrete, gently moral, and state-driven.
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

# ---------------------------------------------------------------------------
# Core thresholds and small domain vocab
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

ANIMALS = ["mouse", "fox", "rabbit", "hedgehog", "badger"]
NAMES = {
    "mouse": ["Pip", "Mina", "Toby", "Lark", "Nell"],
    "fox": ["Fenn", "Ruby", "Tess", "Sol", "Wren"],
    "rabbit": ["Bibi", "Milo", "Pia", "Jun", "Clover"],
    "hedgehog": ["Dot", "Gus", "Poppy", "Nori", "Fern"],
    "badger": ["Bram", "Ari", "Moss", "Ivy", "Rowan"],
}

PLACES = {
    "burrow": "the burrow lane",
    "garden": "the garden edge",
    "path": "the little path",
    "orchard": "the orchard fence",
}

MORALS = [
    "Curiosity is bright, but patience keeps it safe.",
    "A small question can walk far when it wears careful shoes.",
    "It is wise to look twice before scootching once.",
    "Wonder is good when it listens first.",
]


# ---------------------------------------------------------------------------
# Entities and world state
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rabbit", "hedgehog", "badger"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type == "fox":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    name: str
    wonder: str
    allowed_actions: set[str] = field(default_factory=set)


@dataclass
class ObjectKind:
    id: str
    label: str
    phrase: str
    region: str
    protects: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class ActionKind:
    id: str
    verb: str
    gerund: str
    step: str
    mess: str
    effect: str
    zone: set[str]
    keyword: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.history: list[str] = []

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
            self.history.append(text)

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
        c.history = list(self.history)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "burrow": Setting(place="the burrow lane", name="Burrow Lane", wonder="a gate at the end of the lane", allowed_actions={"scootch"}),
    "garden": Setting(place="the garden edge", name="Garden Edge", wonder="a gate behind the ivy", allowed_actions={"scootch"}),
    "path": Setting(place="the little path", name="Little Path", wonder="a gate by the stones", allowed_actions={"scootch"}),
    "orchard": Setting(place="the orchard fence", name="Orchard Fence", wonder="a gate under the apples", allowed_actions={"scootch"}),
}

ACTIONS = {
    "scootch": ActionKind(
        id="scootch",
        verb="scootch closer",
        gerund="scootching closer",
        step="scootched another little step",
        mess="dust",
        effect="tiny dust",
        zone={"path"},
        keyword="scootch",
    )
}

OBJECTS = {
    "lantern": ObjectKind(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        region="paws",
        protects={"dark"},
    ),
    "boots": ObjectKind(
        id="boots",
        label="boots",
        phrase="soft little boots",
        region="feet",
        protects={"mud"},
        plural=True,
    ),
    "cloak": ObjectKind(
        id="cloak",
        label="cloak",
        phrase="a green cloak",
        region="back",
        protects={"wind"},
    ),
}

TRAITS = ["curious", "quiet", "brave", "thoughtful", "hasty"]

CURATED = [
    ("burrow", "mouse", "lantern", "curious"),
    ("garden", "rabbit", "boots", "thoughtful"),
    ("path", "hedgehog", "cloak", "quiet"),
    ("orchard", "fox", "lantern", "hasty"),
]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    animal: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model helpers and causal rules
# ---------------------------------------------------------------------------

def _ensure_meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _ensure_meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _rule_repetition(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if _ensure_meme(hero, "curiosity") < THRESHOLD:
        return out
    if _ensure_meter(hero, "steps") < 2:
        return out
    sig = ("repetition",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1.0
    hero.memes["reflection"] = hero.memes.get("reflection", 0.0) + 1.0
    out.append("Each repeated little step made the thought slower and safer.")
    return out


def _rule_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    gate = world.get("gate")
    if _ensure_meter(gate, "open") < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    out.append("The open gate made the breeze feel bigger.")
    return out


def _rule_resolution(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    gate = world.get("gate")
    if _ensure_meme(hero, "caution") < THRESHOLD:
        return out
    if _ensure_meter(gate, "open") >= THRESHOLD:
        return out
    sig = ("resolve",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1.0
    hero.memes["curiosity"] = max(0.0, hero.memes.get("curiosity", 0.0) - 0.5)
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    out.append("The quiet choice made the little heart feel steady.")
    return out


CAUSAL_RULES = [_rule_worry, _rule_repetition, _rule_resolution]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
curious(H) :- hero(H), curiosity(H), curiosity(H, C), C >= 1.
repeated(H) :- hero(H), steps(H, N), N >= 2.
cautious(H) :- repeated(H), curious(H).
worry(H) :- gate_open(G), hero(H), gate(G).
resolved(H) :- cautious(H), gate_closed(G), gate(G).

#show curious/1.
#show repeated/1.
#show cautious/1.
#show worry/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("gate", "gate"))
    lines.append(asp.fact("curiosity", "hero"))
    lines.append(asp.fact("curiosity", "hero", 1))
    lines.append(asp.fact("steps", "hero", 2))
    lines.append(asp.fact("gate_closed", "gate"))
    lines.append(asp.fact("gate_open", "gate"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show curious/1.\n#show repeated/1.\n#show cautious/1.\n#show worry/1.\n#show resolved/1."))
    atoms = set((sym.name, tuple(getattr(a, "number", getattr(a, "string", a.name)) for a in sym.arguments)) for sym in model)
    expected = {
        ("curious", ("hero",)),
        ("repeated", ("hero",)),
        ("cautious", ("hero",)),
        ("resolved", ("hero",)),
    }
    if atoms == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH in ASP twin.")
    print("atoms:", sorted(atoms))
    print("expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def _init_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.animal, label=params.name))
    mentor = world.add(Entity(id="mentor", kind="character", type="mouse", label="Grand Sable"))
    gate = world.add(Entity(id="gate", kind="thing", type="gate", label="the gate"))
    prize = world.add(Entity(id="prize", kind="thing", type=params.prize, label=OBJECTS[params.prize].label, phrase=OBJECTS[params.prize].phrase, owner="hero"))
    hero.meters.update({"steps": 0.0, "distance": 0.0})
    hero.memes.update({"curiosity": 0.0, "caution": 0.0, "worry": 0.0, "resolve": 0.0, "pride": 0.0})
    mentor.memes.update({"calm": 1.0})
    gate.meters.update({"open": 0.0, "distance": 1.0})
    prize.meters.update({"safe": 1.0})
    world.facts.update(params=params, hero=hero, mentor=mentor, gate=gate, prize=prize, setting=setting)
    return world


def _start(world: World) -> None:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    prize = f["prize"]
    setting = f["setting"]
    trait = f["params"].trait
    world.say(f"{hero.label} was a {trait} little {hero.type} who lived near {setting.place}.")
    world.say(f"One bright morning, {hero.label} noticed {setting.wonder} and a {prize.phrase} hanging nearby.")
    world.say(f"{hero.label} loved to scootch, and {hero.pronoun('possessive')} feet always wanted one more look.")
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    mentor.memes["calm"] = mentor.memes.get("calm", 0.0) + 1.0
    world.say(f"Grand Sable said, \"A gate can teach you twice: once by asking, and once by waiting.\"")


def _middle(world: World) -> None:
    hero = world.get("hero")
    gate = world.get("gate")
    setting = world.setting
    act = ACTIONS["scootch"]

    world.para()
    world.say(f"{hero.label} went to {setting.place} and stood before {setting.wonder}.")
    world.say(f"In {hero.pronoun('possessive')} own head, {hero.label} thought, \"I only want one tiny look.\"")
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0

    for _ in range(2):
        hero.meters["steps"] = hero.meters.get("steps", 0.0) + 1.0
        hero.meters["distance"] = hero.meters.get("distance", 0.0) + 1.0
        world.say(f"{hero.label} {act.step}.")
        world.say(f"\"Just one more scootch,\" {hero.label} told {hero.pronoun('self') if False else 'themselves'} in a small inner voice.")
        propagate(world)

    gate.meters["open"] = 1.0
    world.say(f"Then the gate creaked open a little, and the windy hill breathed through the crack.")
    propagate(world)

    world.say(f"{hero.label} thought, \"This is the part where curiosity must wear caution.\"")
    hero.memes["curiosity"] = max(0.0, hero.memes.get("curiosity", 0.0) - 0.2)
    hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1.0


def _end(world: World) -> None:
    hero = world.get("hero")
    gate = world.get("gate")
    prize = world.get("prize")

    world.para()
    gate.meters["open"] = 0.0
    world.say(f"{hero.label} did not rush in.")
    world.say(f"Instead, {hero.label} scootched back to the flat stones and closed {hero.pronoun('possessive')} eyes to think.")
    world.say(f"\"I can be curious without being careless,\" {hero.label} thought.")
    propagate(world)

    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1.0
    hero.meters["steps"] += 1.0
    world.say(f"So {hero.label} tucked {prize.it()} safely under {hero.pronoun('possessive')} arm and waited for Grand Sable.")
    world.say(f"Grand Sable smiled and said, \"You found the best path: not no wonder, but wise wonder.\"")
    world.say(random.choice(MORALS))
    world.say(f"At sunset, the gate stood closed, the lane was calm, and {hero.label} felt proud of a careful heart.")


def tell(setting: Setting, animal: str, prize_id: str, name: str, trait: str) -> World:
    params = StoryParams(place=_setting_key(setting), animal=animal, prize=prize_id, name=name, trait=trait)
    world = _init_world(params)
    _start(world)
    _middle(world)
    _end(world)
    return world


def _setting_key(setting: Setting) -> str:
    for k, v in SETTINGS.items():
        if v is setting:
            return k
    return "path"


# ---------------------------------------------------------------------------
# Prompt and QA generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f'Write a short fable for a young child about {p.name}, a {p.trait} {p.animal}, who keeps wanting to "{ACTIONS["scootch"].keyword}" near {SETTINGS[p.place].wonder}.',
        f"Tell a gentle story with repetition and inner monologue where {p.name} learns to be curious and careful at {SETTINGS[p.place].name}.",
        f'Write a story that includes the word "{ACTIONS["scootch"].keyword}" and ends with a lesson about patience.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    hero = f["hero"]
    setting = f["setting"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.name}, a {p.trait} little {p.animal} who lives near {setting.place}.",
        ),
        QAItem(
            question=f"What did {p.name} keep wanting to do?",
            answer=f"{p.name} kept wanting to scootch closer to {setting.wonder}.",
        ),
        QAItem(
            question=f"What did {p.name} think in the inner monologue?",
            answer=f"{p.name} thought that one tiny look would be enough, but then realized curiosity needed caution.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {p.name} chose to wait, close the gate, and keep the lesson in mind.",
        ),
    ]
    if hero.memes.get("caution", 0.0) >= THRESHOLD:
        qa.append(
            QAItem(
                question=f"Why did the repeated scootching matter?",
                answer=f"The repeated scootching made {p.name} slow down and think, so caution grew stronger than hurry.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to know more about something new.",
        ),
        QAItem(
            question="Why can repetition matter?",
            answer="Repetition can matter because doing the same thing again can make a habit stronger or help a lesson stick.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talking a character does in their own mind.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that often uses animals and ends with a lesson.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that could produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child-level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params resolution and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like storyworld about scootch, curiosity, repetition, and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--prize", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, animal, prize) for place in SETTINGS for animal in ANIMALS for prize in OBJECTS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    place = args.place or rng.choice(list(SETTINGS))
    animal = args.animal or rng.choice(ANIMALS)
    prize = args.prize or rng.choice(list(OBJECTS))
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or rng.choice(NAMES[animal])
    return StoryParams(place=place, animal=animal, prize=prize, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.animal, params.prize, params.name, params.trait)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show curious/1.\n#show repeated/1.\n#show cautious/1.\n#show worry/1.\n#show resolved/1."))
    out = []
    for sym in model:
        out.append((sym.name,) + tuple(getattr(a, "name", getattr(a, "string", getattr(a, "number", a))) for a in sym.arguments))
    return out


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show curious/1.\n#show repeated/1.\n#show cautious/1.\n#show worry/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program("#show curious/1.\n#show repeated/1.\n#show cautious/1.\n#show worry/1.\n#show resolved/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, (place, animal, prize, trait) in enumerate(CURATED):
            params = StoryParams(place=place, animal=animal, prize=prize, name=NAMES[animal][i % len(NAMES[animal])], trait=trait, seed=base_seed + i)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.animal} at {p.place} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
