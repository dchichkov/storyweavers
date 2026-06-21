#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/nightie_carpet_peck_dialogue_transformation_curiosity_rhyming.py
=================================================================================================

A standalone story world for a tiny rhyming tale: a curious child in a nightie,
a carpet with a peck-like discovery, a small transformation, and dialogue that
moves the story from wondering to changing.

The domain is deliberately small and state-driven:
- an animal or toy may peck at something on the carpet
- the child is curious and asks questions in dialogue
- a gentle transformation happens because of what they learn
- the ending image proves the change

The prose aims for a rhythmic, rhyming storybook feel without becoming a frozen
template. State determines what is seen, asked, and changed.

Supports:
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- Python reasonableness gate and inline ASP twin
- three Q&A sets grounded in world state
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    type: str = "thing"
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))


@dataclass
class Character:
    id: str
    type: str
    role: str
    label: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Scene:
    room: str
    light: str
    mood: str
    rhyme: str
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    carpet: str
    pecker: str
    transformation: str
    curiosity_level: str
    dialogue_style: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


SETTINGS = {
    "nursery": Scene(room="nursery", light="soft moonlight", mood="cozy", rhyme="glow"),
    "bedroom": Scene(room="bedroom", light="lamp-light", mood="snug", rhyme="moon"),
    "attic": Scene(room="attic", light="silver starlight", mood="quiet", rhyme="room"),
}

CARPETS = {
    "rose": Thing(id="rose", label="rose carpet", phrase="a rose-stitched carpet", tags={"carpet"}),
    "blue": Thing(id="blue", label="blue carpet", phrase="a blue wool carpet", tags={"carpet"}),
    "striped": Thing(id="striped", label="striped carpet", phrase="a striped hallway carpet", tags={"carpet"}),
}

PECKERS = {
    "sparrow": Thing(id="sparrow", label="sparrow", phrase="a curious sparrow", tags={"peck"}),
    "toybird": Thing(id="toybird", label="toy bird", phrase="a clockwork toy bird", tags={"peck"}),
    "beak": Thing(id="beak", label="wooden beak toy", phrase="a wooden beak toy", tags={"peck"}),
}

TRANSFORMS = {
    "sparkle": Thing(id="sparkle", label="sparkly patch", phrase="a sparkly patch", tags={"transform"}),
    "patch": Thing(id="patch", label="patch", phrase="a neat patch", tags={"transform"}),
    "flower": Thing(id="flower", label="flower motif", phrase="a flower motif", tags={"transform"}),
}

