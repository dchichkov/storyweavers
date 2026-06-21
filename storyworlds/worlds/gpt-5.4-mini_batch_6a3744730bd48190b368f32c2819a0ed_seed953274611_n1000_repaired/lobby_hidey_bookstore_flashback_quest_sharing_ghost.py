#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lobby_hidey_bookstore_flashback_quest_sharing_ghost.py
========================================================================================

A standalone story world for a small ghost-story set in a bookstore lobby.

Premise:
- A child in a bookstore notices a shy ghost hiding in a nook.
- A tiny quest begins in the lobby and among the shelves.
- A flashback reveals why the ghost is there.
- Sharing a book, a lamp, or a story helps everyone feel brave.
- The ending proves something changed: the ghost is no longer lonely, and the
  child has a solved mystery plus a calmer, brighter bookstore.

This script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- a Python reasonableness gate plus inline ASP twin
- seeded parameter resolution
- story, prompts, story QA, and world-knowledge QA
- --verify smoke-tests ordinary generation and parity
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
    lobby: str
    hidey: str
    shelves: str
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
class GhostCue:
    id: str
    tone: str
    flashback_line: str
    want: str
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
class Quest:
    id: str
    goal: str
    clue: str
    finish: str
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
class ShareThing:
    id: str
    label: str
    phrase: str
    benefit: str
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
class StoryParams:
    setting: str
    cue: str
    quest: str
    sharing: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_lonely(world: World) -> list[str]:
    out = []
    ghost = world.entities.get("ghost")
    if not ghost or ghost.memes.get("lonely", 0.0) < THRESHOLD:
        return out
    if ("lonely",) in world.fired:
        return out
    world.fired.add(("lonely",))
    world.get("child").memes["worry"] = world.get("child").memes.get("worry", 0.0) + 1
    out.append("__lonely__")
    return out


def _r_share(world: World) -> list[str]:
    out = []
    ghost = world.entities.get("ghost")
    child = world.entities.get("child")
    if not ghost or not child:
        return out
    if child.memes.get("sharing", 0.0) < THRESHOLD or ghost.memes.get("trust", 0.0) >= THRESHOLD:
        return out
    if ("share",) in world.fired:
        return out
    world.fired.add(("share",))
    ghost.memes["trust"] = ghost.memes.get("trust", 0.0) + 1
    ghost.memes["lonely"] = 0.0
    child.memes["brave"] = child.memes.get("brave", 0.0) + 1
    out.append("__share__")
    return out


def _r_flashback(world: World) -> list[str]:
    out = []
    ghost = world.entities.get("ghost")
    if not ghost or ghost.memes.get("flashback", 0.0) < THRESHOLD:
        return out
    if ("flashback",) in world.fired:
        return out
    world.fired.add(("flashback",))
    world.facts["flashback_seen"] = True
    out.append("__flashback__")
    return out


CAUSAL_RULES = [Rule("lonely", _r_lonely), Rule("share", _r_share), Rule("flashback", _r_flashback)]


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


def reasonableness_ok(setting: Setting, cue: GhostCue, quest: Quest, sharing: ShareThing) -> bool:
    return setting.id == "bookstore" and "ghost" in cue.tags and "quest" in quest.tags and "share" in sharing.tags


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, c, q, sh) for s in SETTINGS for c in CUES for q in QUESTS for sh in SHARES if reasonableness_ok(SETTINGS[s], CUES[c], QUESTS[q], SHARES[sh])]


def _do_flashback(world: World, cue: GhostCue) -> None:
    ghost = world.get("ghost")
    ghost.memes["flashback"] = ghost.memes.get("flashback", 0.0) + 1
    world.say(cue.flashback_line)


def _do_share(world: World, share: ShareThing) -> None:
    child = world.get("child")
    ghost = world.get("ghost")
    child.memes["sharing"] = child.memes.get("sharing", 0.0) + 1
    world.say(f"{child.id} offered {share.phrase}, and {share.benefit}.")
    propagate(world, narrate=False)
    if ghost.memes.get("trust", 0.0) >= THRESHOLD:
        world.say(f"The ghost leaned closer, and the air in the lobby felt warmer.")
    else:
        world.say(f"The ghost still hid in the shadows, peeking through the shelves.")


