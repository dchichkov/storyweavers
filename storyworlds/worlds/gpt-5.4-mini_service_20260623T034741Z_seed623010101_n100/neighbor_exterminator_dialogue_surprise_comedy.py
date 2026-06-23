#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/neighbor_exterminator_dialogue_surprise_comedy.py
===========================================================================================================================

A small comedy storyworld about a neighbor, an exterminator, and a surprise
that turns out to be much sillier than scary.

The seed tale:
---
A neighbor kept hearing loud scratching in the wall and worried that bugs had
moved in. They called an exterminator, who arrived with a big toolbox and a very
serious face. But after listening closely, the exterminator discovered the noise
wasn't bugs at all. It was the neighbor's pet parrot practicing tap dancing on a
wooden shelf. Everyone laughed, the neighbor apologized, and the exterminator
left with a smile and a feather in his hat.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    place: str = "the apartment hall"
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
    noise: str
    source: str
    surprise: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
class Visitor:
    id: str
    label: str
    tool: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    clue: str = "scratching"
    visitor: str = "classic"
    neighbor_name: str = "Nina"
    neighbor_gender: str = "woman"
    exterminator_name: str = "Otto"
    exterminator_gender: str = "man"
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def valid_combos() -> list[tuple[str, str]]:
    return [(c, v) for c in CLUES for v in VISITORS]


def clue_risk(clue: Clue) -> bool:
    return clue.id in {"scratching", "thumping", "buzzing"}


def visitor_can_help(visitor: Visitor, clue: Clue) -> bool:
    return clue_risk(clue) and visitor.id in {"classic", "mop_up", "tiny_twist"}