QUESTIONS = {
    "curiosity": [
        ("What makes the child curious?",
         "The child notices something odd on the carpet and wants to know what it means. Curiosity turns the tiny moment into a bigger change."),
    ],
    "dialogue": [
        ("Why is there so much talking in the story?",
         "The story uses dialogue so the child can ask, answer, and choose what to do next. That back-and-forth helps the change happen kindly."),
    ],
    "transformation": [
        ("What is transformation in this story?",
         "Transformation means something small becomes something new and nicer. Here, what was plain or puzzling turns into a bright little feature on the carpet."),
    ],
    "carpet": [
        ("What is a carpet?",
         "A carpet is a soft floor covering you can walk or sit on. It can also hold a tiny mark or change that people notice."),
    ],
    "peck": [
        ("What does peck mean?",
         "To peck is to tap quickly with a beak or a small pointed part. In this story, that little peck starts the wonder."),
    ],
    "nightie": [
        ("What is a nightie?",
         "A nightie is a soft bedtime dress or shirt for sleeping. It feels cozy and helps set the sleepy mood."),
    ],
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for carpet in CARPETS:
            for pecker in PECKERS:
                for transform in TRANSFORMS:
                    combos.append((setting, carpet, pecker, transform))
    return combos


def narrate_rhyme(nightie: str, carpet: str, pecker: str, transform: str, scene: Scene,
                  child: Character, helper: Character, world: World) -> None:
    child.memes["curious"] += 1
    world.say(
        f"In {scene.room}, by {scene.light} so bright, {child.id} in a {nightie} felt snug and light."
    )
    world.say(
        f"On the {carpet}, a {pecker} gave a peck-peck tap, and {child.id} leaned near for a tiny clue-map."
    )
    world.say(
        f'"Why peck the carpet?" asked {child.id}. "Why now?" '
        f'"Because curious hearts like mine ask how," said {helper.id}, with a smile and a bow.'
    )
    world.say(
        f'"Could it change?" asked {child.id}. "Could it grow?" '
        f'"Yes," said {helper.id}, "let's watch it show."'
    )
    world.say(
        f"The peck made a small sign, then a neat little trace; "
        f"the {transform} took shape in its tiny soft place."
    )


def apply_transformation(world: World, carpet: Thing, transform: Thing, child: Character) -> None:
    sig = ("transform", carpet.id, transform.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    carpet.meters["changed"] += 1
    carpet.meters["beauty"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"The carpet did not stay the same by the door; it shimmered and shined with {transform.label} and more."
    )
    world.say(
        f"{child.id} grinned, \"Oh wow!\" and stepped back with glee; "
        f"what once was a question had become something to see."
    )


def ending(world: World, child: Character, helper: Character, carpet: Thing, transform: Thing) -> None:
    child.memes["joy"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"Now {child.id} in {child.pronoun('possessive')} nightie could tiptoe and glow, "
        f"while the carpet wore {transform.label} like a soft little show."
    )
    world.say(
        f'"Good night," said {helper.id}. "Good night," said {child.id}. '
        f"And curiosity sparkled where sleepy feet slid."
    )


def tell(params: StoryParams) -> World:
    scene = SETTINGS[params.setting]
    carpet_cfg = CARPETS[params.carpet]
    pecker_cfg = PECKERS[params.pecker]
    transform_cfg = TRANSFORMS[params.transformation]

    world = World()
    child = world.add(Character(
        id=params.child_name, type=params.child_type, role="child", label="the child",
        traits=["curious", params.curiosity_level]
    ))
    helper = world.add(Character(
        id=params.helper_name, type=params.helper_type, role="helper", label="the helper",
        traits=["gentle", "watchful"]
    ))
    carpet = world.add(Thing(
        id="carpet", label=carpet_cfg.label, phrase=carpet_cfg.phrase, tags=set(carpet_cfg.tags)
    ))
    pecker = world.add(Thing(
        id="pecker", label=pecker_cfg.label, phrase=pecker_cfg.phrase, tags=set(pecker_cfg.tags)
    ))
    transform = world.add(Thing(
        id="transform", label=transform_cfg.label, phrase=transform_cfg.phrase, tags=set(transform_cfg.tags)
    ))

    narrate_rhyme("nightie", carpet.label, pecker.label, transform.label, scene, child, helper, world)
    world.para()
    apply_transformation(world, carpet, transform, child)
    world.para()
    ending(world, child, helper, carpet, transform)

    world.facts.update(
        scene=scene, child=child, helper=helper, carpet=carpet, pecker=pecker,
        transform=transform, params=params
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a rhyming bedtime story that includes the words "nightie", "carpet", and "peck".',
        f"Tell a gentle story with dialogue where {p.child_name} is curious about a peck on the carpet and something transforms.",
        f"Write a cozy rhyming story set in a {p.setting} with a nightie, a carpet, curiosity, and a kind ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Character = f["child"]
    helper: Character = f["helper"]
    carpet: Thing = f["carpet"]
    pecker: Thing = f["pecker"]
    transform: Thing = f["transform"]
    scene: Scene = f["scene"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id} in the {scene.room}. The child is the one who notices the peck and asks questions."),
        ("What did the child ask about?",
         f"{child.id} asked about the peck on the {carpet.label}. The questions led to a small transformation and a calmer ending."),
        ("What changed in the story?",
         f"The {carpet.label} became marked with {transform.label}. The change happened because curiosity and dialogue helped the child understand what was happening."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    tags = set()
    for ent in list(world.entities.values()):
        if hasattr(ent, "tags"):
            tags |= set(ent.tags)
    if "carpet" in tags:
        out.extend(QUESTIONS["carpet"])
    if "peck" in tags:
        out.extend(QUESTIONS["peck"])
    out.extend(QUESTIONS["nightie"])
    out.extend(QUESTIONS["curiosity"])
    out.extend(QUESTIONS["dialogue"])
    out.extend(QUESTIONS["transformation"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in getattr(e, "meters", {}).items() if v}
        memes = {k: v for k, v in getattr(e, "memes", {}).items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if hasattr(e, "traits") and e.traits:
            bits.append(f"traits={e.traits}")
        if hasattr(e, "tags") and e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({getattr(e, 'type', 'thing'):7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this tiny world always keeps a carpet, a peck, curiosity, dialogue, and a transformation together.)"


ASP_RULES = r"""
changed(C,T) :- carpet(C), transform(T).
curious_story(C) :- child(C), curiosity(Cur), Cur = curious.
dialogue_story :- child(_), helper(_), said(_,_).
valid(S, C, P, T) :- setting(S), carpet(C), pecker(P), transform(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CARPETS:
        lines.append(asp.fact("carpet", c))
    for p in PECKERS:
        lines.append(asp.fact("pecker", p))
    for t in TRANSFORMS:
        lines.append(asp.fact("transform", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations.")
        print("python only:", sorted(py - cl))
        print("asp only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), _random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny rhyming story world: nightie, carpet, peck, curiosity, dialogue, transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--carpet", choices=CARPETS)
    ap.add_argument("--pecker", choices=PECKERS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father", "girl", "boy"])
    ap.add_argument("--curiosity-level", choices=["quiet", "bright", "eager"])
    ap.add_argument("--dialogue-style", choices=["gentle", "rhyming", "playful"])
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


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Rose"]
BOY_NAMES = ["Theo", "Finn", "Max", "Noah", "Eli", "Sam"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    carpet = args.carpet or rng.choice(list(CARPETS))
    pecker = args.pecker or rng.choice(list(PECKERS))
    transform = args.transform or rng.choice(list(TRANSFORMS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["mother", "father", "girl", "boy"])
    helper_name = args.helper_name or rng.choice(GIRL_NAMES if helper_type in {"girl", "mother"} else BOY_NAMES)
    curiosity_level = args.curiosity_level or rng.choice(["quiet", "bright", "eager"])
    dialogue_style = args.dialogue_style or "rhyming"
    return StoryParams(
        setting=setting,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
        carpet=carpet,
        pecker=pecker,
        transformation=transform,
        curiosity_level=curiosity_level,
        dialogue_style=dialogue_style,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.carpet not in CARPETS or params.pecker not in PECKERS or params.transformation not in TRANSFORMS:
        raise StoryError("Unknown story element.")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print(" ", row)
        return

    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="nursery", child_name="Lily", child_type="girl", helper_name="Mom", helper_type="mother",
                        carpet="rose", pecker="sparrow", transformation="flower", curiosity_level="eager", dialogue_style="rhyming"),
            StoryParams(setting="bedroom", child_name="Noah", child_type="boy", helper_name="Dad", helper_type="father",
                        carpet="blue", pecker="toybird", transformation="sparkle", curiosity_level="bright", dialogue_style="gentle"),
            StoryParams(setting="attic", child_name="Mia", child_type="girl", helper_name="Auntie", helper_type="mother",
                        carpet="striped", pecker="beak", transformation="patch", curiosity_level="quiet", dialogue_style="playful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(rng_base + i))
            i += 1
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
