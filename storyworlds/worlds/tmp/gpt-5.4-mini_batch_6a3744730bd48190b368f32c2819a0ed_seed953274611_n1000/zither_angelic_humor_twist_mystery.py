#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/zither_angelic_humor_twist_mystery.py
=====================================================================

A standalone storyworld for a tiny mystery tale with a humorous twist:
a child hears an "angelic" sound, searches for the source, and discovers a
surprising, funny explanation involving a zither.

The world uses typed entities with physical meters and emotional memes, a small
forward-chaining rule engine, a Python reasonableness gate, and an inline ASP
twin for parity checks.
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
SUSPICION_MIN = 2
TWIST_REVEAL_MIN = 1.0


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
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    dark_place: str
    allows: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    sound: str
    where: str
    surprising: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    reveal: str
    punch: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_humor(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("child")
    if kid.meters["suspicion"] >= THRESHOLD and not world.facts.get("humor_done"):
        world.facts["humor_done"] = True
        kid.memes["amused"] += 1
        out.append("__humor__")
    return out


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("reveal_done") and not world.fired.__contains__(("twist",)):
        world.fired.add(("twist",))
        out.append("__twist__")
    return out


CAUSAL_RULES = [Rule("humor", "social", _r_humor), Rule("twist", "narrative", _r_twist)]


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


def predict_source(world: World, clue: Clue) -> dict:
    sim = world.copy()
    sim.get("child").meters["suspicion"] += 1
    sim.facts["reveal_done"] = True
    return {
        "suspicion": sim.get("child").meters["suspicion"],
        "reveal": True,
        "clue": clue.label,
    }


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for src_id, src in SOURCES.items():
            for clue_id, clue in CLUES.items():
                if src_id in setting.allows and clue_id in clue.tags:
                    combos.append((sid, src_id, clue_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    source: str
    clue: str
    twist: str
    child: str
    child_gender: str
    adult: str
    adult_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "hall": Setting(
        id="hall",
        place="the museum hall",
        dark_place="the shadowy gallery corner",
        allows={"zither", "cuckoo"},
    ),
    "attic": Setting(
        id="attic",
        place="the attic",
        dark_place="the old trunk corner",
        allows={"zither", "music_box"},
    ),
}

SOURCES = {
    "zither": Source(
        id="zither",
        label="a zither",
        sound="an angelic, twinkling sound",
        where="behind the curtain",
        surprising="a cat was sitting on the strings and plinking them with its tail",
        tags={"zither", "music", "angelic"},
    ),
    "music_box": Source(
        id="music_box",
        label="a music box",
        sound="an angelic little tune",
        where="inside the trunk",
        surprising="a toy wind-up mouse was bumping the keys again and again",
        tags={"music_box", "music"},
    ),
    "cuckoo": Source(
        id="cuckoo",
        label="a cuckoo clock",
        sound="an angelic chiming",
        where="on the wall",
        surprising="the clock had a paper bird stuck in its door",
        tags={"cuckoo", "clock"},
    ),
}

CLUES = {
    "feather": Clue("feather", "a white feather", "it had a tiny smudge of glitter", {"angelic"}),
    "note": Clue("note", "a handwritten note", "it said 'not a ghost, just a prank'", {"music", "angelic"}),
    "pawprint": Clue("pawprint", "a pawprint", "there were little muddy prints on the floor", {"zither"}),
}

TWISTS = {
    "cat": Twist("cat", "the mystery answer was a cat", "the cat looked very proud of itself", {"zither", "angelic"}),
    "mouse": Twist("mouse", "the mystery answer was a toy mouse", "the toy mouse had been winding itself back up", {"music_box"}),
}

GIRL_NAMES = ["Lily", "Maya", "Zoe", "Nora", "Mia"]
BOY_NAMES = ["Ben", "Theo", "Finn", "Leo", "Sam"]


def reasonableness_gate(source: Source, clue: Clue) -> bool:
    return source.id in clue.tags or "angelic" in source.tags


def explain_rejection(source: Source, clue: Clue) -> str:
    return f"(No story: {source.label} does not fit the clue {clue.label}, so the mystery would not be grounded.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld with a zither and an angelic twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["woman", "man"])
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.source is None or c[1] == args.source)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, source, clue = rng.choice(sorted(combos))
    twist = args.twist or rng.choice(sorted(TWISTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    child = args.child or _pick_name(rng, child_gender)
    adult = args.adult or ("Mom" if adult_gender == "woman" else "Dad")
    if not reasonableness_gate(SOURCES[source], CLUES[clue]):
        raise StoryError(explain_rejection(SOURCES[source], CLUES[clue]))
    return StoryParams(setting=setting, source=source, clue=clue, twist=twist,
                       child=child, child_gender=child_gender,
                       adult=adult, adult_gender=adult_gender)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child, role="sleuth"))
    adult = world.add(Entity(id="adult", kind="character", type=params.adult_gender, label=params.adult, role="helper"))
    setting = SETTINGS[params.setting]
    source = SOURCES[params.source]
    clue = CLUES[params.clue]
    twist = TWISTS[params.twist]

    world.say(f"{child.label} and {adult.label} were in {setting.place}.")
    world.say(f"Something in {setting.dark_place} made an angelic sound, and {child.label} frowned.")
    world.say(f'"That is strange," {child.label} said. "We should solve this mystery."')
    world.para()
    child.meters["suspicion"] += 1
    child.memes["curious"] += 1
    world.say(f"{child.label} tiptoed closer and found {clue.phrase}.")
    world.say(f"That clue mattered because {clue.phrase} hinted at {source.label}.")
    child.meters["suspicion"] += 1
    if child.meters["suspicion"] >= SUSPICION_MIN:
        world.say(f"{child.label} looked even more certain, but also a little silly-serious.")
    world.para()
    world.say(f"Behind the curtain, the answer waited: {source.surprising}.")
    world.facts["reveal_done"] = True
    propagate(world, narrate=False)
    world.say(f'Then came the twist: {twist.reveal}.')
    world.say(f'Everyone laughed when they saw it, because {twist.punch}.')
    world.say(f"In the end, the angelic sound was not a ghost at all; it was just a funny little accident.")
    world.say(f"{child.label} left smiling, and the mystery became a joke they could tell again and again.")
    world.facts.update(child=child, adult=adult, setting=setting, source=source, clue=clue, twist=twist, outcome="twist")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story that includes the words "{f["source"].label}" and "angelic".',
        f"Tell a funny mystery where {f['child'].label} hears an angelic sound, follows a clue, and discovers {f['source'].label}.",
        f"Write a short story with a twist ending and a little laugh, set in {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    source = f["source"]
    twist = f["twist"]
    return [
        ("What kind of story is this?", "It is a mystery story with a funny twist. The clues lead somewhere surprising instead of spooky."),
        (f"What did {child.label} hear?", f"{child.label} heard an angelic sound coming from the dark corner. That sound made the mystery feel important and worth solving."),
        ("What was the answer to the mystery?", f"The answer was {source.surprising}. The final twist showed that the strange angelic sound had a very ordinary and silly cause."),
        ("How did the story end?", f"It ended with a laugh, because {twist.punch}. The strange sound turned out to be harmless, so the mystery became a funny memory."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a zither?", "A zither is a stringed musical instrument that makes bright, twinkling notes when it is played."),
        ("What does angelic mean?", "Angelic means very gentle, pure, or beautiful, as if it sounded like a little choir of angels."),
        ("What is a twist in a story?", "A twist is a surprise change near the end that makes the story feel different from what you first expected."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="hall", source="zither", clue="pawprint", twist="cat", child="Lily", child_gender="girl", adult="Mom", adult_gender="woman"),
    StoryParams(setting="attic", source="music_box", clue="note", twist="mouse", child="Theo", child_gender="boy", adult="Dad", adult_gender="man"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.source not in SOURCES or params.clue not in CLUES or params.twist not in TWISTS:
        raise StoryError("(Invalid parameters.)")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for src_id, src in SOURCES.items():
        lines.append(asp.fact("source", src_id))
        for t in sorted(src.tags):
            lines.append(asp.fact("src_tag", src_id, t))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for t in sorted(clue.tags):
            lines.append(asp.fact("clue_tag", cid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Src, Clue) :- source(Src), clue(Clue), src_tag(Src, T), clue_tag(Clue, T).
valid_combo(Set, Src, Clue) :- setting(Set), valid(Src, Clue).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - asp_set:
            print("  only in python:", sorted(py - asp_set))
        if asp_set - py:
            print("  only in asp:", sorted(asp_set - py))
    try:
        s = generate(CURATED[0])
        assert s.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with a zither, an angelic sound, humor, and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["woman", "man"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.source is None or c[1] == args.source)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, source, clue = rng.choice(sorted(combos))
    twist = args.twist or rng.choice(sorted(TWISTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    child = args.child or _pick_name(rng, child_gender)
    adult = args.adult or ("Mom" if adult_gender == "woman" else "Dad")
    return StoryParams(setting=setting, source=source, clue=clue, twist=twist,
                       child=child, child_gender=child_gender,
                       adult=adult, adult_gender=adult_gender)


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.child}: {p.source} in {p.setting} ({p.twist})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
