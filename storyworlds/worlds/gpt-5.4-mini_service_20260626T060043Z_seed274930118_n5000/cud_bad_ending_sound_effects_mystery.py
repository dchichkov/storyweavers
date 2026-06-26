#!/usr/bin/env python3
"""
storyworlds/worlds/cud_bad_ending_sound_effects_mystery.py
==========================================================

A small mystery story world about a curious child, a strange patch of cud,
and noisy clues that do not quite lead to a happy ending.

Premise:
- Someone notices a muddy-looking clue near a quiet place.
- The clue makes a strange sound when touched.
- The child tries to solve the mystery with a helper.

Turn:
- The clues seem promising, but each one points to another false lead.
- Sound effects matter: creak, plop, drip, scritch.

Resolution:
- The mystery is "solved" in a bad-ending way: the real answer remains out of
  reach, the clue is lost, or the culprit gets away.
- The final image proves what changed: the child knows less than before, but
  the world feels a little stranger.

This world models small physical states (meters) and emotional states (memes)
with a few typed entities, then uses those facts to drive prose.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

SOUNDS = ["creak", "plop", "drip", "scritch", "clink", "thump", "whisper"]
PLACES = ["the shed", "the pond", "the attic", "the garden path", "the old well"]
CLUES = ["cud", "a muddy print", "a torn ribbon", "a wet note", "a tiny key"]
CULPRITS = ["a squirrel", "a fox", "a windy door", "a forgotten cart", "a hidden mouse"]
HELPERS = ["grandpa", "a sister", "a neighbor", "a friend", "the old cat"]
TRAITS = ["curious", "careful", "brave", "quiet", "eager"]
NAMES = ["Mina", "Noah", "Ivy", "Leo", "Tessa", "Nico", "June", "Owen"]


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "aunt"}
        male = {"boy", "man", "father", "grandpa", "uncle", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    quiet: bool = True
    mystery_tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    label: str
    phrase: str
    sound: str
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    clue: str
    culprit: str
    helper: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.ending_bad: bool = True

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
        clone = World(self.setting)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "caretaker": v.caretaker,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.ending_bad = self.ending_bad
        return clone


# ---------------------------------------------------------------------------
# Scenario registries
# ---------------------------------------------------------------------------
SETTINGS = {p.replace(" ", "_"): Setting(place=p, mystery_tags={"quiet", "clue"}) for p in PLACES}

CLUE_REGISTRY = {
    "cud": Clue(label="cud", phrase="a lump of cud", sound="plop", mess="muddy", tags={"mud", "gross", "clue"}),
    "muddy_print": Clue(label="print", phrase="a muddy print", sound="squelch", mess="muddy", tags={"footprint", "clue"}),
    "ribbon": Clue(label="ribbon", phrase="a torn ribbon", sound="scritch", mess="dry", tags={"cloth", "clue"}),
    "wet_note": Clue(label="note", phrase="a wet note", sound="drip", mess="wet", tags={"paper", "clue"}),
    "tiny_key": Clue(label="key", phrase="a tiny key", sound="clink", mess="dry", tags={"metal", "clue"}),
}

CULPRIT_REGISTRY = {
    "squirrel": "a squirrel with quick feet",
    "fox": "a fox with bright eyes",
    "windy_door": "a windy door that kept opening and closing",
    "cart": "a forgotten cart that creaked in the dark",
    "mouse": "a hidden mouse with a crumb trail",
}

HELPER_REGISTRY = {
    "grandpa": ("grandpa", "he"),
    "sister": ("sister", "she"),
    "neighbor": ("neighbor", "they"),
    "friend": ("friend", "they"),
    "old_cat": ("the old cat", "it"),
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
clue(C) :- clue_item(C).
place(P) :- setting(P).
suspect(S) :- culprit(S).
helper(H) :- helper_item(H).

interesting(P, C) :- setting(P), clue_item(C), clue_sound(C, _).
bad_ending(P, C, S) :- interesting(P, C), culprit(S), not solved(P, C, S).
could_have_solved(P, C, S) :- setting(P), clue_item(C), culprit(S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.quiet:
            lines.append(asp.fact("quiet", sid))
        for tag in sorted(s.mystery_tags):
            lines.append(asp.fact("tag", sid, tag))
    for cid, c in CLUE_REGISTRY.items():
        lines.append(asp.fact("clue_item", cid))
        lines.append(asp.fact("clue_sound", cid, c.sound))
        lines.append(asp.fact("clue_mess", cid, c.mess))
        for tag in sorted(c.tags):
            lines.append(asp.fact("clue_tag", cid, tag))
    for s in CULPRIT_REGISTRY:
        lines.append(asp.fact("culprit", s))
    for h in HELPER_REGISTRY:
        lines.append(asp.fact("helper_item", h))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Mechanics
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue == "cud" and args.culprit == "windy_door":
        pass
    place = args.place or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUE_REGISTRY))
    culprit = args.culprit or rng.choice(list(CULPRIT_REGISTRY))
    helper = args.helper or rng.choice(list(HELPER_REGISTRY))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)

    if clue == "cud" and culprit == "windy_door":
        # Too abstract; refuse only if explicitly pinned with no other anchors.
        if args.clue and args.culprit and args.place:
            raise StoryError("That pairing is too slippery for a concrete mystery.")
    return StoryParams(place=place, clue=clue, culprit=culprit, helper=helper, name=name, gender=gender, trait=trait)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery world with cud, sound effects, and a bad ending.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--clue", choices=list(CLUE_REGISTRY))
    ap.add_argument("--culprit", choices=list(CULPRIT_REGISTRY))
    ap.add_argument("--helper", choices=list(HELPER_REGISTRY))
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def _build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name, kind="character", type=params.gender,
        meters={"attention": 0.0}, memes={"curiosity": 1.0, "worry": 0.0, "doubt": 0.0}
    ))
    helper_type, _ = HELPER_REGISTRY[params.helper]
    helper = world.add(Entity(
        id="Helper", kind="character", type=helper_type, label=helper_type,
        meters={"attention": 0.0}, memes={"calm": 1.0}
    ))
    clue = CLUE_REGISTRY[params.clue]
    clue_ent = world.add(Entity(
        id="Clue", kind="thing", type=clue.label, label=clue.label, phrase=clue.phrase,
        owner=None, caretaker=None, meters={"mystery": 1.0, clue.mess: 1.0}
    ))
    culprit_label = CULPRIT_REGISTRY[params.culprit]

    # Act 1
    world.say(f"On a quiet evening, {hero.id} was {params.trait} and noticed {clue.phrase} near {setting.place}.")
    world.say(f"The thing gave a small {clue.sound}, like the clue was trying to say something.")
    world.say(f"{hero.id} leaned closer and whispered, 'What are you?'")
    hero.memes["curiosity"] += 1.0

    # Act 2
    world.para()
    world.say(f"{helper.id.capitalize()} came over and listened too. Together they heard another {clue.sound}, then a soft {random.choice(SOUNDS)} from the dark.")
    world.say(f"{helper.id.capitalize()} pointed at the {clue.label} and said it might lead to {culprit_label}.")
    hero.memes["worry"] += 1.0
    helper.memes["doubt"] = helper.memes.get("doubt", 0.0) + 1.0

    # Act 3: failed solve / bad ending
    world.para()
    if params.clue == "cud":
        world.say(f"When {hero.id} picked up the cud, it went plop and slipped into the mud before they could study it.")
    else:
        world.say(f"When {hero.id} reached for the clue, it answered with a tiny {clue.sound} and then vanished under the leaves.")
    world.say(f"They ran toward the noise, but the only answer was a {random.choice(['creak', 'drip', 'whisper'])} from somewhere else.")
    world.say(f"The trail ended at {culprit_label}, and then it was gone. {hero.id} knew the mystery was real, but not the truth.")
    world.ending_bad = True

    world.facts = {
        "hero": hero,
        "helper": helper,
        "clue": clue_ent,
        "clue_cfg": clue,
        "culprit": culprit_label,
        "setting": setting,
        "params": params,
    }
    return world


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# Story text helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    clue = world.facts["clue_cfg"]
    return [
        f"Write a short mystery story for young children that includes the word '{p.clue}' and a noisy clue.",
        f"Tell a gentle but unresolved mystery about {p.name} finding {clue.phrase} at {p.place}.",
        f"Write a child-facing story with sound effects like {clue.sound} and a disappointing ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    hero: Entity = f["hero"]
    clue: Clue = f["clue_cfg"]
    helper: Entity = f["helper"]
    qa = [
        QAItem(
            question=f"What did {p.name} find near {p.place}?",
            answer=f"{p.name} found {clue.phrase} near {p.place}, and it made a little {clue.sound} when they got close.",
        ),
        QAItem(
            question=f"Who helped {p.name} look at the clue?",
            answer=f"{helper.id.capitalize()} helped {p.name} listen and guess what the clue might mean.",
        ),
        QAItem(
            question=f"Did {p.name} solve the mystery?",
            answer=f"No. {p.name} followed the sounds, but the real answer slipped away before they could solve it.",
        ),
        QAItem(
            question=f"How did {p.name} feel when the clue disappeared?",
            answer=f"{p.name} felt worried and disappointed, because the mystery stayed unsolved.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue: Clue = f["clue_cfg"]
    out = [
        QAItem(
            question="What is cud?",
            answer="Cud is food that some animals chew, rest, and chew again. It can look like a soft lump.",
        ),
        QAItem(
            question="Why do mystery stories use sound effects?",
            answer="Sound effects help readers imagine what is happening and make clues feel more exciting.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that can help someone guess an answer or solve a mystery.",
        ),
    ]
    if clue.sound == "plop":
        out.append(QAItem(
            question="What sound does something make when it plops?",
            answer="A plop is a small, soft splash or drop sound, like something wet landing in mud or water.",
        ))
    return out


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
        lines.append(f"  {e.id:8} ({e.kind:7}/{e.type:10}) {' '.join(bits)}")
    lines.append(f"  bad ending: {world.ending_bad}")
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_valid_triples() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show interesting/2."))
    return sorted(set(asp.atoms(model, "interesting")))


def asp_verify() -> int:
    # Simple parity check: every registered clue should be representable.
    triples = asp_valid_triples()
    expected = {(p, c) for p in SETTINGS for c in CLUE_REGISTRY}
    actual = set(triples)
    if actual == expected:
        print(f"OK: ASP sees all {len(actual)} setting/clue combinations.")
        return 0
    print("MISMATCH between ASP and Python registries.")
    print("only in ASP:", sorted(actual - expected))
    print("only in Python:", sorted(expected - actual))
    return 1


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="the_shed", clue="cud", culprit="windy_door", helper="grandpa", name="Mina", gender="girl", trait="curious"),
    StoryParams(place="the_pond", clue="muddy_print", culprit="fox", helper="sister", name="Leo", gender="boy", trait="careful"),
    StoryParams(place="the_attic", clue="wet_note", culprit="mouse", helper="neighbor", name="Ivy", gender="girl", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show interesting/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_triples()
        print(f"{len(triples)} compatible setting/clue combinations:\n")
        for place, clue in triples[:50]:
            print(f"  {place:12} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
