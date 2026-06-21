#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ultra_waltz_sink_dialogue_flashback_surprise_pirate.py
======================================================================================

A tiny pirate-style storyworld about a child crew in a ship galley, a sink, a
lost ultra-important trinket, a remembered flashback, a dialogue turn, and a
surprise ending that changes the world state.

The world is intentionally small and classical:
- two children on a ship
- one sink or washbasin
- one missing object
- one helper adult
- one surprise that resolves the story

The seed words are woven into the story:
- ultra
- waltz
- sink

Narrative instruments:
- Dialogue
- Flashback
- Surprise
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False
    can_hold: bool = False
    can_search: bool = False
    can_help: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    mood: str


@dataclass(frozen=True)
class Trinket:
    id: str
    label: str
    phrase: str
    color: str
    important: bool = True


@dataclass(frozen=True)
class Helper:
    id: str
    label: str
    surprise_gift: str
    knows_flashback: bool = True


@dataclass(frozen=True)
class Conflict:
    id: str
    clue: str
    search_word: str
    risk_word: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    lost = world.get("trinket")
    if lost.meters["missing"] >= THRESHOLD:
        for cid in ("child1", "child2"):
            kid = world.get(cid)
            if kid.memes["worry"] < THRESHOLD:
                kid.memes["worry"] += 1
                out.append("")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child1").memes["remember"] >= THRESHOLD and ("flashback", "told") not in world.fired:
        world.fired.add(("flashback", "told"))
        world.get("child1").memes["relief"] += 1
        world.get("child2").memes["curiosity"] += 1
        out.append("__flashback__")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    if world.get("trinket").meters["found"] >= THRESHOLD and ("surprise", "gift") not in world.fired:
        world.fired.add(("surprise", "gift"))
        world.get("child1").memes["joy"] += 1
        world.get("child2").memes["joy"] += 1
        out.append("__surprise__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("worry", "social", _r_worry),
    Rule("flashback", "memory", _r_flashback),
    Rule("surprise", "ending", _r_surprise),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "galley": Setting(id="galley", place="the ship's galley", mood="salty"),
    "harbor": Setting(id="harbor", place="the dockside washroom", mood="bright"),
}

TRINKETS = {
    "map_token": Trinket(id="map_token", label="ultra map token", phrase="an ultra-bright map token", color="gold"),
    "song_shell": Trinket(id="song_shell", label="song shell", phrase="a pearly song shell", color="white"),
}

HELPERS = {
    "captain": Helper(id="captain", label="Captain Mira", surprise_gift="a tiny compass lantern"),
    "cook": Helper(id="cook", label="Cook Finn", surprise_gift="a snack box and a clean cloth"),
}

CONFLICTS = {
    "sink": Conflict(id="sink", clue="the sink", search_word="sink", risk_word="sink"),
}

GIRL_NAMES = ["Mina", "Luna", "Nell", "Ruby"]
BOY_NAMES = ["Toby", "Finn", "Pip", "Jax"]
TRAITS = ["bold", "curious", "careful", "cheerful"]


@dataclass
class StoryParams:
    setting: str
    trinket: str
    helper: str
    conflict: str
    name1: str
    type1: str
    name2: str
    type2: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate storyworld with dialogue, flashback, and surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trinket", choices=TRINKETS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--conflict", choices=CONFLICTS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TRINKETS:
            for c in CONFLICTS:
                combos.append((s, t, c))
    return combos


def explain_invalid() -> str:
    return "(No story: this tiny world only knows the ship's sink mystery.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.trinket is None or c[1] == args.trinket)
              and (args.conflict is None or c[2] == args.conflict)]
    if not combos:
        raise StoryError(explain_invalid())
    setting, trinket, conflict = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    gender1 = rng.choice(["girl", "boy"])
    gender2 = "boy" if gender1 == "girl" else "girl"
    name1 = rng.choice(GIRL_NAMES if gender1 == "girl" else BOY_NAMES)
    name2 = rng.choice([n for n in (BOY_NAMES if gender2 == "boy" else GIRL_NAMES) if n != name1])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, trinket=trinket, helper=helper, conflict=conflict,
                       name1=name1, type1=gender1, name2=name2, type2=gender2, trait=trait)


def _setup(world: World, p: StoryParams) -> tuple[Entity, Entity, Entity, Entity, Entity]:
    a = world.add(Entity(id="child1", kind="character", type=p.type1, label=p.name1, role="explorer", traits=[p.trait]))
    b = world.add(Entity(id="child2", kind="character", type=p.type2, label=p.name2, role="mate", traits=["loyal"]))
    helper = world.add(Entity(id="helper", kind="character", type="father", label=HELPERS[p.helper].label, role="helper", can_help=True))
    sink = world.add(Entity(id="sink", kind="thing", label="the sink", can_search=True, attrs={"place": SETTINGS[p.setting].place}))
    trinket = world.add(Entity(id="trinket", kind="thing", label=TRINKETS[p.trinket].label, attrs={"color": TRINKETS[p.trinket].color}))
    trinket.meters["missing"] = 1
    world.facts["setting"] = SETTINGS[p.setting]
    world.facts["helper_cfg"] = HELPERS[p.helper]
    world.facts["trinket_cfg"] = TRINKETS[p.trinket]
    world.facts["conflict_cfg"] = CONFLICTS[p.conflict]
    return a, b, helper, sink, trinket


