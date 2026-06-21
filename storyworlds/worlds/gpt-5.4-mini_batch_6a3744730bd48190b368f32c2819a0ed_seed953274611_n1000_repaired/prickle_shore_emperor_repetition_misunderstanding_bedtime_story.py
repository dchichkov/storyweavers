#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/prickle_shore_emperor_repetition_misunderstanding_bedtime_story.py
===================================================================================================

A tiny bedtime storyworld about a child by the shore, a prickly little object,
and a kind emperor who helps clear up a misunderstanding. The model is small
but stateful: the story is driven by simulated meters and memes, not by a fixed
paragraph with swapped nouns.

Seed words: prickle, shore, emperor
Features: repetition, misunderstanding
Style: bedtime story
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "emperor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"emperor": "emperor"}.get(self.type, self.type)
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
class Shore:
    id: str
    name: str
    water: str
    sky: str
    hush: str
    tag: str = "shore"
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
class Prickle:
    id: str
    name: str
    phrase: str
    tiny_reason: str
    harmless: bool = False
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
class Misunderstanding:
    id: str
    repeated_line: str
    mistaken_name: str
    truth_line: str
    fix_line: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class StoryParams:
    shore: str
    prickle: str
    misunderstanding: str
    child: str
    child_type: str
    emperor_name: str
    emperor_type: str
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
        clone.facts = copy.deepcopy(self.facts)
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