def _r_relief(world: World) -> list[str]:
    out = []
    if world.facts.get("resolved") and not world.facts.get("quiet"):
        if ("relief",) in world.fired:
            return []
        world.fired.add(("relief",))
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["relief"] += 1
                e.memes["joy"] += 1
        out.append("__relief__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for sent in _r_relief(world):
            changed = True
            if sent != "__relief__":
                produced.append(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, clue: Clue, visitor: Visitor,
         neighbor_name: str, neighbor_gender: str,
         exterminator_name: str, exterminator_gender: str) -> World:
    world = World(setting)
    neighbor = world.add(Entity(id=neighbor_name, kind="character", type=neighbor_gender, label="neighbor"))
    exterminator = world.add(Entity(id=exterminator_name, kind="character", type=exterminator_gender, label="exterminator"))
    pet = world.add(Entity(id="pet", kind="character", type="bird", label="parrot"))

    for e in (neighbor, exterminator, pet):
        e.meters.setdefault("noise", 0.0)
        e.meters.setdefault("mess", 0.0)
        e.memes.setdefault("worry", 0.0)
        e.memes.setdefault("joy", 0.0)
        e.memes.setdefault("relief", 0.0)

    world.facts["setting"] = setting
    world.facts["clue"] = clue
    world.facts["visitor"] = visitor

    neighbor.memes["worry"] += 1
    neighbor.meters["noise"] += 1
    world.say(f"{neighbor.id} lived at {setting.place} and kept hearing {clue.noise} noises.")
    world.say(f'"Something is in the wall," {neighbor.pronoun()} said. "I hope it is not bugs."')
    world.say(f'"Then I will need an exterminator," {neighbor.pronoun()} said, and {neighbor.pronoun()} called one right away.')

    world.para()
    exterminator.memes["focus"] += 1
    world.say(f"{exterminator.id} arrived with {visitor.phrase} and a very serious face.")
    world.say(f'"Where is the trouble?" {exterminator.pronoun()} asked.')
    world.say(f'"In the wall," {neighbor.id} said. "It sounds dramatic."')

    world.para()
    neighbor.memes["worry"] += 1
    world.say(f"{exterminator.id} listened, tapped the wall, and tilted {exterminator.pronoun('possessive')} head.")
    if clue.id == "scratching":
        world.say(f'"That is not bug scratching," {exterminator.pronoun()} said. "That is tap dancing."')
    elif clue.id == "thumping":
        world.say(f'"That is not a nest," {exterminator.pronoun()} said. "That is a very busy shelf."')
    else:
        world.say(f'"That is not buzzing," {exterminator.pronoun()} said. "That is a very offended parrot."')

    world.say(f'Then the surprise: the noise came from {clue.surprise}.')
    world.say(f'"Of course," {neighbor.id} said. "I taught {pet.id} to dance."')
    world.say(f'"You taught a bird tap shoes?" {exterminator.id} asked.')
    world.say(f'"Only on weekends," {neighbor.id} said. "He is unionized."')

    world.para()
    world.say(f'{exterminator.id} laughed so hard {exterminator.pronoun()} nearly dropped {exterminator.pronoun("possessive")} toolbox.')
    world.say(f'"No bugs, no problem," {exterminator.pronoun()} said. "But your bird has excellent rhythm."')
    world.say(f'{neighbor.id} apologized, and {exterminator.id} left smiling with one feather stuck to {exterminator.pronoun("possessive")} hat.')
    world.facts["quiet"] = True
    world.facts["resolved"] = True
    propagate(world, narrate=False)
    world.facts.update(neighbor=neighbor, exterminator=exterminator, pet=pet, outcome="surprise")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a young child that uses the words "neighbor" and "exterminator" and includes a surprise ending.',
        f"Tell a comedy story where {f['neighbor'].id} thinks a noise means bugs, calls an exterminator, and learns the sound is something silly.",
        f"Write a short dialogue story with a worried neighbor, an exterminator, and a surprising reveal that makes everyone laugh.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    n, e, c = f["neighbor"], f["exterminator"], f["clue"]
    return [
        QAItem(
            question=f"Why did {n.id} call an exterminator?",
            answer=f"{n.id} heard a noisy sound in the wall and worried that bugs had moved in. {n.pronoun().capitalize()} wanted someone to check before the worry got bigger.",
        ),
        QAItem(
            question=f"What did the exterminator think at first?",
            answer=f"{e.id} thought the trouble might be pests, but then {e.pronoun()} listened carefully and smiled. The sound turned out to be something much sillier than bugs.",
        ),
        QAItem(
            question="What was the surprise at the end?",
            answer=f"The surprise was that the noise came from a parrot practicing tap dancing on a shelf. Everyone laughed because the scary-sounding problem was actually a funny one.",
        ),
        QAItem(
            question=f"How did {n.id} and {e.id} feel at the end?",
            answer=f"They both ended up laughing. {n.id} felt relieved, and {e.id} left amused instead of serious.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an exterminator do?",
            answer="An exterminator helps get rid of pests like bugs and mice from a home. The job is to solve a problem that people do not want in the house.",
        ),
        QAItem(
            question="Why can a funny surprise be nice in a story?",
            answer="A funny surprise makes the ending feel playful and bright. It can turn a worry into laughter when the problem is not as bad as it seemed.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    out.append(f"facts={sorted(world.facts)}")
    return "\n".join(out)


CLUES = {
    "scratching": Clue(id="scratching", noise="scratching", source="a parrot practicing tap dancing", surprise="the neighbor's pet parrot practicing tap dancing on a shelf", tags={"bird", "comedy"}),
    "thumping": Clue(id="thumping", noise="thumping", source="a rolling toy drum", surprise="the neighbor's wind-up toy drummer on top of the fridge", tags={"toy", "comedy"}),
    "buzzing": Clue(id="buzzing", noise="buzzing", source="a blender making soup", surprise="the neighbor's blender because someone forgot the lid", tags={"kitchen", "comedy"}),
}

VISITORS = {
    "classic": Visitor(id="classic", label="a big toolbox", tool="toolbox", phrase="a big toolbox and a very serious face", tags={"toolbox"}),
    "mop_up": Visitor(id="mop_up", label="a tiny dustpan", tool="dustpan", phrase="a tiny dustpan and a very stern mustache", tags={"dustpan"}),
    "tiny_twist": Visitor(id="tiny_twist", label="a very small flashlight", tool="flashlight", phrase="a very small flashlight and a giant hat", tags={"flashlight"}),
}


def explain_rejection(clue: Clue, visitor: Visitor) -> str:
    if not clue_risk(clue):
        return "(No story: the chosen noise is too calm for a comedy of mistaken pests. Pick a more suspicious sound.)"
    if not visitor_can_help(visitor, clue):
        return "(No story: this visitor would not plausibly make the pest-check story work.)"
    return "(No story: the combination is not reasonable.)"


def valid_story_combos() -> list[tuple[str, str]]:
    out = []
    for c in CLUES:
        for v in VISITORS:
            if clue_risk(CLUES[c]) and visitor_can_help(VISITORS[v], CLUES[c]):
                out.append((c, v))
    return out


ASP_RULES = r"""
clue_risk(scratching).
clue_risk(thumping).
clue_risk(buzzing).

helpful(classic).
helpful(mop_up).
helpful(tiny_twist).

valid(C,V) :- clue_risk(C), helpful(V).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for v in VISITORS:
        lines.append(asp.fact("visitor", v))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class StoryParams:
    clue: str = "scratching"
    visitor: str = "classic"
    neighbor_name: str = "Nina"
    neighbor_gender: str = "woman"
    exterminator_name: str = "Otto"
    exterminator_gender: str = "man"
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a neighbor and an exterminator.")
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--neighbor-name")
    ap.add_argument("--neighbor-gender", choices=["woman", "man"])
    ap.add_argument("--exterminator-name")
    ap.add_argument("--exterminator-gender", choices=["woman", "man"])
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
    combos = [c for c in valid_story_combos()
              if (args.clue is None or c[0] == args.clue)
              and (args.visitor is None or c[1] == args.visitor)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    clue, visitor = rng.choice(sorted(combos))
    return StoryParams(
        clue=clue,
        visitor=visitor,
        neighbor_name=args.neighbor_name or rng.choice(["Nina", "Mara", "Tess", "Ivy", "Rosa"]),
        neighbor_gender=args.neighbor_gender or rng.choice(["woman", "man"]),
        exterminator_name=args.exterminator_name or rng.choice(["Otto", "Gus", "Perry", "Luca"]),
        exterminator_gender=args.exterminator_gender or rng.choice(["man", "woman"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.clue not in CLUES or params.visitor not in VISITORS:
        raise StoryError("invalid params")
    world = tell(Setting(), CLUES[params.clue], VISITORS[params.visitor],
                 params.neighbor_name, params.neighbor_gender,
                 params.exterminator_name, params.exterminator_gender)
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


def asp_verify() -> int:
    py = set(valid_story_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH")
        print("python-only:", sorted(py - cl))
        print("clingo-only:", sorted(cl - py))
        return 1
    try:
        sample = generate(StoryParams())
        _ = sample.story
        _ = format_qa(sample)
        print("OK: ASP parity and smoke test passed.")
        return 0
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1


CURATED = [
    StoryParams(clue="scratching", visitor="classic", neighbor_name="Nina", neighbor_gender="woman", exterminator_name="Otto", exterminator_gender="man"),
    StoryParams(clue="thumping", visitor="mop_up", neighbor_name="Mara", neighbor_gender="woman", exterminator_name="Gus", exterminator_gender="man"),
    StoryParams(clue="buzzing", visitor="tiny_twist", neighbor_name="Tess", neighbor_gender="woman", exterminator_name="Perry", exterminator_gender="man"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
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
            header = f"### {p.neighbor_name} and the {p.visitor} exterminator"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
