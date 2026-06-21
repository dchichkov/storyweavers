#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/intelligent_monologue_tyke_rhyme_magic_whodunit.py
===================================================================================

A tiny story world for a child-facing whodunit with rhyme and a little magic:
an intelligent tyke thinks out loud, follows clues, and reveals who took the
missing thing. The world is small, state-driven, and built to support complete
stories with a clear mystery, a turn, and a satisfying reveal.

Core premise:
- A small child detective notices a puzzling loss.
- A rhyming monologue helps organize clues and calm everyone down.
- A magical prop gives a useful, fair hint rather than solving everything.
- The mystery ends with the culprit identified and the missing thing returned.

Seed words: intelligent, monologue, tyke
Features: rhyme, magic
Style: whodunit
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
class Setting:
    id: str
    place: str
    mood: str
    surfaces: list[str] = field(default_factory=list)
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
class Clue:
    id: str
    label: str
    place: str
    kind: str
    tells_on: Optional[str] = None
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
class MagicItem:
    id: str
    label: str
    phrase: str
    hint: str
    truthiness: int
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
class Suspect:
    id: str
    label: str
    type: str
    motive: str
    tell: str
    innocent_when: str
    guilty: bool = False
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.log.append(text)

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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("missing") and "tyke" in world.entities:
        kid = world.get("tyke")
        if kid.memes["curiosity"] >= THRESHOLD and ("worry", "start") not in world.fired:
            world.fired.add(("worry", "start"))
            kid.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_suspect(world: World) -> list[str]:
    out: list[str] = []
    missing_owner = world.facts.get("missing_owner")
    if not missing_owner:
        return out
    for sid in world.facts.get("suspect_ids", []):
        sus = world.get(sid)
        if sus.meters["sticky"] >= THRESHOLD and not sus.guilty:
            sig = ("suspect", sid)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append("__suspect__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("reveal_ready") and not world.facts.get("revealed"):
        world.facts["revealed"] = True
        out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("suspect", _r_suspect), Rule("reveal", _r_reveal)]


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


def predict(world: World, suspect_id: str) -> dict:
    sim = world.copy()
    simulate_question(sim, suspect_id, narrate=False)
    return {
        "revealed": bool(sim.facts.get("revealed")),
        "sticky": sim.get(suspect_id).meters.get("sticky", 0.0),
    }


def rhyme_monologue(world: World, kid: Entity, clue: Clue, magic: MagicItem) -> None:
    kid.memes["confidence"] += 1
    world.say(
        f'{kid.id} took a breath and began a little monologue: "When something is gone, '
        f'I look where it was shown. If crumbs are near the chair, then someone sat there."'
    )
    world.say(
        f'{kid.id} pointed at the {clue.label} and grinned. "A clue can be sly, '
        f'but I am quite {kid.traits[0] if kid.traits else "smart"}; '
        f'the {magic.label} may whisper the part that I need."'
    )
    world.say(
        f'Then the {magic.label} gave a tiny glow and said, "{magic.hint}"'
    )


def simulate_question(world: World, suspect_id: str, narrate: bool = True) -> None:
    suspect = world.get(suspect_id)
    suspect.meters["sticky"] += 1
    suspect.memes["nervous"] += 1
    propagate(world, narrate=narrate)


def reveal(world: World, detective: Entity, suspect: Suspect, missing: Entity,
           clue: Clue, magic: MagicItem) -> None:
    detective.memes["triumph"] += 1
    suspect_ent = world.get(suspect.id)
    suspect_ent.meters["sticky"] += 0
    world.say(
        f'The room grew still. "{suspect.label} did it," {detective.id} said, '
        f'clapping {detective.pronoun("possessive")} hands once. '
        f'"{clue.label} and the {magic.label} both pointed the same way."'
    )
    if suspect.guilty:
        world.say(
            f"{suspect.label} blushed and admitted it had been an accident. "
            f"{suspect.label_word if hasattr(suspect, 'label_word') else suspect.label} "
            f"returned the {missing.label} at once."
        )
    else:
        world.say(
            f"But the clue led to an honest answer: {suspect.label} had simply seen "
            f"the {missing.label} on the table earlier, and the mystery finally made sense."
        )