def tell(setting: Setting, cue: GhostCue, quest: Quest, sharing: ShareThing,
         child_name: str = "Mia", child_gender: str = "girl",
         adult_name: str = "Mr. Green", adult_gender: str = "man") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult", label="the bookseller"))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", role="mystery", label="the ghost"))

    ghost.memes["lonely"] = 1.0
    ghost.memes["trust"] = 0.0
    ghost.memes["flashback"] = 0.0
    child.memes["curious"] = 1.0
    child.memes["brave"] = 0.0

    world.say(
        f"In the bookstore lobby, {child.id} heard a soft whisper from a hidey nook near the shelves. "
        f"{setting.lobby} held the hush of turned pages, and {setting.hidey} looked like a secret."
    )
    world.say(
        f'"Something is there," {child.id} said, and {adult.label_word} pointed toward {setting.shelves}. '
        f'The tiny quest was to find out who was hiding and why.'
    )

    world.para()
    _do_flashback(world, cue)
    world.say(
        f'The whisper pulled a flashback from the dark: {cue.flashback_line.lower()} '
        f'That memory explained why the ghost kept close to the shelves.'
    )
    world.say(f"The quest now had a clue: {quest.clue}.")

    world.para()
    world.say(
        f'{child.id} looked at the lonely ghost and remembered that some things are easier when shared. '
        f'They held out {sharing.phrase}.'
    )
    _do_share(world, sharing)
    world.say(
        f'{quest.finish.capitalize()}, and {adult.label_word} smiled because the mystery was finally answered.'
    )

    ghost.memes["lonely"] = 0.0
    ghost.memes["home"] = 1.0
    child.memes["happy"] = 1.0

    world.facts.update(
        child=child,
        adult=adult,
        ghost=ghost,
        setting=setting,
        cue=cue,
        quest=quest,
        sharing=sharing,
        resolved=True,
        flashback_seen=True,
        shared=True,
    )
    return world


SETTINGS = {
    "bookstore": Setting(
        id="bookstore",
        place="bookstore",
        lobby="the lobby",
        hidey="a hidey nook behind a tall shelf",
        shelves="the quiet shelves",
        tags={"bookstore", "lobby", "hidey"},
    )
}

CUES = {
    "flashback": GhostCue(
        id="flashback",
        tone="soft and misty",
        flashback_line="Years ago, the ghost had hidden a favorite story in the lobby during a storm",
        want="to find the lost story again",
        tags={"ghost", "flashback", "book"},
    )
}

QUESTS = {
    "quest": Quest(
        id="quest",
        goal="solve the little mystery",
        clue="the ghost was searching for a book it had tucked away long ago",
        finish="the ghost found its old storybook tucked behind a shelf",
        tags={"quest", "mystery"},
    )
}

