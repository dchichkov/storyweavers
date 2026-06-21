#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/oppress_reconciliation_rhyming_story.py
======================================================================

A small standalone storyworld for a rhyming TinyStories-style tale about
pressure, unfairness, apology, and reconciliation.

Premise:
- Two children prepare a tiny rhyme show.
- One child becomes bossy and tries to oppress the other's turn.
- A wise helper sees the hurt, helps them speak honestly, and guides them
  toward reconciliation.
- The ending proves the change with shared verses and a warm, bright finish.

The story keeps a light rhyming style and includes the seed word "oppress".
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Scene:
    id: str
    place: str
    rhyme: str
    props: str
    helper_line: str
    ending: str
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
class Pressure:
    id: str
    label: str
    push_line: str
    hurt_line: str
    apology_line: str
    tag: str = "pressure"
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
class Resolution:
    id: str
    sense: int
    power: int
    act_line: str
    fail_line: str
    end_line: str
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


def _r_hurt(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["pressured"] < THRESHOLD:
            continue
        sig = ("hurt", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["hurt"] += 1
        e.memes["sad"] += 1
        out.append("__hurt__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("apology") and world.facts.get("listening"):
        for e in list(world.entities.values()):
            if e.role in {"child_a", "child_b"}:
                e.memes["warmth"] += 1
                e.memes["hurt"] = max(0.0, e.memes["hurt"] - 1.0)
        sig = ("reconcile",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("hurt", "social", _r_hurt), Rule("reconcile", "social", _r_reconcile)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def pressure_is_unfair(pressure: Pressure) -> bool:
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sc in SCENES:
        for pr in PRESSURES:
            for rs in RESOLUTIONS:
                if pr.label and rs.sense >= 2:
                    combos.append((sc.id, pr.id, rs.id))
    return combos


@dataclass
class StoryParams:
    scene: str
    pressure: str
    resolution: str
    child_a: str
    child_a_gender: str
    child_b: str
    child_b_gender: str
    helper: str
    helper_gender: str
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


def rhyme_end(text: str) -> str:
    return text


def tell(scene: Scene, pressure: Pressure, resolution: Resolution,
         child_a: str = "Mia", child_a_gender: str = "girl",
         child_b: str = "Noah", child_b_gender: str = "boy",
         helper: str = "Grandma", helper_gender: str = "woman") -> World:
    world = World()
    a = world.add(Entity(id=child_a, kind="character", type=child_a_gender, role="child_a"))
    b = world.add(Entity(id=child_b, kind="character", type=child_b_gender, role="child_b"))
    h = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper", label="the helper"))

    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(f"In {scene.place}, under a sunlit glaze, {a.id} and {b.id} began their rhyme-day daze.")
    world.say(f"They stacked up props and paper bright; {scene.props} made the room feel light.")
    world.say(f'"Let’s share the stage," {a.id} sang with cheer, "and make our little show appear!"')
    world.say(f'But then {b.id} grew bossy and stern, and tried to make {a.id} wait and learn.')
    world.say(f"{pressure.push_line} The mean command could oppress the song, and make a sweet duet feel wrong.")

    world.para()
    a.memes["hurt"] += 1
    b.meters["pressured"] += 1
    world.facts["apology"] = False
    world.facts["listening"] = False
    if pressure_is_unfair(pressure):
        world.say(f"{a.id} frowned and said, “That feels not fair.” The room grew quiet in the air.")
    world.say(f"{scene.helper_line}")
    world.say(f'"{pressure.hurt_line}" {h.id} said, "and hurt words bruise. Let’s pause, breathe deep, and kindly choose."')

    world.para()
    world.facts["listening"] = True
    world.say(f"{h.id} asked them both to take a turn, to speak with care and truly learn.")
    world.say(f"{a.id} said, “I felt small.” {b.id} said, “I know. I was too loud. I let it grow.”")
    world.facts["apology"] = True
    b.memes["remorse"] += 1
    a.memes["hurt"] = 0.0
    b.meters["pressured"] = 0.0
    propagate(world, narrate=False)
    world.say(f'"I’m sorry," {b.id} said, with eyes grown mild. "I tried to oppress my sister/brother child."')
    world.say(f"{pressure.apology_line} {h.id} smiled, and nodded true, because kind apologies make hearts feel new.")

    world.para()
    if resolution.power >= 2:
        a.memes["warmth"] += 1
        b.memes["warmth"] += 1
        world.say(f"{resolution.act_line} Soon {a.id} and {b.id} stood side by side, with one shared beat and one shared pride.")
        world.say(f"{scene.ending} {resolution.end_line}")
    else:
        world.say(f"{resolution.fail_line}")
        world.say("So the song stayed shaky, soft, and thin, until they tried again and let peace in.")

    world.facts.update(scene=scene, pressure=pressure, resolution=resolution,
                       child_a=a, child_b=b, helper=h, outcome="reconciled")
    return world


SCENES = {
    "playroom": Scene(
        id="playroom",
        place="the playroom",
        rhyme="playtime",
        props="a drum, two bells, and a silver cape",
        helper_line="An old lamp glowed low and sweet, like a tiny moon beside their feet.",
        ending="Their duet rose up, warm and bright, like ribboned stars at end of night.",
    ),
    "garden": Scene(
        id="garden",
        place="the garden",
        rhyme="songtime",
        props="a cardboard crown, a note-book, and a painted kite",
        helper_line="A bird on the fence gave a gentle peep, as if it, too, had words to keep.",
        ending="Their rhymes flew out like bees in spring, and everyone could hear them sing.",
    ),
}

PRESSURES = {
    "hogging": Pressure(
        id="hogging",
        label="hogging",
        push_line="He pointed and patted the drum like a king, saying, “My turn first — let me own the thing!”",
        hurt_line="No one should be pushed or boxed or stuck; a friend’s soft voice needs space and luck.",
        apology_line="With room for both, the tune could mend.",
    ),
    "bossy_words": Pressure(
        id="bossy_words",
        label="bossy words",
        push_line="She folded her arms and made the rules tight, saying, “Listen to me — I know best tonight!”",
        hurt_line="Sharp words can press a heart like stone; they make a shared song feel all alone.",
        apology_line="They promised to speak in kinder tones.",
    ),
}

RESOLUTIONS = {
    "apology": Resolution(
        id="apology",
        sense=3,
        power=3,
        act_line="They traded lines, then laughed and swayed.",
        fail_line="The helper's words were sweet, but not enough; the air stayed prickly, stiff, and rough.",
        end_line="From then on, they took turns, one by one, and every shared verse felt like sun.",
    ),
    "shared_chorus": Resolution(
        id="shared_chorus",
        sense=4,
        power=4,
        act_line="They made a chorus, clear and true, where every line belonged to two.",
        fail_line="The plan was almost there, but one more breath was needed before the song could feel just right.",
        end_line="Together they sang a round, and found that sharing made the music sound.",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld about unfair pressure and reconciliation.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--pressure", choices=PRESSURES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--child-a")
    ap.add_argument("--child-a-gender", choices=["girl", "boy", "woman", "man"], default="girl")
    ap.add_argument("--child-b")
    ap.add_argument("--child-b-gender", choices=["girl", "boy", "woman", "man"], default="boy")
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man", "girl", "boy"], default="woman")
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
    if args.scene and args.scene not in SCENES:
        raise StoryError("Unknown scene.")
    if args.pressure and args.pressure not in PRESSURES:
        raise StoryError("Unknown pressure.")
    if args.resolution and args.resolution not in RESOLUTIONS:
        raise StoryError("Unknown resolution.")
    scenes = list(SCENES)
    pressures = list(PRESSURES)
    resolutions = [rid for rid, r in RESOLUTIONS.items() if r.sense >= 2]
    scene = args.scene or rng.choice(scenes)
    pressure = args.pressure or rng.choice(pressures)
    resolution = args.resolution or rng.choice(resolutions)
    a = args.child_a or rng.choice(["Mia", "Lena", "Tia", "Ivy"])
    b = args.child_b or rng.choice(["Noah", "Owen", "Ben", "Eli"])
    helper = args.helper or rng.choice(["Grandma", "Aunt May", "Uncle Jo"])
    return StoryParams(
        scene=scene, pressure=pressure, resolution=resolution,
        child_a=a, child_a_gender=args.child_a_gender,
        child_b=b, child_b_gender=args.child_b_gender,
        helper=helper, helper_gender=args.helper_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sc = f["scene"].id
    pr = f["pressure"].id
    return [
        f"Write a rhyming story about children in a {sc} who face {pr} and then reconcile.",
        f"Tell a child-friendly rhyming tale that uses the word oppress and ends in forgiveness.",
        "Create a short rhyme-story where a bossy moment turns into an apology and shared singing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, h = f["child_a"], f["child_b"], f["helper"]
    items = [
        QAItem(
            question="What problem started the story?",
            answer=f"{b.id} became bossy and tried to oppress {a.id}'s turn. That made the song feel tight instead of shared."
        ),
        QAItem(
            question="Who helped fix the problem?",
            answer=f"{h.id} helped by asking them to pause, listen, and speak kindly. That gave both children room to tell the truth."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with reconciliation. The children apologized, took turns, and sang together again in a warmer way."
        ),
    ]
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an apology?",
            answer="An apology is when someone says they are sorry for hurting or upsetting another person. It is a way to begin making things right again."
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people who were upset make peace and come back together kindly. They may forgive, share, and start fresh."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"  {e.id} ({e.role}) meters={meters} memes={memes}")
    return "\n".join(out)


CURATED = [
    StoryParams(scene="playroom", pressure="hogging", resolution="apology",
                child_a="Mia", child_a_gender="girl", child_b="Noah", child_b_gender="boy",
                helper="Grandma", helper_gender="woman"),
    StoryParams(scene="garden", pressure="bossy_words", resolution="shared_chorus",
                child_a="Lina", child_a_gender="girl", child_b="Eli", child_b_gender="boy",
                helper="Aunt May", helper_gender="woman"),
]


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.pressure not in PRESSURES or params.resolution not in RESOLUTIONS:
        raise StoryError("Invalid params.")
    world = tell(SCENES[params.scene], PRESSURES[params.pressure], RESOLUTIONS[params.resolution],
                 child_a=params.child_a, child_a_gender=params.child_a_gender,
                 child_b=params.child_b, child_b_gender=params.child_b_gender,
                 helper=params.helper, helper_gender=params.helper_gender)
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for pid in PRESSURES:
        lines.append(asp.fact("pressure", pid))
    for rid, r in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,R) :- scene(S), pressure(P), resolution(R), sense(R, N), N >= 2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