def tell_story(world: World, p: StoryParams) -> None:
    a, b, helper, sink, trinket = _setup(world, p)
    world.say(f"On a salty morning, {a.label} and {b.label} played pirate games in {SETTINGS[p.setting].place}.")
    world.say(f"They searched for {TRINKETS[p.trinket].phrase}, because the little token was the heart of their treasure hunt.")
    world.para()
    world.say(f'"Where did it go?" asked {b.label}.')
    world.say(f'"Maybe near {CONFLICTS[p.conflict].clue}," said {a.label}. "Let\'s look by {CONFLICTS[p.conflict].search_word}."')
    a.memes["remember"] += 1
    propagate(world, narrate=False)
    world.say(f"Then {a.label} remembered a flashback: earlier, the token had slid across the table with a tiny clink and vanished toward {sink.label_word}.")
    world.say(f'"I saw it! It went by {sink.label_word}!" {a.label} said.')
    world.para()
    world.say(f'They peeked under the basin and looked inside {sink.label_word}. "There it is!" cried {b.label}.')
    trinket.meters["missing"] = 0
    trinket.meters["found"] = 1
    world.say(f"Their search turned into a surprise when {helper.label} arrived carrying {HELPERS[p.helper].surprise_gift}.")
    world.say(f'"You found the ultra treasure," said {helper.label}, smiling at their muddy paws.')
    propagate(world, narrate=False)
    world.para()
    world.say(f'{helper.label} gave them the gift, and the children did a little waltz across the galley floor, careful not to bump the sink.')
    world.say(f'"Now the crew can sail again," said {b.label}. "And this time we know where to look."')
    world.facts.update(child1=a, child2=b, helper=helper, sink=sink, trinket=trinket,
                       outcome="found", setting=p.setting, seed=p.seed)


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, helper = f["child1"], f["child2"], f["helper"]
    trinket = f["trinket_cfg"]
    return [
        ("Who was the story about?",
         f"It was about {a.label} and {b.label}, two little pirates in the ship's galley. They were searching for {trinket.phrase} together."),
        ("What did the sink have to do with the story?",
         f"The sink was the place they checked when they could not find the token. It gave the children a clue about where the treasure had slid."),
        ("What did the flashback do?",
         f"The flashback showed what had happened earlier, so {a.label} could remember the token's little clink and where it went. That memory helped solve the mystery."),
        ("What was the surprise at the end?",
         f"{helper.label} arrived with a gift after the children found the token. The surprise made the ending brighter and turned the search into a happy pirate win."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a sink?", answer="A sink is a basin where water goes down the drain. People wash things there and sometimes look around it when something is lost."),
        QAItem(question="What is a waltz?", answer="A waltz is a gentle dance with smooth steps. People can waltz slowly and carefully across a floor."),
        QAItem(question="What does ultra mean?", answer="Ultra means extra strong, extra bright, or extra big. It is a word that gives something a very powerful feel."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    trinket = f["trinket_cfg"].label
    return [
        f'Write a pirate story for a young child that includes the words "ultra", "waltz", and "sink".',
        f"Tell a short story with dialogue and a flashback where two pirates search for {trinket} and find it near the sink.",
        f"Write a surprising pirate tale where the children remember a clue, speak to each other, and end with a happy gift.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        out.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({a for a, *_ in world.fired})}")
    return "\n".join(out)


CURATED = [
    StoryParams(setting="galley", trinket="map_token", helper="captain", conflict="sink",
                name1="Mina", type1="girl", name2="Toby", type2="boy", trait="curious"),
    StoryParams(setting="harbor", trinket="song_shell", helper="cook", conflict="sink",
                name1="Finn", type1="boy", name2="Luna", type2="girl", trait="careful"),
]


ASP_RULES = r"""
missing(X) :- trinket(X), not found(X).
worry(C) :- child(C), missing(trinket).
flashback :- remember(C), child(C).
surprise :- found(trinket), helper(H).

#show valid/3.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TRINKETS:
        lines.append(asp.fact("trinket", tid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for cid in CONFLICTS:
        lines.append(asp.fact("conflict", cid))
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
    rc = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generate() succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.trinket not in TRINKETS:
        raise StoryError("Unknown trinket.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if params.conflict not in CONFLICTS:
        raise StoryError("Unknown conflict.")
    world = World()
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for item in asp_valid_combos():
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
