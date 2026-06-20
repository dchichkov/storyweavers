#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/biblical_repulse_kindness_transformation_nursery_rhyme.py
========================================================================================

A small standalone storyworld for a nursery-rhyme-style tale about a child who
meets someone who first feels repulsive or off-putting, then responds with
kindness, and a soft transformation follows.

The world keeps the prose state-driven: a character has an emotional repulsion,
another acts with kindness, and the relationship changes into warmth and trust.
The story is written in a gentle rhyming cadence, with a biblical flavor in the
lesson and imagery, while remaining child-facing and concrete.

Required words included in the story and world vocabulary:
- biblical
- repulse

Features:
- Kindness
- Transformation
- Nursery rhyme style
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0}
        if not self.memes:
            self.memes = {"repulse": 0.0, "kindness": 0.0, "trust": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman"}
        masculine = {"boy", "father", "dad", "man"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



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
    rhyme_word: str

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
class Visitor:
    id: str
    label: str
    scent: str
    look: str
    shiver: str
    charm: str
    kind: str = "visitor"

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
class KindAct:
    id: str
    deed: str
    gentle_line: str
    touch: str
    result: str

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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_gender: str
    visitor: str
    kindness: str
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


SETTINGS = {
    "stable": Setting("stable", "the little stable", "warm straw and moonlight", "glow"),
    "garden": Setting("garden", "the cottage garden", "soft petals and dew", "bloom"),
    "lane": Setting("lane", "the old lane", "silver puddles and fence-posts", "shine"),
}

VISITORS = {
    "mucky_hedgehog": Visitor(
        "mucky_hedgehog",
        "a mucky hedgehog",
        "a damp mossy smell",
        "spiky bristles and muddy feet",
        "a little sniffle",
        "looked prickly and strange",
    ),
    "muddy_kitten": Visitor(
        "muddy_kitten",
        "a muddy kitten",
        "wet grass and milk",
        "a tiny face with whiskers",
        "a weary mew",
        "looked scruffed and small",
    ),
    "grumpy_lamb": Visitor(
        "grumpy_lamb",
        "a grumpy lamb",
        "rain and wool",
        "a woolly coat full of straw",
        "a baasome bleat",
        "looked fussy and forlorn",
    ),
}

KIND_ACTS = {
    "wash": KindAct("wash", "washed", "She sang a lullaby and washed the little paws clean.", "warm water", "the mud slid away"),
    "brush": KindAct("brush", "brushed", "He brushed the mess from the fur with gentle hands.", "a soft brush", "the fur grew neat"),
    "wrap": KindAct("wrap", "wrapped", "They wrapped the visitor in a tiny blanket like a gift.", "a clean blanket", "the shivers went away"),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Eli", "Theo", "Sam"]


def rhyme(setting: Setting, visitor: Visitor) -> str:
    return f"{setting.rhyme_word} and {visitor.charm}"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for v in VISITORS:
            for k in KIND_ACTS:
                combos.append((s, v, k))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for vid in VISITORS:
        lines.append(asp.fact("visitor", vid))
        lines.append(asp.fact("can_repulse", vid))
    for kid in KIND_ACTS:
        lines.append(asp.fact("kind_act", kid))
    return "\n".join(lines)


ASP_RULES = r"""
repulse(V) :- visitor(V), can_repulse(V).
transform(S, V, K) :- setting(S), visitor(V), kind_act(K), repulse(V).
valid(S, V, K) :- setting(S), visitor(V), kind_act(K), transform(S, V, K).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH: ASP and Python valid combo sets differ.")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in asp:", sorted(cl - py))
        return 1
    print(f"OK: ASP and Python agree on {len(py)} valid combos.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about repulse, kindness, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--kindness", choices=KIND_ACTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              and (args.visitor is None or c[1] == args.visitor)
              and (args.kindness is None or c[2] == args.kindness)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s, v, k = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(s, name, gender, v, k)


def _make_world(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    visitor = VISITORS[params.visitor]
    act = KIND_ACTS[params.kindness]

    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    other = world.add(Entity(id="visitor", kind="character", type="visitor", label=visitor.label, role="visitor"))
    place = world.add(Entity(id="place", kind="place", label=setting.place))
    world.facts.update(setting=setting, visitor=visitor, act=act, child=child, other=other, place=place)

    child.memes["repulse"] = 1.0
    child.memes["joy"] = 0.0
    other.memes["mess"] = 1.0

    world.say(
        f"In {setting.place}, by a little old gate, {child.id} met {visitor.label} at dusk so late."
    )
    world.say(
        f"{visitor.label.capitalize()} was {visitor.look}, with {visitor.scent}, and {visitor.shiver} in the air."
    )
    world.say(
        f"{child.id} stepped back at once and felt a little repulse, for the sight seemed odd and spare."
    )

    world.para()
    world.say(
        f"But {child.id} remembered a biblical line, so gentle and bright: to meet a small soul with kindness, and make the dark turn light."
    )
    child.memes["kindness"] += 1.0
    child.memes["repulse"] = 0.0
    other.memes["trust"] += 1.0
    other.memes["joy"] += 1.0
    world.say(
        f'So {child.id} knelt down softly and said, "{visitor.label.capitalize()}, come in from the cold tonight."'
    )
    world.say(f"{act.gentle_line}")
    world.say(f"Then {act.result}, and {visitor.label} stopped looking grim and fright.")

    world.para()
    child.memes["joy"] += 1.0
    other.memes["joy"] += 1.0
    other.memes["trust"] += 1.0
    world.say(
        f"{visitor.label.capitalize()} perked right up, and the old gloom slipped away like a shadow in moonlight."
    )
    world.say(
        f"By the end of the little rhyme, the same {visitor.label} that once would repulse now sparkled soft and kind."
    )

    world.facts["outcome"] = "transformed"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting: Setting = f["setting"]
    visitor: Visitor = f["visitor"]
    return [
        f'Write a nursery-rhyme story in {setting.place} that includes the words "biblical" and "repulse".',
        f"Tell a gentle rhyme where {visitor.label} first causes repulse, then kindness changes the mood.",
        f"Write a child-friendly story about kindness and transformation with a biblical lesson and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    visitor: Visitor = f["visitor"]
    setting: Setting = f["setting"]
    act: KindAct = f["act"]
    return [
        QAItem(
            question="What happened at the beginning of the story?",
            answer=f"{child.id} met {visitor.label} in {setting.place}, and {visitor.label} first made {child.id} feel repulse. The visitor looked odd and sorry, so the scene began with a little bit of worry.",
        ),
        QAItem(
            question="How did the child change the moment?",
            answer=f"{child.id} chose kindness instead of turning away. That gentle choice was the turning point, because it helped the visitor feel safe and welcome.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"By the end, {visitor.label} looked brighter and calmer, and the old sadness was gone. The story turned repulse into trust, which is the transformation the rhyme wanted to show.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kindness mean in this world?",
            answer="Kindness means speaking gently, helping someone who looks left out, and making room for them. In this storyworld, kindness can change fear into trust.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a new kind of feeling or state. Here, a gloomy meeting becomes a warm friendship by the end.",
        ),
        QAItem(
            question="What does biblical mean here?",
            answer="Biblical means the story carries a simple, wise lesson like the kind found in Bible stories. It points the reader toward mercy, care, and a good ending.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:10} {e.type:8} memes={dict(e.memes)} meters={dict(e.meters)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams("stable", "Mia", "girl", "mucky_hedgehog", "wash"),
    StoryParams("garden", "Theo", "boy", "muddy_kitten", "wrap"),
    StoryParams("lane", "Lily", "girl", "grumpy_lamb", "brush"),
]


def explain_rejection() -> str:
    return "(No story: this world always needs a visitor, a kindness, and a place to transform the feeling.)"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show repulse/1.\n#show transform/3.\n#show valid/3."))
        return
    if args.verify:
        rc = asp_verify()
        if rc == 0:
            try:
                sample = generate(CURATED[0])
                assert sample.story
                assert sample.world is not None
            except Exception as exc:  # pragma: no cover
                print(f"SMOKE TEST FAILED: {exc}")
                sys.exit(1)
            print("OK: story generation smoke test passed.")
        sys.exit(rc)
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, v, k in asp_valid_combos():
            print(f"  {s:8} {v:16} {k}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        if args.setting is None and args.visitor is None and args.kindness is None:
            pass
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.setting} / {p.visitor} / {p.kindness}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
