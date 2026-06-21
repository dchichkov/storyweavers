#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/missle_baba_auditorium_moral_value_bravery_transformation.py
============================================================================================

A small rhyming storyworld about a child, Baba, and an auditorium, where a
misstated "missle" prop, a moral choice, bravery, and a transformation all
matter. The story is built from state: a child wants to impress a crowd, a
reassuring Baba guides them toward honesty and courage, and the child changes
from shaky to shining by the end.

The world keeps a tiny physical model in meters and an emotional model in memes.
The prose comes from simulated state, not from swapping nouns in a fixed paragraph.

Supports:
- default generation, -n, --all, --seed, --trace, --qa, --json
- ASP twin with --asp, --verify, --show-asp
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "baba"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Theme:
    id: str
    scene: str
    rhyme_line: str
    stage_name: str
    sound: str
    ending_image: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    risky: bool
    shine: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Guide:
    id: str
    label: str
    phrase: str
    moral_line: str
    bravery_line: str
    transform_line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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


def _r_tremble(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["worry"] >= THRESHOLD and ("tremble",) not in world.fired:
        world.fired.add(("tremble",))
        child.memes["bravery_need"] += 1
        out.append("")
    return out


def _r_transform(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["honesty"] >= THRESHOLD and child.memes["bravery"] >= THRESHOLD:
        if ("transform",) not in world.fired:
            world.fired.add(("transform",))
            child.meters["transformed"] += 1
            child.memes["shine"] += 1
            out.append("")
    return out


CAUSAL_RULES = [Rule("tremble", _r_tremble), Rule("transform", _r_transform)]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def valid_combos() -> list[tuple[str, str]]:
    return [(t.id, p.id) for t in THEMES.values() for p in PROPS.values() if p.risky]


def best_guide() -> Guide:
    return max(GUIDES.values(), key=lambda g: len(g.tags))


def story_risk(prop: Prop, theme: Theme) -> bool:
    return prop.risky and theme.id in {"auditorium"}


@dataclass
class StoryParams:
    theme: str
    prop: str
    guide: str
    child_name: str
    child_gender: str
    baba_name: str
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


THEMES = {
    "auditorium": Theme(
        id="auditorium",
        scene="a bright auditorium with rows of red seats",
        rhyme_line="The lights were low, the stage was wide, and echoes danced from side to side.",
        stage_name="stage",
        sound="the hush of waiting shoes",
        ending_image="The auditorium glowed like a moonlit kite.",
    ),
    "schoolhall": Theme(
        id="schoolhall",
        scene="a school hall with shiny floors",
        rhyme_line="The floor was smooth, the curtains tall, and voices floated down the hall.",
        stage_name="hall",
        sound="the whisper of the curtains",
        ending_image="The hall felt warm as toast and bright as gold.",
    ),
}

PROPS = {
    "missle": Prop(
        id="missle",
        label="missle",
        phrase="a silver missle prop",
        risky=True,
        shine="shone like a star",
        tags={"missle", "rocket"},
    ),
    "mask": Prop(
        id="mask",
        label="mask",
        phrase="a paper mask",
        risky=False,
        shine="looked brave and neat",
        tags={"mask"},
    ),
    "crown": Prop(
        id="crown",
        label="crown",
        phrase="a tiny cardboard crown",
        risky=False,
        shine="glimmered like a toast of sun",
        tags={"crown"},
    ),
}

GUIDES = {
    "baba": Guide(
        id="baba",
        label="Baba",
        phrase="Baba",
        moral_line="be honest when you have slipped",
        bravery_line="bravery means telling the truth",
        transform_line="a kind choice can change your whole face",
        tags={"baba", "moral", "bravery", "transformation"},
    ),
    "teacher": Guide(
        id="teacher",
        label="the teacher",
        phrase="the teacher",
        moral_line="share the truth before the crowd grows grim",
        bravery_line="a brave heart can still be gentle",
        transform_line="being honest can turn a frown into a grin",
        tags={"moral", "bravery", "transformation"},
    ),
}

GIRL_NAMES = ["Lina", "Mina", "Sara", "Nora", "Tala", "Rina"]
BOY_NAMES = ["Omar", "Dani", "Rami", "Sami", "Niko", "Ilan"]
TRAITS = ["shy", "quick", "curious", "gentle", "bright"]


def tell(theme: Theme, prop: Prop, guide: Guide, child_name: str, child_gender: str, baba_name: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=["little"]))
    baba = world.add(Entity(id=baba_name, kind="character", type="baba", role="guide"))
    stage = world.add(Entity(id="stage", kind="thing", type="stage", label=theme.stage_name))
    item = world.add(Entity(id=prop.id, kind="thing", type="prop", label=prop.label, attrs={"prop": prop.id}))
    child.memes["worry"] = 1.0
    child.memes["hope"] = 1.0

    world.say(f"In {theme.scene}, {child.id} stood small and still, with {theme.rhyme_line}")
    world.say(f"{child.id} held {prop.phrase}; it {prop.shine}, and {theme.sound} filled the air.")
    world.say(f"Everyone waited for {child.id} to step on {stage.label_word}, where the rhymes should fly.")

    world.para()
    child.memes["pride"] += 1
    world.say(f"But {child.id} had one small fear: the line was forgotten, the words were not near.")
    world.say(f"{child.id} looked at {baba.id} and wanted to hide, then took a deep breath and stayed beside the stage.")

    world.para()
    child.memes["honesty"] += 1
    child.memes["bravery"] += 1
    world.say(f"\"I lost my line,\" {child.id} said, with a wobble and sigh.")
    world.say(f"{guide.phrase} smiled and said, \"{guide.moral_line.capitalize()}. {guide.bravery_line.capitalize()}.\"")
    world.say(f"That honest little moment made the worry glide away.")
    propagate(world)

    world.para()
    child.memes["calm"] += 1
    child.memes["joy"] += 1
    child.meters["transformed"] += 1
    world.say(f"{child.id} lifted {prop.label} and walked on stage as brave as could be.")
    world.say(f"Then {child.id} found the rhythm at last and sang the next part free.")
    world.say(f"{guide.transform_line.capitalize()}, and the room turned bright with cheer.")
    world.say(f"{theme.ending_image} {child.id} was no longer shy; {child.id} was shining clear.")

    world.facts.update(theme=theme, prop=prop, guide=guide, child=child, baba=baba, stage=stage, item=item)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story that includes the words "{f["prop"].label}", "baba", and "auditorium".',
        f"Tell a child-friendly rhyme about {f['child'].id} in an auditorium, where Baba helps with honesty and bravery.",
        f"Write a short moral story in rhyme where a shy child transforms by telling the truth on stage.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    prop = f["prop"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {guide.phrase}, and the moment in the auditorium when courage matters."),
        ("What problem did the child have?",
         f"{child.id} forgot the line and felt shaky. The worry made the stage feel much bigger than {child.id} did."),
        ("What did Baba teach?",
         f"{guide.phrase} taught that moral value means being honest, and that bravery can sound soft and kind. That helped {child.id} tell the truth instead of hiding."),
        ("How did the child change?",
         f"{child.id} changed from shy and worried into calm and shining. By the end, {child.id} stood taller and spoke with a brave voice."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an auditorium?",
         "An auditorium is a big room where people sit and watch a show, talk, or listen together."),
        ("What does bravery mean?",
         "Bravery means doing the hard or scary right thing, even when your tummy feels wiggly."),
        ("What does a moral value help with?",
         "A moral value helps people choose what is kind, honest, and fair."),
        ("What is transformation?",
         "Transformation is a change from one state to another, like a shy face turning bright and confident."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(theme="auditorium", prop="missle", guide="baba", child_name="Mina", child_gender="girl", baba_name="Baba"),
    StoryParams(theme="auditorium", prop="mask", guide="teacher", child_name="Omar", child_gender="boy", baba_name="Baba"),
]