def finish(world: World, detective: Entity, owner: Entity, missing: Entity, suspect: Suspect) -> None:
    owner.memes["relief"] += 1
    detective.memes["joy"] += 1
    world.say(
        f"{owner.label_word.capitalize()} found the {missing.label} back where it belonged, "
        f"warm from the little hands that had held it."
    )
    world.say(
        f"{detective.id} smiled. The whodunit was solved, the room was tidy again, "
        f"and the small {detective.type} looked very clever indeed."
    )


def tell(setting: Setting, clue: Clue, magic: MagicItem, suspect: Suspect,
         missing_label: str = "golden spoon", detective_name: str = "Pip",
         detective_type: str = "tyke", owner_name: str = "Mum") -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type,
                                 role="detective", traits=["intelligent", "keen"]))
    owner = world.add(Entity(id=owner_name, kind="character", type="mother", role="owner"))
    missing = world.add(Entity(id="missing", kind="thing", type="thing", label=missing_label))
    world.add(Entity(id=suspect.id, kind="character", type=suspect.type, role="suspect",
                     label=suspect.label, traits=[suspect.motive]))
    world.facts.update(
        setting=setting, clue=clue, magic=magic, suspect=suspect,
        missing=missing, missing_owner=owner, suspect_ids=[suspect.id], missing_label=missing.label
    )

    detective.memes["curiosity"] = 1
    detective.memes["intelligence"] = 2
    world.say(
        f"At {setting.place}, a {detective.type} named {detective.id} found a puzzle: "
        f"the {missing.label} was gone, and everybody looked surprised."
    )
    world.say(
        f'The air felt {setting.mood}, and the only thing louder than the silence was '
        f'the detective\'s own careful thinking.'
    )
    world.para()
    rhyme_monologue(world, detective, clue, magic)

    world.para()
    simulate_question(world, suspect.id, narrate=True)
    world.say(
        f"{suspect.label} had a tell: {suspect.tell}. That little detail fit the clue "
        f"like a key in a lock."
    )

    world.para()
    world.facts["reveal_ready"] = True
    propagate(world, narrate=True)
    reveal(world, detective, suspect, missing, clue, magic)
    world.para()
    finish(world, detective, owner, missing, suspect)
    return world


SETTINGS = {
    "kitchen": Setting(id="kitchen", place="the kitchen", mood="quiet and shiny", surfaces=["table", "floor"]),
    "classroom": Setting(id="classroom", place="the classroom", mood="still and bright", surfaces=["desk", "shelf"]),
    "attic": Setting(id="attic", place="the attic", mood="dusty and strange", surfaces=["box", "beam"]),
}

CLUES = {
    "crumbs": Clue(id="crumbs", label="crumbs", place="near the chair", kind="food", tells_on="snack"),
    "sparkle": Clue(id="sparkle", label="sparkles", place="on the rug", kind="magic", tells_on="glitter"),
    "footprint": Clue(id="footprint", label="tiny footprint", place="by the door", kind="dust", tells_on="someone passed by"),
}

MAGIC_ITEMS = {
    "mirror": MagicItem(id="mirror", label="magic mirror", phrase="a magic mirror", hint="Look where the shiny thing points, not where the eyes first stare.", truthiness=3, tags={"magic"}),
    "bell": MagicItem(id="bell", label="rhyme bell", phrase="a rhyme bell", hint="The answer likes to hide near a sound that rhymes.", truthiness=2, tags={"rhyme", "magic"}),
    "star": MagicItem(id="star", label="glow star", phrase="a glow star", hint="The brightest clue is often the one no one wanted to notice.", truthiness=3, tags={"magic"}),
}

