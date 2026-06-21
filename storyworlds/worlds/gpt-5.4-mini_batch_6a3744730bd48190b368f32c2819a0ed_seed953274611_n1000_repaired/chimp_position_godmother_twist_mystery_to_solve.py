#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chimp_position_godmother_twist_mystery_to_solve.py
===================================================================================

A small storyworld for an adventure tale with a chimp, a mysterious position
problem, a godmother, and a magical twist.

Premise:
- A child and a chimp are on an adventure trail.
- A strange position clue causes confusion.
- The godmother notices a mystery to solve.
- Magic reveals the twist.
- The ending proves the position was the key all along.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- story-driven state changes
- QA from world state, not rendered English
- a Python reasonableness gate plus inline ASP twin
- CLI support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if case == "possessive":
            return "its"
        return "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "godmother": "godmother"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    clue_place: str
    dark_place: str
    adventure: str
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
class CharacterSpec:
    id: str
    type: str
    role: str
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
class Mystery:
    id: str
    clue: str
    misread: str
    reveal: str
    twist: str
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
class Magic:
    id: str
    tool: str
    effect: str
    reveal: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone.facts = copy.deepcopy(self.facts)
        return clone
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


def _r_confusion(world: World) -> list[str]:
    out = []
    c = world.get("chimp")
    if c.meters["confused"] >= THRESHOLD and (("confusion",) not in world.fired):
        world.fired.add(("confusion",))
        world.get("trail").meters["tension"] += 1
        out.append("__confusion__")
    return out


def _r_magic(world: World) -> list[str]:
    out = []
    if world.get("chimp").meters["wonder"] >= THRESHOLD and (("magic",) not in world.fired):
        world.fired.add(("magic",))
        world.get("trail").meters["mystery"] += 1
        out.append("__magic__")
    return out


