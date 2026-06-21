#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/necessary_dome_bad_ending_reconciliation_whodunit.py
=====================================================================================

A small whodunit-style storyworld about a museum dome, a necessary clue, a bad
ending, and a reconciliation. The domain is intentionally tiny: a child or two,
a caretaker, a locked dome room, one necessary object, one suspicious object,
and a final reveal that repairs trust after a mistake has already caused harm.

The world is modeled with typed entities, physical meters, emotional memes, a
forward-chained causal engine, a reasonableness gate, and an ASP twin.

Run:
    python storyworlds/worlds/gpt-5.4-mini/necessary_dome_bad_ending_reconciliation_whodunit.py
    python storyworlds/worlds/gpt-5.4-mini/necessary_dome_bad_ending_reconciliation_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/necessary_dome_bad_ending_reconciliation_whodunit.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
class Setting:
    id: str
    place: str
    detail: str
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
    phrase: str
    necessary: bool
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
    phrase: str
    suspicious: bool
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
class Outcome:
    id: str
    sense: int
    damage: int
    text: str
    fail: str
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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    if world.get("dome_room").meters["disturbed"] >= THRESHOLD:
        sig = ("alarm",)
        if sig not in world.fired:
            world.fired.add(sig)
            for c in world.characters():
                c.memes["fear"] += 1
            out.append("__alarm__")
    return out


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    if world.get("dome").meters["broken"] >= THRESHOLD:
        sig = ("damage",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("museum").meters["damage"] += 1
            out.append("__damage__")
    return out


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm), Rule("damage", "physical", _r_damage)]


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


def necessary_clue(clue: Clue) -> bool:
    return clue.necessary