SUSPECTS = {
    "cat": Suspect(id="cat", label="the cat", type="thing", motive="curiosity", tell="a trail of flour on its whiskers", innocent_when="it only wanted to nap", guilty=True, tags={"cat"}),
    "brother": Suspect(id="brother", label="the big brother", type="boy", motive="play", tell="crumbs on his sleeve", innocent_when="he was building blocks", guilty=True, tags={"boy"}),
    "neighbor": Suspect(id="neighbor", label="the neighbor", type="woman", motive="help", tell="a muddy shoe", innocent_when="she had come to return a ball", guilty=False, tags={"adult"}),
}


@dataclass
class StoryParams:
    setting: str = "kitchen"
    clue: str = "crumbs"
    magic: str = "mirror"
    suspect: str = "cat"
    missing_label: str = "golden spoon"
    detective_name: str = "Pip"
    detective_type: str = "tyke"
    owner_name: str = "Mum"
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


CURATED = [
    StoryParams(setting="kitchen", clue="crumbs", magic="bell", suspect="brother", missing_label="blue cookie tin", detective_name="Pip", detective_type="tyke", owner_name="Mum"),
    StoryParams(setting="classroom", clue="sparkle", magic="mirror", suspect="cat", missing_label="silver paintbrush", detective_name="Dot", detective_type="tyke", owner_name="Teacher"),
    StoryParams(setting="attic", clue="footprint", magic="star", suspect="neighbor", missing_label="red ribbon", detective_name="Bo", detective_type="tyke", owner_name="Aunt"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, _ in SETTINGS.items():
        for cid, clue in CLUES.items():
            for mid, magic in MAGIC_ITEMS.items():
                if clue.kind == "magic" and "magic" not in magic.tags:
                    continue
                combos.append((sid, cid, mid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit story world with rhyme and magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--magic", choices=MAGIC_ITEMS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--owner")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, magic = rng.choice(sorted(combos))
    suspect = args.suspect or rng.choice(sorted(SUSPECTS))
    name = args.name or rng.choice(["Pip", "Dot", "Bo", "Kit", "Nia"])
    owner = args.owner or rng.choice(["Mum", "Aunt", "Teacher"])
    return StoryParams(setting=setting, clue=clue, magic=magic, suspect=suspect, detective_name=name, owner_name=owner)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.clue not in CLUES or params.magic not in MAGIC_ITEMS or params.suspect not in SUSPECTS:
        raise StoryError("Unknown story parameters.")
    world = tell(SETTINGS[params.setting], CLUES[params.clue], MAGIC_ITEMS[params.magic], SUSPECTS[params.suspect], params.detective_name, params.detective_type, params.owner_name, params.missing_label)
    prompts = [
        f"Write a whodunit for a little tyke named {params.detective_name} with a rhyme and a magic clue.",
        f"Tell a child mystery where {params.detective_name} uses a monologue to solve a missing {params.missing_label}.",
        f"Write a story with the words intelligent, monologue, and tyke, and let a magic clue help reveal who did it.",
    ]
    story_qa = [
        QAItem(question="Who solved the mystery?", answer=f"{params.detective_name}, the little {params.detective_type}, solved it by following the clue and the magic hint."),
        QAItem(question="What made the detective think the way they did?", answer="The detective used a careful monologue to line up the clues. The rhyme kept the thinking calm, and the magic item gave a useful hint."),
        QAItem(question="What changed by the end?", answer=f"The missing {params.missing_label} was found again, the suspect answer became clear, and the room felt calm and tidy."),
    ]
    world_qa = [
        QAItem(question="What is a clue?", answer="A clue is a small piece of information that helps someone figure out what happened. In a mystery, clues point toward the answer."),
        QAItem(question="What does magic do in this story world?", answer="Magic gives a gentle hint rather than doing all the work. It helps the detective notice the right thing faster."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,M) :- setting(S), clue(C), magic(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for mid in MAGIC_ITEMS:
        lines.append(asp.fact("magic", mid))
    return "\n".join(lines)


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
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, clue=None, magic=None, suspect=None, name=None, owner=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"MISMATCH in generate() smoke test: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
