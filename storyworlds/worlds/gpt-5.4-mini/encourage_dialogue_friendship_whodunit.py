#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/encourage_dialogue_friendship_whodunit.py
=========================================================================

A small storyworld for a kid-friendly whodunit about friendship, dialogue, and
encouragement.

Premise
-------
A tiny group of friends is preparing for a club show-and-tell. One special item
goes missing, everyone talks, a clue trail appears, and the mystery is solved by
careful noticing, honest dialogue, and a friend who encourages the shy one to
speak up.

The world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a reasonableness gate
- a declarative ASP twin
- three grounded Q&A sets

The word "encourage" is central to the story, along with friendship and dialogue.
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
SENSE_MIN = 2


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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    clue_spots: list[str]

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
class ClueItem:
    id: str
    label: str
    hiding_place: str
    shine: str
    tags: set[str] = field(default_factory=set)

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
class Suspect:
    id: str
    label: str
    sentence: str
    honesty: int
    alibi: str
    tags: set[str] = field(default_factory=set)

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
class Hunch:
    id: str
    clue_needed: str
    suspect_id: str
    reveal: str
    tags: set[str] = field(default_factory=set)

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
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["missing"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ch in list(world.entities.values()):
            if ch.kind == "character":
                ch.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_doubt(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("talked") and world.facts.get("shy"):
        sig = ("doubt", "shy")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("shy").memes["doubt"] += 1
            out.append("__doubt__")
    return out


CAUSAL_RULES = [Rule("worry", "emotion", _r_worry), Rule("doubt", "emotion", _r_doubt)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def clue_needed_for(setting: Setting, item: ClueItem) -> bool:
    return item.hiding_place in setting.clue_spots


def suspect_is_lying(suspect: Suspect) -> bool:
    return suspect.honesty < 4


def solve_with_dialogue(world: World, suspect: Entity, friend: Entity, clue: Entity) -> None:
    world.facts["talked"] = True
    friend.memes["encouragement"] += 1
    world.say(f'{friend.id} leaned close and whispered, "You can tell them. I will encourage you."')
    world.say(f'{suspect.id} took a breath and said, "{world.facts["question"]}"')
    if world.facts.get("shy"):
        world.say(f'The room grew quiet, and then {suspect.id} answered in a small but steady voice.')
    clue.meters["revealed"] = 1.0


def setup_scene(world: World, setting: Setting, hero: Entity, friend: Entity, host: Entity, item: Entity) -> None:
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"At {setting.place}, {hero.id} and {friend.id} were helping {host.id} set up for a little club show-and-tell."
    )
    world.say(
        f'Their friendship made the room feel calm, and everyone chatted in soft, careful dialogue while they looked for {item.label}.'
    )


def notice_missing(world: World, item: Entity, setting: Setting) -> None:
    item.meters["missing"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then {item.label} was gone. It had been sitting in a {setting.clue_spots[0]}, but now that spot was empty."
    )
    world.say('Someone asked, "Who saw it last?" and the little mystery began.')


def question_suspects(world: World, hero: Entity, friend: Entity, suspects: list[Entity]) -> None:
    for s in suspects:
        world.say(f'{s.id} said, "{s.attrs["alibi"]}"')
    world.say(
        f'{hero.id} frowned and said, "That does not fit." {friend.id} nodded and encouraged {hero.id} to keep listening.'
    )


def find_clue(world: World, clue: Entity, hunch: Hunch, detective: Entity) -> None:
    world.say(
        f'{detective.id} noticed {clue.label} near {clue.hiding_place}. It {clue.shine}, which matched the clue they needed.'
    )
    world.say(
        f'"That is the key," {detective.id} said. "It shows where the missing thing was moved."'
    )
    clue.meters["found"] = 1.0
    world.facts["solution"] = hunch.reveal


def reveal_solution(world: World, culprit: Entity, host: Entity, hero: Entity, friend: Entity, item: Entity) -> None:
    world.say(
        f'{hero.id} turned to {culprit.id} and said, "You took it to be helpful, but you should have told {host.id}."'
    )
    world.say(
        f'{culprit.id} looked down. Then {friend.id} encouraged {culprit.id} to speak honestly, and {culprit.id} admitted it.'
    )
    world.say(
        f'It turned out {culprit.id} had moved {item.label} to a safer shelf so nobody would knock it over.'
    )


def warm_ending(world: World, host: Entity, hero: Entity, friend: Entity, item: Entity) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    host.memes["relief"] += 1
    world.say(
        f"{host.id} smiled and thanked them all. The missing {item.label} was back in its place, and the room felt friendly again."
    )
    world.say(
        f'{hero.id} and {friend.id} left together, still talking, still listening, and still ready to encourage one another.'
    )


def tell(setting: Setting, item: ClueItem, suspect_cfg: Suspect, hunch: Hunch,
         hero_name: str, friend_name: str, host_name: str, shy_name: str) -> World:
    world = World()
    hero = world.add(Entity(hero_name, kind="character", type="boy", role="detective"))
    friend = world.add(Entity(friend_name, kind="character", type="girl", role="friend"))
    host = world.add(Entity(host_name, kind="character", type="woman", role="host", label="the host"))
    shy = world.add(Entity(shy_name, kind="character", type="boy", role="shy"))
    culprit = world.add(Entity(suspect_cfg.id, kind="character", type="girl", role="suspect"))
    clue = world.add(Entity(item.id, type="thing", label=item.label))
    world.facts["shy"] = shy
    world.facts["question"] = "Where did you move it?"
    setup_scene(world, setting, hero, friend, host, clue)
    world.para()
    notice_missing(world, clue, setting)
    world.para()
    question_suspects(world, hero, friend, [shy, culprit])
    if suspect_is_lying(suspect_cfg):
        world.say(f'{culprit.id} avoided eye contact, which made {hero.id} more certain there was a clue to find.')
    world.para()
    solve_with_dialogue(world, shy, friend, clue)
    find_clue(world, clue, hunch, hero)
    world.para()
    reveal_solution(world, culprit, host, hero, friend, clue)
    warm_ending(world, host, hero, friend, clue)
    world.facts.update(
        hero=hero, friend=friend, host=host, shy=shy, culprit=culprit,
        setting=setting, item=item, hunch=hunch, suspect_cfg=suspect_cfg,
        solved=True, talked=True
    )
    return world


SETTINGS = {
    "clubroom": Setting("clubroom", "the clubroom", ["shelf", "table", "basket"]),
    "library": Setting("library", "the library corner", ["desk", "cart", "window seat"]),
    "garden": Setting("garden", "the garden shed room", ["bench", "crate", "peg rack"]),
}

ITEMS = {
    "badge": ClueItem("badge", "a shiny badge", "shelf", "glint", {"badge", "shiny"}),
    "button": ClueItem("button", "a bright button", "basket", "glimmer", {"button", "small"}),
    "photo": ClueItem("photo", "a paper photo", "table", "gleamed in the light", {"photo", "paper"}),
}

SUSPECTS = {
    "nina": Suspect("Nina", "Nina", "I did not move it", honesty=3, alibi="I was by the window", tags={"lying"}),
    "omar": Suspect("Omar", "Omar", "I sorted the crayons", honesty=7, alibi="I was sorting crayons", tags={"truth"}),
    "piper": Suspect("Piper", "Piper", "I was helping the host", honesty=6, alibi="I was helping the host", tags={"truth"}),
}

HUNCHES = {
    "badge": Hunch("badge_hunch", "badge", "Nina", "the shiny badge had been tucked behind the shelf", {"badge"}),
    "button": Hunch("button_hunch", "button", "Omar", "the button had rolled into the basket", {"button"}),
    "photo": Hunch("photo_hunch", "photo", "Piper", "the paper photo had slipped under the table", {"photo"}),
}

HERO_NAMES = ["Leo", "Maya", "Ari", "Noa", "Sage", "Ivy"]
FRIEND_NAMES = ["Zoe", "Mina", "Rory", "Pia", "Eli", "June"]
HOST_NAMES = ["Parent", "Teacher", "Librarian"]
SHY_NAMES = ["Ben", "Tess", "Sam", "Luca"]

TRAITS = ["careful", "kind", "quiet", "patient", "brave"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    item: str
    suspect: str
    hunch: str
    hero: str
    friend: str
    host: str
    shy: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            if clue_needed_for(setting, item):
                for sus in SUSPECTS:
                    for huh in HUNCHES:
                        combos.append((sid, iid, sus))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld about friendship and encouragement.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--hunch", choices=HUNCHES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--host")
    ap.add_argument("--shy")
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
              and (args.item is None or c[1] == args.item)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid whodunit combination matches the given options.)")
    setting, item, suspect = rng.choice(sorted(combos))
    hunch = args.hunch or item
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    if friend == hero:
        friend = rng.choice([n for n in FRIEND_NAMES if n != hero])
    host = args.host or rng.choice(HOST_NAMES)
    shy = args.shy or rng.choice(SHY_NAMES)
    return StoryParams(setting, item, suspect, hunch, hero, friend, host, shy)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit story that includes the word "encourage" and features friendship and dialogue.',
        f"Tell a mystery story where {f['friend'].id} encourages {f['shy'].id} to speak, and the friends solve a missing {f['item'].label}.",
        f"Write a cozy whodunit set in {f['setting'].place} where talking things through leads to the answer.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, host, culprit = f["hero"], f["friend"], f["host"], f["culprit"]
    item, setting = f["item"], f["setting"]
    return [
        ("Who are the friends in the story?",
         f"{hero.id} and {friend.id} are the friends. They work together, listen carefully, and keep encouraging each other."),
        (f"What was missing?",
         f"{item.label} was missing from {setting.place}. The empty spot started the mystery."),
        (f"How did {friend.id} help?",
         f"{friend.id} encouraged the shy one to speak up and used calm dialogue to keep everyone talking. That helped the clue come out without anyone feeling scared."),
        (f"Who solved the whodunit?",
         f"{hero.id} solved it with help from {friend.id}. They followed the clue and learned what happened from honest conversation."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["item"].tags) | set(f["suspect_cfg"].tags)
    out = []
    if "shiny" in tags:
        out.append(("Why do shiny things catch attention?",
                    "Shiny things reflect light, so they stand out and are easy to notice. That is why a clue like a shiny badge can be spotted quickly."))
    if "lying" in tags:
        out.append(("Why can a lie make a mystery harder?",
                    "A lie hides the truth, so people may chase the wrong idea at first. Honest dialogue helps sort out what really happened."))
    out.append(("What does encourage mean?",
                "To encourage someone means to give them courage and help them feel braver. Kind words can help a nervous friend speak up."))
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("clubroom", "badge", "nina", "badge", "Leo", "Zoe", "Parent", "Sam"),
    StoryParams("library", "button", "omar", "button", "Maya", "Rory", "Teacher", "Ben"),
    StoryParams("garden", "photo", "piper", "photo", "Ari", "June", "Librarian", "Tess"),
]


def explain_rejection(setting: Setting, item: ClueItem) -> str:
    return f"(No story: {item.label} is not a good fit for {setting.place}; pick a clue that can hide there.)"


ASP_RULES = r"""
valid(S, I, U) :- setting(S), item(I), suspect(U), clue_needed(S, I).
outcome(solved) :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for uid in SUSPECTS:
        lines.append(asp.fact("suspect", uid))
    for sid, setting in SETTINGS.items():
        for spot in setting.clue_spots:
            lines.append(asp.fact("clue_spot", sid, spot))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("clue_needed", "clubroom" if item.hiding_place == "shelf" else "library" if item.hiding_place == "basket" else "garden", iid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, item=None, suspect=None, hunch=None, hero=None, friend=None, host=None, shy=None), random.Random(7)))
        with redirect_stdout(io.StringIO()):
            emit(sample)
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    if rc == 0:
        print("OK: ASP parity and smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item], SUSPECTS[params.suspect],
                 HUNCHES[params.hunch], params.hero, params.friend, params.host, params.shy)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
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