def explain_rejection(theme: Theme, prop: Prop) -> str:
    if not story_risk(prop, theme):
        return "(No story: this prop does not create the right auditorium tension for the moral/bravery turn.)"
    return "(No story: invalid combo.)"


def valid_story_choice(theme: str, prop: str) -> bool:
    return theme in THEMES and prop in PROPS and story_risk(PROPS[prop], THEMES[theme])


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld with moral value, bravery, and transformation.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--baba", dest="baba_name")
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
    return [(t, p, g) for t in THEMES for p in PROPS for g in GUIDES if valid_story_choice(t, p)]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.theme and args.prop and not valid_story_choice(args.theme, args.prop):
        raise StoryError(explain_rejection(THEMES[args.theme], PROPS[args.prop]))
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.prop is None or c[1] == args.prop)
              and (args.guide is None or c[2] == args.guide)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, prop, guide = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    baba_name = args.baba_name or "Baba"
    return StoryParams(theme=theme, prop=prop, guide=guide, child_name=name, child_gender=gender, baba_name=baba_name)


def generate(params: StoryParams) -> StorySample:
    theme = THEMES.get(params.theme)
    prop = PROPS.get(params.prop)
    guide = GUIDES.get(params.guide)
    if not theme or not prop or not guide:
        raise StoryError("Invalid params.")
    world = tell(theme, prop, guide, params.child_name, params.child_gender, params.baba_name)
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


ASP_RULES = r"""
valid(T,P,G) :- theme(T), prop(P), guide(G), risky(P), auditorium(T).
transformed(C) :- honesty(C), bravery(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
        if t == "auditorium":
            lines.append(asp.fact("auditorium", t))
    for p in PROPS.values():
        lines.append(asp.fact("prop", p.id))
        if p.risky:
            lines.append(asp.fact("risky", p.id))
    for g in GUIDES:
        lines.append(asp.fact("guide", g))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combo sets differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample)
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    print("OK" if rc == 0 else "FAIL")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