SHARES = {
    "sharing": ShareThing(
        id="sharing",
        label="sharing",
        phrase="a warm flashlight and the library card with the little map",
        benefit="that gave the ghost enough courage to step out of the hidey nook",
        tags={"sharing", "share"},
    )
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Ben", "Theo", "Noah", "Max", "Eli"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a child-friendly ghost story set in a bookstore lobby, with a hidden nook and a gentle mystery.",
        f"Tell a story where {f['child'].id} meets a shy ghost, learns a flashback, and shares something kind to help.",
        "Write a short quest story that uses the words lobby and hidey, and ends with the ghost feeling less lonely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    ghost: Entity = f["ghost"]
    setting: Setting = f["setting"]
    cue: GhostCue = f["cue"]
    quest: Quest = f["quest"]
    sharing: ShareThing = f["sharing"]
    return [
        QAItem(
            question="Where does the story take place?",
            answer=f"It takes place in a bookstore, especially the lobby and the quiet shelves. The hidey nook makes the setting feel a little spooky but still safe.",
        ),
        QAItem(
            question="What was the child trying to do?",
            answer=f"{child.id} was trying to solve a tiny quest and find out why the ghost was hiding. The clue led from the lobby into a gentle mystery about an old storybook.",
        ),
        QAItem(
            question="What did the flashback show?",
            answer=f"The flashback showed that the ghost had hidden a favorite story years ago during a storm. That memory explained why it stayed near the shelves and the hidey nook.",
        ),
        QAItem(
            question="How did sharing help?",
            answer=f"{child.id} shared {sharing.phrase}, and that made the ghost feel safer. Sharing turned the spooky moment into a friendly one, so the ghost could come out and finish the quest.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the ghost finding its old storybook and no longer feeling lonely. {child.id} and the bookseller were glad the mystery in the lobby had been solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bookstore?",
            answer="A bookstore is a place where people go to find books, read books, and buy books to take home.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory that jumps back to an earlier time. Stories use it to explain something that happened before the main scene.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something with you. It can help people feel kinder and less alone.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a little search or mission to find something, solve a mystery, or help someone.",
        ),
        QAItem(
            question="Why can a lobby matter in a story?",
            answer="A lobby is often the first room people enter, so it can be a place where a story starts and a mystery appears.",
        ),
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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="bookstore", cue="flashback", quest="quest", sharing="sharing", child_name="Mia", child_gender="girl", adult_name="Mr. Green", adult_gender="man"),
    StoryParams(setting="bookstore", cue="flashback", quest="quest", sharing="sharing", child_name="Noah", child_gender="boy", adult_name="Ms. Lane", adult_gender="woman"),
]


ASP_RULES = r"""
bookstore_setting(S) :- setting(S), S = bookstore.
valid(S, C, Q, H) :- bookstore_setting(S), cue(C), quest(Q), share(H).
lonely(g) :- ghost(g), not trust(g).
trust(g) :- share_event, ghost(g).
flashback_seen :- cue(flashback).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CUES:
        lines.append(asp.fact("cue", cid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for hid in SHARES:
        lines.append(asp.fact("share", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH between clingo and Python valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, cue=None, quest=None, sharing=None, child_name=None, child_gender=None, adult_name=None, adult_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: ordinary story generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world in a bookstore lobby.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cue", choices=CUES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--sharing", choices=SHARES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult-name")
    ap.add_argument("--adult-gender", choices=["woman", "man"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    cue = args.cue or rng.choice(list(CUES))
    quest = args.quest or rng.choice(list(QUESTS))
    sharing = args.sharing or rng.choice(list(SHARES))
    if setting not in SETTINGS or cue not in CUES or quest not in QUESTS or sharing not in SHARES:
        raise StoryError("Invalid lookup key.")
    if not reasonableness_ok(SETTINGS[setting], CUES[cue], QUESTS[quest], SHARES[sharing]):
        raise StoryError("This story needs the bookstore, a flashback, a quest, and sharing.")
    gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    adult_name = args.adult_name or (rng.choice(["Ms. Lane", "Mr. Green", "Aunt June", "Uncle Ray"]))
    return StoryParams(setting=setting, cue=cue, quest=quest, sharing=sharing, child_name=child_name, child_gender=gender, adult_name=adult_name, adult_gender=adult_gender)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.cue not in CUES or params.quest not in QUESTS or params.sharing not in SHARES:
        raise StoryError("Unknown parameter value.")
    if not reasonableness_ok(SETTINGS[params.setting], CUES[params.cue], QUESTS[params.quest], SHARES[params.sharing]):
        raise StoryError("This combination does not make a coherent ghost story.")
    world = tell(SETTINGS[params.setting], CUES[params.cue], QUESTS[params.quest], SHARES[params.sharing], params.child_name, params.child_gender, params.adult_name, params.adult_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/4.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            sample = generate(p)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
