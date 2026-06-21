#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/research_conflict_suspense_pirate_tale.py
=========================================================================
A small pirate storyworld about a curious ship's crew, a secret map, a tense
research mission, and a safe resolution after conflict and suspense.

Seed premise:
- Style: Pirate Tale
- Feature: Conflict, Suspense
- Seed word: research

The domain models a child-facing pirate crew searching library clues and ship
records to solve a mystery. The tension comes from a rival pirate crew trying to
steal the clue, and the suspense comes from waiting through the dark while the
research pays off.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVE_INIT = 4.0


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
class Place:
    id: str
    label: str
    dark: bool = False
    dangerous: bool = False
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
class Clue:
    id: str
    label: str
    phrase: str
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
class Rival:
    id: str
    label: str
    tricky: bool = True
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
class Tool:
    id: str
    label: str
    phrase: str
    safe: bool = True
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    setting: str
    clue: str
    rival: str
    tool: str
    investigator: str
    investigator_gender: str
    helper: str
    helper_gender: str
    captain: str
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
    "harbor": Place(id="harbor", label="the harbor", dark=False, dangerous=False, tags={"sea"}),
    "cave": Place(id="cave", label="the sea cave", dark=True, dangerous=True, tags={"dark", "cave"}),
    "ship": Place(id="ship", label="the old ship", dark=True, dangerous=False, tags={"ship", "dark"}),
}

CLUES = {
    "journal": Clue(id="journal", label="captain's journal", phrase="a salty captain's journal", tags={"research"}),
    "chart": Clue(id="chart", label="map chart", phrase="a map chart with tiny ink marks", tags={"research", "map"}),
    "logbook": Clue(id="logbook", label="logbook", phrase="a ship logbook full of dates and notes", tags={"research"}),
}

RIVALS = {
    "red_crew": Rival(id="red_crew", label="the Red Hook crew", tricky=True, tags={"conflict"}),
    "black_crew": Rival(id="black_crew", label="the Black Sail crew", tricky=True, tags={"conflict", "suspense"}),
}

TOOLS = {
    "lantern": Tool(id="lantern", label="lantern", phrase="a lantern with a steady glow", safe=True, tags={"light"}),
    "spyglass": Tool(id="spyglass", label="spyglass", phrase="a small spyglass", safe=True, tags={"research"}),
    "rope_lamp": Tool(id="rope_lamp", label="rope lamp", phrase="a rope lamp tied high on the mast", safe=True, tags={"light"}),
}