def _r_prickle(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    obj = world.get("prickle")
    if child.meters["mistrust"] >= THRESHOLD and obj.meters["noticed"] >= THRESHOLD:
        sig = ("prickle",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["unease"] += 1
            out.append("__prickle__")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    emperor = world.get("emperor")
    if child.memes["unease"] >= THRESHOLD and emperor.memes["kindness"] >= THRESHOLD:
        sig = ("misunderstanding",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["confusion"] += 1
            emperor.memes["gentleness"] += 1
            out.append("__misunderstanding__")
    return out


CAUSAL_RULES = [Rule("prickle", "social", _r_prickle), Rule("misunderstanding", "social", _r_misunderstanding)]


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


def predict_misunderstanding(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["mistrust"] += 1
    propagate(sim, narrate=False)
    return {
        "uneasy": sim.get("child").memes["unease"] >= THRESHOLD,
        "confused": sim.get("child").memes["confusion"] >= THRESHOLD,
    }


def tell_setup(world: World, child: Entity, emperor: Entity, shore: Shore, prickle: Prickle) -> None:
    child.memes["sleepiness"] += 1
    emperor.memes["kindness"] += 1
    world.say(
        f"At the {shore.name}, where {shore.water} lapped softly and the {shore.sky} "
        f"rested like a blanket, {child.id} wandered close with sleepy feet."
    )
    world.say(
        f"Near a shell pile, {child.id} found {prickle.phrase}. "
        f"It looked small, but it gave a little prickle when touched."
    )


def repeat_question(world: World, child: Entity, prickle: Prickle, misunderstanding: Misunderstanding) -> None:
    child.meters["mistrust"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f'"What is it?" {child.id} asked. "What is it?" {child.id} asked again, '
        f"because the little thing felt strange."
    )
    world.say(
        f'{child.id} pointed and whispered, "{misunderstanding.repeated_line}" '
        f'then, a moment later, "{misunderstanding.repeated_line}"'
    )


def warn_emperor(world: World, emperor: Entity, child: Entity, prickle: Prickle, misunderstanding: Misunderstanding) -> None:
    pred = predict_misunderstanding(world)
    emperor.memes["kindness"] += 1
    emperor.memes["attention"] += 1
    if pred["uneasy"]:
        world.say(
            f'The {emperor.label_word} heard the little voice and knelt down. '
            f'"You mean {prickle.name}," {emperor.id} said softly, "not '
            f'{misunderstanding.mistaken_name}."'
        )
    else:
        world.say(
            f'The {emperor.label_word} smiled and listened closely. '
            f'"Let me look," {emperor.id} said, "and we will name it properly."'
        )


def clarify(world: World, emperor: Entity, child: Entity, prickle: Prickle, misunderstanding: Misunderstanding) -> None:
    child.memes["unease"] += 1
    world.say(
        f'"{misunderstanding.truth_line}" {emperor.id} said. '
        f'"It is only {prickle.phrase}, and the prickle is just its little way '
        f"of saying hello.""
    )
    world.say(
        f'{child.id} blinked, then laughed. "{misunderstanding.fix_line}" '
        f'{child.id} said, repeating the new truth once, then again.'
    )


def comfort_end(world: World, emperor: Entity, child: Entity, shore: Shore, prickle: Prickle) -> None:
    child.memes["relief"] += 1
    child.memes["sleepiness"] += 1
    world.say(
        f"The {emperor.label_word} brushed the sand from {child.id}'s hands and "
        f"showed how to leave the little {prickle.name} where it was."
    )
    world.say(
        f"Then the two of them watched the {shore.name} turn silver under the sky, "
        f"and everything felt quiet and safe."
    )
    world.say(
        f'{child.id} yawned a tiny yawn and held still, listening to the hush of the waves.'
    )


def tell(shore: Shore, prickle: Prickle, misunderstanding: Misunderstanding,
         child_name: str = "Mina", child_type: str = "girl",
         emperor_name: str = "Emperor Kai", emperor_type: str = "emperor") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    emperor = world.add(Entity(id=emperor_name, kind="character", type=emperor_type, role="helper"))
    shore_ent = world.add(Entity(id="shore", kind="place", type="place", label=shore.name))
    prick = world.add(Entity(id="prickle", kind="thing", type="thing", label=prickle.name))
    world.facts["shore"] = shore
    world.facts["prickle"] = prickle
    world.facts["misunderstanding"] = misunderstanding

    tell_setup(world, child, emperor, shore, prickle)
    world.para()
    repeat_question(world, child, prickle, misunderstanding)
    warn_emperor(world, emperor, child, prickle, misunderstanding)
    world.para()
    clarify(world, emperor, child, prickle, misunderstanding)
    propagate(world, narrate=False)
    comfort_end(world, emperor, child, shore, prickle)

    world.facts.update(
        child=child,
        emperor=emperor,
        shore_ent=shore_ent,
        prickle_ent=prick,
        repeated=child.meters["mistrust"] >= THRESHOLD,
        resolved=True,
    )
    return world


SHORES = {
    "calm": Shore(id="calm", name="the quiet shore", water="small waves", sky="blue evening sky", hush="soft hush"),
    "moon": Shore(id="moon", name="the moonlit shore", water="silver waves", sky="moon", hush="gentle hush"),
    "harbor": Shore(id="harbor", name="the harbor shore", water="little harbor waves", sky="pink dusk sky", hush="sleepy hush"),
}

PRICKLES = {
    "shell": Prickle(id="shell", name="a shell with a prickle", phrase="a tiny shell with a sharp edge", tiny_reason="it had a rough shell edge", tags={"prickle", "shore"}),
    "sea_urchin": Prickle(id="sea_urchin", name="a sea urchin", phrase="a round sea urchin", tiny_reason="its little spines were prickly", tags={"prickle", "shore"}),
    "thorn": Prickle(id="thorn", name="a drifted thorn", phrase="a small thorn caught in sea grass", tiny_reason="it was just a little thorn", tags={"prickle", "shore"}),
}

MISUNDERSTANDINGS = {
    "name": Misunderstanding(
        id="name",
        repeated_line="Is it a prickly crab?",
        mistaken_name="a prickly crab",
        truth_line="It is not a crab at all",
        fix_line="Oh, it is only a shell",
        tags={"repetition", "misunderstanding"},
    ),
    "star": Misunderstanding(
        id="star",
        repeated_line="Is it a little star?",
        mistaken_name="a little star",
        truth_line="It is not a star at all",
        fix_line="Oh, it is only a sea urchin",
        tags={"repetition", "misunderstanding"},
    ),
    "spike": Misunderstanding(
        id="spike",
        repeated_line="Is it a sleepy spike?",
        mistaken_name="a sleepy spike",
        truth_line="It is not a spike at all",
        fix_line="Oh, it is only a tiny thorn",
        tags={"repetition", "misunderstanding"},
    ),
}

CHILDREN = [("Mina", "girl"), ("Nico", "boy"), ("Lena", "girl"), ("Pip", "boy")]
EMPERORS = ["Emperor Kai", "Emperor Milo", "Emperor Sol"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SHORES:
        for p in PRICKLES:
            for m in MISUNDERSTANDINGS:
                combos.append((s, p, m))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about a shore, a prickle, and an emperor.")
    ap.add_argument("--shore", choices=SHORES)
    ap.add_argument("--prickle", choices=PRICKLES)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--emperor")
    ap.add_argument("--emperor-type", choices=["emperor"])
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
    combos = [c for c in valid_combos()
              if (args.shore is None or c[0] == args.shore)
              and (args.prickle is None or c[1] == args.prickle)
              and (args.misunderstanding is None or c[2] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    shore, prickle, misunderstanding = rng.choice(sorted(combos))
    child_name, child_type = (args.child, args.child_type) if args.child else rng.choice(CHILDREN)
    emperor_name = args.emperor or rng.choice(EMPERORS)
    emperor_type = args.emperor_type or "emperor"
    return StoryParams(
        shore=shore,
        prickle=prickle,
        misunderstanding=misunderstanding,
        child=child_name,
        child_type=child_type,
        emperor_name=emperor_name,
        emperor_type=emperor_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle bedtime story that includes the words "prickle", "shore", and "emperor".',
        f"Tell a bedtime story where {f['child'].id} mistakes a little shore thing for something else, then an emperor kindly explains it.",
        f"Write a calm story with repetition in the dialogue and a misunderstanding that ends safely at the shore.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    emperor = f["emperor"]
    prickle = f["prickle"]
    misunderstanding = f["misunderstanding"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {emperor.id}, who meet by the shore and talk about a little prickle."),
        ("What did the child keep repeating?",
         f'{child.id} kept asking, "{misunderstanding.repeated_line}" because the little thing was hard to name at first. The repetition shows the misunderstanding before the emperor clears it up.'),
        ("How did the emperor help?",
         f"{emperor.id} listened kindly and named the object correctly. That helped {child.id} understand that {prickle.name} was harmless."),
        ("How did the story end?",
         f"It ended quietly, with {child.id} feeling safe beside the {f['shore'].name}. The shore became a calm bedtime picture instead of a scary mystery."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    prickle = f["prickle"]
    return [
        ("What does the word prickle mean?",
         f"A prickle is a tiny sharp feeling or a small sharp part. It can make you notice something gently or carefully."),
        ("What is a shore?",
         f"A shore is the land at the edge of water, like where the sea or a lake meets the sand. It is a good place to look at waves."),
        ("What is an emperor?",
         f"An emperor is a ruler, like a very important king. In this story, the emperor is kind and helps the child feel calm."),
        ("Why can people misunderstand things?",
         f"People can misunderstand when they see something quickly or do not know its name yet. Then they may say the wrong thing until someone explains it."),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(shore="calm", prickle="shell", misunderstanding="name", child="Mina", child_type="girl", emperor_name="Emperor Kai", emperor_type="emperor"),
    StoryParams(shore="moon", prickle="sea_urchin", misunderstanding="star", child="Nico", child_type="boy", emperor_name="Emperor Milo", emperor_type="emperor"),
    StoryParams(shore="harbor", prickle="thorn", misunderstanding="spike", child="Lena", child_type="girl", emperor_name="Emperor Sol", emperor_type="emperor"),
]


def generate(params: StoryParams) -> StorySample:
    if params.shore not in SHORES or params.prickle not in PRICKLES or params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("(Invalid StoryParams: unknown registry key.)")
    world = tell(SHORES[params.shore], PRICKLES[params.prickle], MISUNDERSTANDINGS[params.misunderstanding],
                 child_name=params.child, child_type=params.child_type,
                 emperor_name=params.emperor_name, emperor_type=params.emperor_type)
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
    for sid in SHORES:
        lines.append(asp.fact("shore", sid))
    for pid in PRICKLES:
        lines.append(asp.fact("prickle", pid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,M) :- shore(S), prickle(P), misunderstanding(M).
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
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python valid_combos().")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        emit(sample)
    except Exception as err:
        rc = 1
        print(f"MISMATCH: smoke test failed: {err}")
    else:
        print("OK: smoke test generate/emit succeeded.")
    return rc


def build_parser_main() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:\n")
        for s, p, m in combos:
            print(f"  {s:7} {p:14} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} at the {p.shore} ({p.prickle}, {p.misunderstanding})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