def sensible_outcomes() -> list[Outcome]:
    return [o for o in OUTCOMES.values() if o.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for clue_id, clue in CLUES.items():
            for suspect_id, suspect in SUSPECTS.items():
                if clue.necessary and suspect.suspicious:
                    combos.append((setting, clue_id, suspect_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    clue: str
    suspect: str
    outcome: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    keeper: str
    keeper_gender: str
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


def _do_misstep(world: World, clue: Clue, suspect: Suspect) -> None:
    world.get("dome_room").meters["disturbed"] += 1
    world.get("dome").meters["broken"] += 1
    world.get("detector").memes["certainty"] -= 1
    propagate(world, narrate=False)


def _predict(world: World, clue: Clue, suspect: Suspect) -> dict:
    sim = world.copy()
    _do_misstep(sim, clue, suspect)
    return {
        "disturbed": sim.get("dome_room").meters["disturbed"] >= THRESHOLD,
        "broken": sim.get("dome").meters["broken"] >= THRESHOLD,
        "damage": sim.get("museum").meters["damage"],
    }


def open_case(world: World, d: Entity, h: Entity, k: Entity, setting: Setting) -> None:
    world.say(
        f"On a quiet night, {d.id} and {h.id} entered {setting.place}. "
        f"{setting.detail}"
    )
    world.say(
        f'"This case is necessary," {d.id} said, because the old dome had a lock, '
        f'and somebody had left a note.'
    )


def inspect(world: World, d: Entity, clue: Clue, suspect: Suspect) -> None:
    d.memes["curiosity"] += 1
    world.say(
        f"{d.id} spotted {clue.phrase} beside the dome. That looked necessary, "
        f"because it was the only thing that matched the torn scrap of paper."
    )
    world.say(
        f'But {suspect.label} seemed suspicious, and {d.id} could not ignore it. '
        f'"The clues do not line up yet," {d.pronoun()} whispered.'
    )


def warn(world: World, h: Entity, d: Entity, clue: Clue, suspect: Suspect, keeper: Entity) -> None:
    pred = _predict(world, clue, suspect)
    h.memes["concern"] += 1
    world.facts["predicted_damage"] = pred["damage"]
    world.say(
        f'{h.id} frowned. "{d.id}, wait. If we rush this, the dome could break, '
        f'and {keeper.label_word} will be hurt by the mess."'
    )


def misstep(world: World, d: Entity, clue: Clue, suspect: Suspect) -> None:
    d.memes["defiance"] += 1
    world.say(
        f'{d.id} ignored the warning and touched {clue.label} anyway. '
        f'The wrong latch clicked. The room went still.'
    )


def reveal(world: World, keeper: Entity, d: Entity, suspect: Suspect, outcome: Outcome) -> None:
    if outcome.id == "bad":
        body = outcome.fail
    else:
        body = outcome.text
    world.say(
        f"{keeper.label_word.capitalize()} came running. {body} "
        f"The real answer was hidden in plain sight."
    )
    world.say(
        f"At last {d.id} understood that {suspect.label} was not the culprit; "
        f"the clue had been necessary after all."
    )


def bad_ending(world: World, keeper: Entity, d: Entity, h: Entity) -> None:
    for kid in (d, h):
        kid.memes["shame"] += 1
    world.say(
        f"The dome cracked with a sharp little crack, and the museum lights flickered. "
        f"The case had gone wrong."
    )
    world.say(
        f"Nobody was badly hurt, but the old dome was ruined, and {keeper.label_word} "
        f"looked very sad."
    )


def reconciliation(world: World, keeper: Entity, d: Entity, h: Entity) -> None:
    for kid in (d, h):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
    world.say(
        f"Then {d.id} stepped closer and said sorry. {h.id} nodded and said sorry too. "
        f"{keeper.label_word.capitalize()} did not scold them; {keeper.pronoun()} "
        f"just hugged them both."
    )
    world.say(
        f'"We can fix what we can," {keeper.id} said softly. "And the next mystery '
        f"will need better care."'
    )
    world.say(
        f"So they swept up the broken glass, closed the hall, and walked out together "
        f"under the moonlit dome, a little wiser and still a family."
    )


SETTINGS = {
    "museum": Setting(
        id="museum",
        place="the museum hall",
        detail="Above them rose the glass dome, pale as a pearl."
    ),
    "gallery": Setting(
        id="gallery",
        place="the old gallery",
        detail="The painted ceiling curved like a shell over the exhibits."
    ),
}

CLUES = {
    "key": Clue(
        id="key",
        label="key",
        phrase="a brass key",
        necessary=True,
        tags={"key", "necessary"},
    ),
    "note": Clue(
        id="note",
        label="note",
        phrase="a folded note",
        necessary=True,
        tags={"note", "necessary"},
    ),
    "ribbon": Clue(
        id="ribbon",
        label="ribbon",
        phrase="a bright ribbon",
        necessary=False,
        tags={"ribbon"},
    ),
}

SUSPECTS = {
    "janitor": Suspect(
        id="janitor",
        label="the janitor",
        phrase="the janitor by the stairs",
        suspicious=True,
        tags={"janitor", "suspect"},
    ),
    "guide": Suspect(
        id="guide",
        label="the guide",
        phrase="the guide with the lantern",
        suspicious=True,
        tags={"guide", "suspect"},
    ),
    "cat": Suspect(
        id="cat",
        label="the cat",
        phrase="a sleepy cat",
        suspicious=False,
        tags={"cat"},
    ),
}

OUTCOMES = {
    "bad": Outcome(
        id="bad",
        sense=3,
        damage=2,
        text="The keeper arrived too late, and the dome shattered into glittering pieces.",
        fail="The keeper arrived too late, and the clues scattered under the broken glass.",
        tags={"bad", "damage"},
    ),
    "repair": Outcome(
        id="repair",
        sense=3,
        damage=1,
        text="The keeper slowed the panic, gathered the pieces, and kept the damage small.",
        fail="The keeper slowed the panic, but the damage had already begun.",
        tags={"repair", "reconciliation"},
    ),
    "water": Outcome(
        id="water",
        sense=1,
        damage=1,
        text="Someone splashed water over the floor, which only made the trail harder to read.",
        fail="Someone splashed water over the floor, and the clue disappeared in the mess.",
        tags={"water"},
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Ivy", "Lena", "Rose", "Ada"]
BOY_NAMES = ["Theo", "Milo", "Eli", "Noah", "Finn", "Owen"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with a dome, a necessary clue, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--outcome", choices=OUTCOMES)
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--keeper")
    ap.add_argument("--keeper-gender", choices=["girl", "boy"])
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
    if args.clue and not CLUES[args.clue].necessary:
        raise StoryError("That clue is not necessary enough for this whodunit.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, suspect = rng.choice(sorted(combos))
    outcome = args.outcome or rng.choice(sorted(OUTCOMES))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if detective_gender == "girl" else "girl")
    keeper_gender = args.keeper_gender or rng.choice(["girl", "boy"])
    detective = args.detective or rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != detective])
    keeper = args.keeper or rng.choice(GIRL_NAMES if keeper_gender == "girl" else BOY_NAMES)
    return StoryParams(
        setting=setting,
        clue=clue,
        suspect=suspect,
        outcome=outcome,
        detective=detective,
        detective_gender=detective_gender,
        helper=helper,
        helper_gender=helper_gender,
        keeper=keeper,
        keeper_gender=keeper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.clue not in CLUES or params.suspect not in SUSPECTS or params.outcome not in OUTCOMES:
        raise StoryError("Invalid parameters.")
    world = World()
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    suspect = SUSPECTS[params.suspect]
    outcome = OUTCOMES[params.outcome]
    detective = world.add(Entity(id=params.detective, kind="character", type=params.detective_gender, role="detective"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    keeper = world.add(Entity(id=params.keeper, kind="character", type=params.keeper_gender, role="keeper", label="the keeper"))
    world.add(Entity(id="museum", type="place", label="the museum"))
    world.add(Entity(id="dome_room", type="room", label="the dome room"))
    dome = world.add(Entity(id="dome", type="object", label="the dome"))
    world.add(Entity(id="detector", type="thing", label="the detector"))

    open_case(world, detective, helper, keeper, setting)
    world.para()
    inspect(world, detective, clue, suspect)
    warn(world, helper, detective, clue, suspect, keeper)
    world.para()
    misstep(world, detective, clue, suspect)
    reveal(world, keeper, detective, suspect, outcome)
    world.para()
    bad_ending(world, keeper, detective, helper)
    reconciliation(world, keeper, detective, helper)

    world.facts.update(
        setting=setting,
        clue=clue,
        suspect=suspect,
        outcome=outcome,
        detective=detective,
        helper=helper,
        keeper=keeper,
        dome=dome,
        bad=True,
        reconciled=True,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit story that includes the word "{f["clue"].label}" and the word "necessary".',
        f"Tell a short mystery where {f['detective'].id} follows a necessary clue near a dome, but gets the ending wrong and then makes peace afterward.",
        f"Write a child-friendly detective story with a bad ending first, then reconciliation, and let the dome matter to the plot.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    d, h, k = f["detective"], f["helper"], f["keeper"]
    clue, suspect = f["clue"], f["suspect"]
    qa = [
        ("Who is the story about?",
         f"It is about {d.id}, {h.id}, and {k.label_word}. They are the people who try to solve the mystery under the dome."),
        ("What clue was necessary?",
         f"{clue.phrase} was necessary. It was the one clue that matched the torn note and helped point the story in the right direction."),
        ("What looked suspicious?",
         f"{suspect.label} looked suspicious at first. That is why {d.id} kept watching carefully instead of deciding too soon."),
        ("What went wrong?",
         "The detective rushed the case and made the dome break. The bad ending happens because the wrong move caused damage before anyone could fix it."),
        ("How did the story end after the bad part?",
         f"{d.id} and {h.id} said sorry, and {k.label_word} forgave them. That reconciliation let everyone leave together, even though the dome had already been ruined."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["clue"].tags) | set(f["suspect"].tags) | set(f["outcome"].tags)
    if f.get("bad"):
        tags.add("damage")
    if f.get("reconciled"):
        tags.add("reconciliation")
    qa = []
    if "necessary" in tags:
        qa.append(("What does necessary mean?",
                   "Necessary means something is needed and important. If it is necessary, the story depends on it."))

    if "damage" in tags:
        qa.append(("What is damage?",
                   "Damage is harm done to something. It can mean a crack, a break, or anything that makes an object less whole."))
    if "reconciliation" in tags:
        qa.append(("What is reconciliation?",
                   "Reconciliation is when people make peace after a problem. They apologize, listen, and choose to be kind again."))
    if "cat" in tags:
        qa.append(("Are cats usually suspicious?",
                   "Not usually. A cat can look mysterious in a story, but that does not mean it caused the problem."))
    return qa


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def valid_asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show valid/3.\n#show outcome/1.\n"


def asp_facts() -> str:
    import asp
    out = []
    for sid in SETTINGS:
        out.append(asp.fact("setting", sid))
    for cid, c in CLUES.items():
        out.append(asp.fact("clue", cid))
        if c.necessary:
            out.append(asp.fact("necessary", cid))
    for sid, s in SUSPECTS.items():
        out.append(asp.fact("suspect", sid))
        if s.suspicious:
            out.append(asp.fact("suspicious", sid))
    for oid, o in OUTCOMES.items():
        out.append(asp.fact("outcome_cfg", oid))
        out.append(asp.fact("sense", oid, o.sense))
    out.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(out)


ASP_RULES = r"""
valid(S, C, U) :- setting(S), clue(C), suspect(U), necessary(C), suspicious(U).
ok_outcome(O) :- outcome_cfg(O), sense(O, V), sense_min(M), V >= M.
"""


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(f"{asp_facts()}\n{ASP_RULES}\n#show valid/3.\n")
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, clue=None, suspect=None, outcome=None,
            detective=None, detective_gender=None, helper=None, helper_gender=None,
            keeper=None, keeper_gender=None
        ), random.Random(7)))
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"MISMATCH: smoke test failed: {exc}")
    return rc


def explain_rejection() -> str:
    return "(No story: this combination is not a necessary clue mystery.)"


def build_names(gender: str, rng: random.Random, avoid: str = "") -> str:
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool)


def generate_params_seeded(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="museum", clue="key", suspect="janitor", outcome="bad",
                detective="Mina", detective_gender="girl", helper="Theo", helper_gender="boy",
                keeper="Nora", keeper_gender="girl"),
    StoryParams(setting="gallery", clue="note", suspect="guide", outcome="repair",
                detective="Eli", detective_gender="boy", helper="Ivy", helper_gender="girl",
                keeper="Rose", keeper_gender="girl"),
    StoryParams(setting="museum", clue="note", suspect="cat", outcome="bad",
                detective="Ada", detective_gender="girl", helper="Owen", helper_gender="boy",
                keeper="Lena", keeper_gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(valid_asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, clue, suspect) combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        if args.all:
            p = sample.params
            header = f"### {p.detective}: {p.clue} near the dome ({p.setting}, {p.outcome})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, suspect = rng.choice(sorted(combos))
    outcome = args.outcome or rng.choice(sorted(OUTCOMES))
    dg = args.detective_gender or rng.choice(["girl", "boy"])
    hg = args.helper_gender or ("boy" if dg == "girl" else "girl")
    kg = args.keeper_gender or rng.choice(["girl", "boy"])
    detective = args.detective or build_names(dg, rng)
    helper = args.helper or build_names(hg, rng, avoid=detective)
    keeper = args.keeper or build_names(kg, rng, avoid=detective)
    return StoryParams(
        setting=setting, clue=clue, suspect=suspect, outcome=outcome,
        detective=detective, detective_gender=dg,
        helper=helper, helper_gender=hg,
        keeper=keeper, keeper_gender=kg,
    )


def story_qa(_: World) -> list[tuple[str, str]]:
    return []


def world_knowledge_qa(_: World) -> list[tuple[str, str]]:
    return []


def generation_prompts(_: World) -> list[str]:
    return []