GIRL_NAMES = ["Mira", "Lina", "Tess", "Nia", "Ruby", "Pip"]
BOY_NAMES = ["Kai", "Owen", "Finn", "Jace", "Nate", "Bram"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, clue in CLUES.items():
            for rid, rival in RIVALS.items():
                if setting.dark and "research" in clue.tags and "conflict" in rival.tags:
                    combos.append((sid, cid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld about research, conflict, and suspense.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--rival", choices=RIVALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", dest="helper_gender", choices=["girl", "boy"])
    ap.add_argument("--captain")
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and not SETTINGS[args.setting].dark:
        raise StoryError("This pirate tale needs suspense, so the setting must be dark enough for a tense search.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.rival is None or c[2] == args.rival)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, rival = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(TOOLS))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or _pick_name(rng, gender)
    helper = args.helper or _pick_name(rng, helper_gender)
    captain = args.captain or rng.choice(["Captain Reed", "Captain Tide", "Captain Marlow"])
    return StoryParams(setting=setting, clue=clue, rival=rival, tool=tool,
                       investigator=name, investigator_gender=gender,
                       helper=helper, helper_gender=helper_gender, captain=captain)


def _tension_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.investigator, kind="character", type=params.investigator_gender, role="investigator"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    captain = world.add(Entity(id="captain", kind="character", type="adult", label=params.captain, role="captain"))
    world.add(Entity(id="setting", type="place", label=SETTINGS[params.setting].label))
    world.add(Entity(id="clue", type="clue", label=CLUES[params.clue].label))
    world.add(Entity(id="rival", type="rival", label=RIVALS[params.rival].label))
    world.add(Entity(id="tool", type="tool", label=TOOLS[params.tool].label))
    hero.memes["bravery"] = BRAVE_INIT
    helper.memes["worry"] = 2.0
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["captain"] = captain
    return world


def _research_scene(world: World, params: StoryParams) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    rival = RIVALS[params.rival]
    tool = TOOLS[params.tool]
    hero.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(f"On a moonless night, {hero.id} and {helper.id} slipped onto {setting.label}.")
    world.say(f"They were on a careful research mission, looking for {clue.phrase} that might explain the hidden tide route.")
    world.say(f'{helper.id} held up {tool.phrase}, and the weak glow made the wet wood shine like black glass.')
    world.say(f'Far off, {rival.label} prowled between the crates, and the crew had to whisper to keep the clue secret.')


def _conflict_scene(world: World, params: StoryParams) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    rival = RIVALS[params.rival]
    hero.memes["defiance"] += 1
    helper.memes["suspense"] += 1
    world.para()
    world.say(f'Then {rival.label} appeared at the hatch and shouted, "Hand over the research!"')
    world.say(f"{hero.id} stepped in front of the clue, and {helper.id} grabbed the map tighter.")
    world.say("For a moment, nobody moved. The sea creaked, the ropes tapped the mast, and the dark felt very close.")


def _solve_scene(world: World, params: StoryParams) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    captain = world.facts["captain"]
    clue = CLUES[params.clue]
    tool = TOOLS[params.tool]
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    captain.memes["pride"] += 1
    world.para()
    world.say(f"At last, {hero.id} noticed a tiny ink mark in {clue.label} that matched the rope knot by the mast.")
    world.say(f"That was the missing answer in their research, and it showed where the hidden cove waited.")
    world.say(f'{captain.label_word if hasattr(captain, "label_word") else captain.label} smiled and said, "Well done. You solved it without ever losing the clue."')
    world.say(f"With {tool.label} lighting the deck, the crew set out together, and the rival pirates slipped away in the fog.")


def tell(params: StoryParams) -> World:
    world = _tension_world(params)
    _research_scene(world, params)
    _conflict_scene(world, params)
    _solve_scene(world, params)
    world.facts.update(
        params=params,
        setting=SETTINGS[params.setting],
        clue=CLUES[params.clue],
        rival=RIVALS[params.rival],
        tool=TOOLS[params.tool],
        outcome="solved",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate story for a small child that includes the word "research" and has a tense but safe conflict on {f["setting"].label}.',
        f"Tell a suspenseful pirate tale where {f['hero'].id} and {f['helper'].id} use research to solve a mystery before {f['rival'].label} can steal it.",
        f'Write a child-friendly pirate adventure with the word "research", a rival crew, and a brave ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    clue = f["clue"]
    rival = f["rival"]
    captain = f["captain"]
    return [
        QAItem(
            question="What were the children doing on the ship?",
            answer=f"They were doing research to find the clue and solve the mystery. They stayed quiet because the deck was dark and another crew was nearby."
        ),
        QAItem(
            question="What caused the conflict in the story?",
            answer=f"The conflict started when {rival.label} demanded the research and tried to take the clue. {hero.id} and {helper.id} protected it so they could finish their search."
        ),
        QAItem(
            question="How did the suspense end?",
            answer=f"The suspense ended when {hero.id} noticed the tiny ink mark in {clue.label} and found the answer. After that, {captain.label} was proud and the crew sailed on safely."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is research?",
            answer="Research is when you look carefully at clues, facts, or books to learn something new. It helps you solve problems and understand a mystery."
        ),
        QAItem(
            question="Why can a dark place feel suspenseful?",
            answer="A dark place can feel suspenseful because you cannot see everything at once. That makes people wait, listen closely, and wonder what might happen next."
        ),
        QAItem(
            question="What is a pirate crew?",
            answer="A pirate crew is a group of pirates who work together on a ship. They share jobs, watch for danger, and sail as a team."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,R) :- setting(S), clue(C), rival(R), dark(S), clue_has_research(C), rival_conflict(R).
outcome(solved) :- valid(_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.dark:
            lines.append(asp.fact("dark", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if "research" in c.tags:
            lines.append(asp.fact("clue_has_research", cid))
    for rid, r in RIVALS.items():
        lines.append(asp.fact("rival", rid))
        if "conflict" in r.tags:
            lines.append(asp.fact("rival_conflict", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome() -> str:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    vals = asp.atoms(model, "outcome")
    return vals[0][0] if vals else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as ex:
        rc = 1
        print(f"SMOKE TEST FAILED: {ex}")
    return rc


CURATED = [
    StoryParams(setting="ship", clue="journal", rival="red_crew", tool="lantern", investigator="Mira", investigator_gender="girl", helper="Kai", helper_gender="boy", captain="Captain Reed"),
    StoryParams(setting="cave", clue="chart", rival="black_crew", tool="rope_lamp", investigator="Finn", investigator_gender="boy", helper="Nia", helper_gender="girl", captain="Captain Tide"),
    StoryParams(setting="ship", clue="logbook", rival="black_crew", tool="spyglass", investigator="Ruby", investigator_gender="girl", helper="Bram", helper_gender="boy", captain="Captain Marlow"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.clue not in CLUES or params.rival not in RIVALS or params.tool not in TOOLS:
        raise StoryError("Invalid params for this pirate storyworld.")
    world = tell(params)
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


def resolve_default_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        print("outcome:", asp_outcome())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.investigator} and {p.helper}: {p.setting} / {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.rival is None or c[2] == args.rival)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, rival = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(TOOLS))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    return StoryParams(
        setting=setting,
        clue=clue,
        rival=rival,
        tool=tool,
        investigator=args.name or _pick_name(rng, gender),
        investigator_gender=gender,
        helper=args.helper or _pick_name(rng, helper_gender),
        helper_gender=helper_gender,
        captain=args.captain or rng.choice(["Captain Reed", "Captain Tide", "Captain Marlow"]),
    )


if __name__ == "__main__":
    main()