CAUSAL_RULES = [Rule("confusion", _r_confusion), Rule("magic", _r_magic)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def reasonableness_ok(setting: Setting, mystery: Mystery, magic: Magic) -> bool:
    return "adventure" in setting.tags and "twist" in mystery.tags and "magic" in magic.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            for gid in MAGICS:
                if reasonableness_ok(SETTINGS[sid], MYSTERIES[mid], MAGICS[gid]):
                    combos.append((sid, mid, gid))
    return combos


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("chimp").meters["confused"] += 1
    propagate(sim, narrate=False)
    return {
        "mystery": sim.get("trail").meters["mystery"] >= THRESHOLD,
        "tension": sim.get("trail").meters["tension"],
    }


def tell(setting: Setting, mystery: Mystery, magic: Magic, chimp_name: str = "Koko",
         child_name: str = "Mina", godmother_name: str = "Aunt June") -> World:
    world = World(setting)
    chimp = world.add(Entity(id="chimp", kind="character", type="chimp", role="helper", label=chimp_name, tags={"chimp"}))
    child = world.add(Entity(id="child", kind="character", type="girl", role="adventurer", label=child_name, tags={"adventure"}))
    godmother = world.add(Entity(id="godmother", kind="character", type="woman", role="guide", label=godmother_name, tags={"godmother"}))
    trail = world.add(Entity(id="trail", type="place", label=setting.place, tags={"adventure"}))

    world.say(f"{child.label} and {chimp.label} went on an adventure through {setting.place}.")
    world.say(f"They followed a strange clue about a {mystery.clue} near {setting.clue_place}.")
    world.say(f"But the note said the right position was only important if you looked from the {setting.dark_place}.")

    world.para()
    child.memes["curiosity"] += 1
    chimp.meters["confused"] += 1
    chimp.meters["wonder"] += 1
    world.say(f"{chimp.label} scratched {chimp.pronoun('possessive')} head and pointed at the wrong spot.")
    world.say(f"{child.label} guessed the clue meant {mystery.misread}, but the trail still felt puzzling.")

    pred = predict(world)
    godmother.memes["calm"] += 1
    world.say(f"Then {godmother.label} arrived with a smile. '{mystery.reveal}!' {godmother.label} said.")
    world.say(f"She lifted the magic {magic.tool}, and it {magic.effect}.")

    if pred["mystery"]:
        world.para()
        trail.meters["mystery"] += 1
        world.say(f"The light changed everything. The answer was not the thing itself, but its position.")
        world.say(f"Once they stood in the right place, the hidden path appeared and the twist made sense.")
    else:
        raise StoryError("The mystery did not become vivid enough to tell a story.")

    world.para()
    child.memes["joy"] += 1
    chimp.memes["joy"] += 1
    godmother.memes["pride"] += 1
    world.say(f"{child.label} laughed, and {chimp.label} clapped {chimp.pronoun('possessive')} hands.")
    world.say(f"Together they solved the mystery, and {setting.adventure} ended with a bright magical view from the correct position.")

    world.facts.update(
        child=child,
        chimp=chimp,
        godmother=godmother,
        setting=setting,
        mystery=mystery,
        magic=magic,
        trail=trail,
        reveal_position=True,
        twist=mystery.twist,
    )
    return world


SETTINGS = {
    "jungle": Setting(id="jungle", place="the jungle trail", clue_place="the tall root", dark_place="the shadowy bend", adventure="adventure", tags={"adventure"}),
    "ruins": Setting(id="ruins", place="the old ruins", clue_place="the mossy arch", dark_place="the broken hall", adventure="adventure", tags={"adventure"}),
    "cave": Setting(id="cave", place="the glittering cave", clue_place="the narrow ledge", dark_place="the far wall", adventure="adventure", tags={"adventure"}),
}

MYSTERIES = {
    "statue": Mystery(id="statue", clue="silver statue", misread="the statue was the clue", reveal="The statue was only a marker", twist="the clue was about where to stand", tags={"twist"}),
    "shadow": Mystery(id="shadow", clue="moving shadow", misread="the shadow was a monster", reveal="The shadow was only a sign", twist="the clue was about the angle of the light", tags={"twist"}),
    "door": Mystery(id="door", clue="hidden door", misread="the door was locked forever", reveal="The door was not locked at all", twist="the clue was about the side to face", tags={"twist"}),
}

MAGICS = {
    "lamp": Magic(id="lamp", tool="lantern", effect="glowed gold over the stones", reveal="gold light spilled across the path", tags={"magic"}),
    "map": Magic(id="map", tool="magic map", effect="shimmered and pointed the way", reveal="a magical line pointed at the right position", tags={"magic"}),
    "stone": Magic(id="stone", tool="moonstone", effect="sparkled and revealed footprints", reveal="sparkling dust marked the correct spot", tags={"magic"}),
}

@dataclass
class StoryParams:
    setting: str
    mystery: str
    magic: str
    chimp_name: str = "Koko"
    child_name: str = "Mina"
    godmother_name: str = "Aunt June"
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
    StoryParams(
        setting="jungle",
        mystery="statue",
        magic="lamp",
        chimp_name="Koko",
        child_name="Mina",
        godmother_name="Aunt June",
        seed=None,
    ),
    StoryParams(
        setting="ruins",
        mystery="shadow",
        magic="map",
        chimp_name="Milo",
        child_name="Ada",
        godmother_name="Godmother Fern",
        seed=None,
    ),
    StoryParams(
        setting="cave",
        mystery="door",
        magic="stone",
        chimp_name="Bobo",
        child_name="Nia",
        godmother_name="Aunt Lila",
        seed=None,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an adventure story about a chimp, a godmother, and a mystery about position in {f['setting'].place}.",
        f"Tell a child-facing mystery where {f['chimp'].label} and {f['child'].label} get a clue wrong, then a godmother uses magic to reveal the answer.",
        f"Write a twisty story that includes the words chimp, position, and godmother, and ends with the mystery solved by magic.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    chimp = f["chimp"]
    godmother = f["godmother"]
    setting = f["setting"]
    mystery = f["mystery"]
    magic = f["magic"]
    return [
        ("Who went on the adventure?",
         f"{child.label} and {chimp.label} went together, and {godmother.label} helped them when the mystery became confusing."),
        ("What was the mystery about?",
         f"It was about a clue that only made sense when they looked from the right position. That twist changed the whole answer."),
        (f"What did {godmother.label} do?",
         f"She arrived with magic and showed that the clue was not about the object itself, but about where to stand in {setting.place}."),
        ("How did the story end?",
         f"They solved the mystery and saw the path clearly at last. The ending proved the position mattered more than the first guess."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a chimp?",
         "A chimp is a kind of ape. Chimps are smart, curious animals that can climb and use their hands well."),
        ("What does position mean here?",
         "Position means where something is placed or where someone stands. In a mystery like this, the answer depends on the right spot."),
        ("What is a godmother?",
         "A godmother is a caring grown-up who helps guide a child. In stories, a godmother often gives wise help."),
        ("What is magic in an adventure story?",
         "Magic is a special story tool that can reveal hidden things or help characters solve problems in surprising ways."),
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    magic: str
    chimp_name: str = "Koko"
    child_name: str = "Mina"
    godmother_name: str = "Aunt June"
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
    ap = argparse.ArgumentParser(description="Adventure storyworld about a chimp, a godmother, position, and magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--chimp-name")
    ap.add_argument("--child-name")
    ap.add_argument("--godmother-name")
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
              and (args.mystery is None or c[1] == args.mystery)
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, magic = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        mystery=mystery,
        magic=magic,
        chimp_name=args.chimp_name or rng.choice(["Koko", "Milo", "Bobo", "Tiki"]),
        child_name=args.child_name or rng.choice(["Mina", "Ada", "Nia", "Lina"]),
        godmother_name=args.godmother_name or rng.choice(["Aunt June", "Godmother Fern", "Aunt Lila"]),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES or params.magic not in MAGICS:
        raise StoryError("Invalid parameters for this storyworld.")
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], MAGICS[params.magic],
                 chimp_name=params.chimp_name, child_name=params.child_name, godmother_name=params.godmother_name)
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


ASP_RULES = r"""
twist(S) :- mystery(S), twisty(S).
magic(M) :- magic_item(M).
valid(S, M, G) :- setting(S), mystery(M), magic_item(G), adventure_setting(S), twisty(M), magicy(G).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "adventure" in s.tags:
            lines.append(asp.fact("adventure_setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        if "twist" in m.tags:
            lines.append(asp.fact("twisty", mid))
    for gid, g in MAGICS.items():
        lines.append(asp.fact("magic_item", gid))
        lines.append(asp.fact("magicy", gid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH between ASP and Python gate.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            for gid in MAGICS:
                if reasonableness_ok(SETTINGS[sid], MYSTERIES[mid], MAGICS[gid]):
                    combos.append((sid, mid, gid))
    return combos

def story_knowledge_tags(world: World) -> set[str]:
    return {"chimp", "position", "godmother", "magic", "twist"}

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.child_name}, {p.chimp_name}, and the {p.mystery} mystery"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
