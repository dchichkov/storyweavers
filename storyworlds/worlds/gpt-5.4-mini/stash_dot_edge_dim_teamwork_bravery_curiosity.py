#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/stash_dot_edge_dim_teamwork_bravery_curiosity.py
=================================================================================

A standalone story world for a tiny detective tale: a curious child and a brave
friend follow a dot clue, work together at the edge-dim of dusk, find a stash,
and learn that teamwork is the best magnifying glass.

The domain is intentionally small and classical:
- a clue appears
- curiosity and bravery push the search forward
- teamwork helps the pair examine the scene
- the hidden stash is found and the mystery resolves

The story uses the seed words stash, dot, and edge-dim, while keeping the tone
close to a kid-friendly detective story.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/stash_dot_edge_dim_teamwork_bravery_curiosity.py
    python storyworlds/worlds/gpt-5.4-mini/stash_dot_edge_dim_teamwork_bravery_curiosity.py --qa
    python storyworlds/worlds/gpt-5.4-mini/stash_dot_edge_dim_teamwork_bravery_curiosity.py --all
    python storyworlds/worlds/gpt-5.4-mini/stash_dot_edge_dim_teamwork_bravery_curiosity.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    mood: str
    edge: str
    clue_spot: str
    hiding_spot: str
    result_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class SearchItem:
    id: str
    label: str
    phrase: str
    found_when: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    setting: str
    stash: str
    clue: str
    response: str
    hero: str
    hero_gender: str
    partner: str
    partner_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_teamwork(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.memes["teamwork"] < THRESHOLD:
            continue
        sig = ("teamwork", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["confidence"] += 1
        out.append("__teamwork__")
    return out


def _r_clue(world: World) -> list[str]:
    out = []
    clue = world.entities.get("clue")
    if clue and clue.meters["noticed"] >= THRESHOLD:
        sig = ("clue", clue.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__clue__")
    return out


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


CAUSAL_RULES = [
    Rule("teamwork", "social", _r_teamwork),
    Rule("clue", "physical", _r_clue),
]


def valid_pair(stash: SearchItem, clue: SearchItem) -> bool:
    return stash.id == "stash" and clue.id == "dot"


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def clue_at_risk(clue: SearchItem) -> bool:
    return clue.id == "dot"


def outcome_of(params: StoryParams) -> str:
    return "found" if params.response in RESPONSES else "found"


def _set_pair(name: str) -> tuple[str, str]:
    if name == "mira_ace":
        return "Mira", "Ace"
    if name == "nina_jo":
        return "Nina", "Jo"
    if name == "leo_ivy":
        return "Leo", "Ivy"
    return "Pip", "Mina"


SETTINGS = {
    "edge_dim_park": Setting(
        "edge_dim_park",
        "the edge-dim park",
        "quiet",
        "edge-dim",
        "under the bench",
        "behind the planter box",
        "the tiny stash box opened in the last streak of light",
    ),
    "alley_garden": Setting(
        "alley_garden",
        "the small alley garden",
        "still",
        "edge-dim",
        "beside the wall",
        "under the flower crate",
        "the stash sat safe in the open palm of the evening",
    ),
    "library_steps": Setting(
        "library_steps",
        "the steps by the library",
        "hushed",
        "edge-dim",
        "near the railing",
        "inside the loose stone",
        "the stash was found before the lamps blinked on",
    ),
}

STASHES = {
    "stash": SearchItem("stash", "stash", "a little stash", "hidden in the hiding spot", tags={"stash"}),
    "box": SearchItem("box", "box", "a small box", "tucked away", tags={"stash"}),
    "tin": SearchItem("tin", "tin", "a round tin", "carefully covered", tags={"stash"}),
}

CLUES = {
    "dot": SearchItem("dot", "dot", "a dot clue", "noticed at once", tags={"dot", "clue"}),
    "smudge": SearchItem("smudge", "smudge", "a tiny smudge", "seen after looking twice", tags={"clue"}),
    "crumb": SearchItem("crumb", "crumb", "a crumb trail", "spotted near the edge", tags={"clue"}),
}

RESPONSES = {
    "look_close": Response(
        "look_close",
        3,
        "leaned in together and looked close to the dot until the shape made sense",
        "leaned in together and looked close to the dot until the shape made sense",
        tags={"curiosity"},
    ),
    "share_lamp": Response(
        "share_lamp",
        3,
        "shared a small lamp and used its soft circle of light to check the edge-dim corner",
        "shared a small lamp and used its soft circle of light to check the edge-dim corner",
        tags={"teamwork"},
    ),
    "trace_steps": Response(
        "trace_steps",
        2,
        "followed the small marks step by step until the stash was right there",
        "followed the small marks step by step until the stash was right there",
        tags={"curiosity"},
    ),
}

GIRL_NAMES = ["Mina", "Ivy", "Luna", "Nora", "Zoe", "Lily"]
BOY_NAMES = ["Pip", "Leo", "Owen", "Ben", "Theo", "Max"]
TRAITS = ["curious", "brave", "careful", "bright", "steady"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--stash", choices=STASHES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--partner")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = []
    for sid in SETTINGS:
        for stash in STASHES:
            for clue in CLUES:
                if valid_pair(STASHES[stash], CLUES[clue]):
                    combos.append((sid, stash, clue))
    return combos


def explain_rejection(stash: SearchItem, clue: SearchItem) -> str:
    return f"(No story: this mystery needs a real stash and a dot clue. Try stash + dot.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.stash and args.clue and not valid_pair(STASHES[args.stash], CLUES[args.clue]):
        raise StoryError(explain_rejection(STASHES[args.stash], CLUES[args.clue]))

    combos = [c for c in valid_combos()
              if args.setting is None or c[0] == args.setting
              and (args.stash is None or c[1] == args.stash)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, stash, clue = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    partner = args.partner or rng.choice([n for n in (BOY_NAMES if partner_gender == "boy" else GIRL_NAMES) if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, stash, clue, response, hero, hero_gender, partner, partner_gender, parent, trait)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero = world.add(Entity(params.hero, kind="character", type=params.hero_gender, role="detective", traits=[params.trait]))
    partner = world.add(Entity(params.partner, kind="character", type=params.partner_gender, role="helper", traits=["steady"]))
    parent = world.add(Entity("Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    stash = world.add(Entity("stash", type="thing", label=STASHES[params.stash].phrase))
    clue = world.add(Entity("clue", type="thing", label=CLUES[params.clue].phrase))

    hero.memes["curiosity"] = 3.0
    hero.memes["bravery"] = 2.0
    partner.memes["teamwork"] = 3.0

    world.say(f"At {setting.place}, {hero.id} and {partner.id} were playing detective in the {setting.mood} air.")
    world.say(f"{hero.id} spotted {clue.label} near {setting.clue_spot}, and it felt like a clue on purpose.")
    world.say(f'"That could lead to a stash," said {partner.id}, and {hero.id} smiled at the idea.')

    world.para()
    hero.meters["noticed"] += 1
    partner.memes["teamwork"] += 1
    propagate(world, narrate=False)
    world.say(f"The light was {setting.edge}, but {hero.id} was brave enough to keep looking.")
    world.say(f"{partner.id} held still so {hero.id} could examine the dot clue without missing a thing.")

    world.para()
    response = RESPONSES[params.response]
    if response.id == "share_lamp":
        world.say(f'Together they {response.text}.')
    elif response.id == "trace_steps":
        world.say(f'With careful teamwork, they {response.text}.')
    else:
        world.say(f'As a team, they {response.text}.')

    stash.meters["found"] += 1
    hero.memes["pride"] += 1
    partner.memes["pride"] += 1
    world.say(f"Behind {setting.hiding_spot}, the {params.stash} was real: a tiny thing, but worth the chase.")
    world.say(f"Inside it was a note and a shiny token, and the whole mystery made sense at last.")
    world.say(f"By the time they walked home, the {setting.result_image}, and the children grinned like true detectives.")

    world.facts.update(
        hero=hero, partner=partner, parent=parent, setting=setting,
        stash=stash, clue=clue, response=response,
        outcome="found", promised=True
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a kid-friendly detective story that includes the words "stash", "dot", and "edge-dim".',
        f"Tell a mystery story where {f['hero'].id} and {f['partner'].id} use teamwork, bravery, and curiosity to follow a dot clue to a stash.",
        f"Write a short detective tale for a young child with a dim evening, a hidden stash, and a brave discovery.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, partner, setting = f["hero"], f["partner"], f["setting"]
    return [
        ("Who are the story about?", f"It is about {hero.id} and {partner.id}, two little detectives who work together."),
        ("What clue did they find?", f"They found a {f['clue'].label} and followed it carefully."),
        ("What did teamwork help them do?", f"Teamwork helped them search the edge-dim place without giving up. It also helped them examine the clue closely and find the stash."),
        ("What did they discover in the end?", f"They discovered the {f['stash'].label} hidden by {setting.hiding_spot}."),
        ("How did the story end?", f"It ended with the stash found, the mystery solved, and the children feeling proud and brave."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a stash?", "A stash is a hidden group of things kept out of sight for later."),
        ("What is a clue?", "A clue is a small hint that can help solve a mystery."),
        ("What does curious mean?", "Curious means wanting to know more and asking questions."),
        ("What does teamwork mean?", "Teamwork means people help each other and do a job together."),
        ("What does brave mean?", "Brave means you keep going even when something feels a little scary."),
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, St, C) :- setting(S), stash(St), clue(C), pair_ok(St, C).
pair_ok(stash, dot).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for x in STASHES:
        lines.append(asp.fact("stash", x))
    for x in CLUES:
        lines.append(asp.fact("clue", x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


CURATED = [
    StoryParams("edge_dim_park", "stash", "dot", "look_close", "Mira", "girl", "Ace", "boy", "mother", "curious"),
    StoryParams("alley_garden", "stash", "dot", "share_lamp", "Pip", "boy", "Mina", "girl", "father", "brave"),
    StoryParams("library_steps", "stash", "dot", "trace_steps", "Nora", "girl", "Leo", "boy", "mother", "steady"),
]


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it is not sensible enough for this detective story.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(explain_response(args.response))
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, stash, clue = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(sensible_responses(), key=lambda r: r.id)).id
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    partner_choices = [n for n in (BOY_NAMES if partner_gender == "boy" else GIRL_NAMES) if n != hero]
    partner = args.partner or rng.choice(partner_choices)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, stash, clue, response, hero, hero_gender, partner, partner_gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, stash, clue) combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.partner}: {p.setting} / {p.stash} / {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
