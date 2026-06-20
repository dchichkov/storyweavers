#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hunt_technic_curiosity_whodunit.py
=================================================================

A small whodunit-style storyworld where a curious child follows a tiny hunt for
a missing object and solves the mystery by using a simple technic: careful
observing, comparing clues, and testing one likely path before jumping to a
conclusion.

The world is deliberately narrow: one small setting, one missing thing, a few
possible suspects, and one revealing technic. The prose stays child-facing and
state-driven: curiosity rises, clues accumulate, a false lead gets checked, and
the ending proves who moved the object and why.

Supported CLI:
    -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
class Place:
    id: str
    label: str
    hiding_spots: list[str]
    surfaces: list[str]
    clues: list[str]

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
class MissingThing:
    id: str
    label: str
    usual_spot: str
    easy_to_move: bool = True
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
    motive: str
    likely_spot: str
    innocent_if: str
    truth_tell: str
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
class Technic:
    id: str
    label: str
    method: str
    reveal: str
    confidence: int
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
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


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["curiosity"] < THRESHOLD:
            continue
        sig = ("curiosity", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["focus"] += 1
        out.append("__curious__")
    return out


def _r_clue_chain(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    if detective.meters["clues"] < 2:
        return out
    sig = ("chain", "detective")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["certainty"] += 1
    out.append("__chain__")
    return out


CAUSAL_RULES = [Rule("curiosity", _r_curiosity), Rule("clue_chain", _r_clue_chain)]


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


def valid_combo(place: Place, thing: MissingThing, suspect: Suspect) -> bool:
    return thing.usual_spot in place.hiding_spots and suspect.likely_spot in place.surfaces


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for tid, thing in MISSING.items():
            for sid, suspect in SUSPECTS.items():
                if valid_combo(place, thing, suspect):
                    out.append((pid, tid, sid))
    return out


def _find_note(world: World, place: Place, thing: MissingThing) -> None:
    world.say(
        f"That morning, {world.get('detective').id} noticed {thing.label} was gone. "
        f"The hunt began in {place.label}, where every shelf and corner felt like it might hide a secret."
    )
    world.get("detective").memes["curiosity"] += 1


def _ask_and_listen(world: World, detective: Entity, friend: Entity, suspect: Suspect) -> None:
    world.say(
        f'{detective.id} frowned and said, "If I follow the wrong clue, I will just make a bigger mess." '
        f'{friend.id} pointed to the crumbs by the chair and said, "Try the technic we learned: look, compare, then test."'
    )
    detective.memes["curiosity"] += 1
    detective.meters["clues"] += 1
    detective.meters["clues"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{detective.id} liked the technic. It was not a wild chase; it was a careful hunt for facts."
    )


def _check_false_lead(world: World, detective: Entity, place: Place, suspect: Suspect) -> None:
    world.say(
        f"First {detective.id} checked {suspect.likely_spot}, because it looked suspicious."
    )
    if suspect.innocent_if == "empty":
        world.say(
            f"But the spot was empty, and the clue did not fit. That was one mystery solved, and one mystery still waiting."
        )
    else:
        world.say(
            f"But the clue told a different story. {suspect.label} was not the one who moved it."
        )
    detective.meters["clues"] += 1
    propagate(world, narrate=False)


def _reveal(world: World, detective: Entity, suspect: Suspect, thing: MissingThing, technic: Technic) -> None:
    detective.meters["clues"] += 1
    detective.memes["certainty"] += 1
    world.say(
        f"Then the last clue clicked into place. Using the {technic.label}, {detective.id} saw that the trail led to {suspect.likely_spot}, not because {suspect.label} meant trouble, but because {suspect.motive}."
    )
    world.say(
        f'The mystery was solved: {suspect.label} had moved {thing.label} to {suspect.likely_spot}, and {suspect.truth_tell}.'
    )
    world.say(
        f"{detective.id} smiled at the neat ending image: the missing {thing.label} was back where it belonged, and the hunt had turned into a tidy answer."
    )


def tell(place: Place, thing: MissingThing, suspect: Suspect, technic: Technic,
         detective_name: str = "Mina", detective_gender: str = "girl",
         friend_name: str = "Ben", friend_gender: str = "boy") -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    adult = world.add(Entity(id="Adult", kind="character", type="mother", role="adult", label="the parent"))
    world.add(Entity(id="room", type="room", label=place.label))
    detective.memes["curiosity"] = 2.0
    friend.memes["curiosity"] = 1.0
    world.facts["place"] = place
    world.facts["thing"] = thing
    world.facts["suspect"] = suspect
    world.facts["technic"] = technic
    world.facts["adult"] = adult

    world.say(
        f"Curiosity made {detective.id} start the hunt in {place.label}. {detective.id} had lost {thing.label}, and every little detail felt important."
    )
    world.say(
        f"{friend.id} stayed close. {friend.id} knew this was a whodunit, and the answer would come from calm eyes, not noisy guesses."
    )

    world.para()
    _find_note(world, place, thing)
    _ask_and_listen(world, detective, friend, suspect)

    world.para()
    world.say(
        f'{detective.id} tried the technic: {technic.method}.'
    )
    _check_false_lead(world, detective, place, suspect)

    world.para()
    _reveal(world, detective, suspect, thing, technic)
    adult.memes["pride"] += 1
    world.say(
        f"{adult.label_word.capitalize()} nodded with a warm grin, glad the children had used curiosity kindly and solved the small puzzle without fuss."
    )

    world.facts.update(
        detective=detective,
        friend=friend,
        adult=adult,
        outcome="solved",
        clues=int(detective.meters["clues"]),
    )
    return world


PLACES = {
    "library": Place("library", "the little library", ["reading nook", "back shelf", "riddle corner"], ["table", "chair", "shelf"], ["crumbs", "paper strip", "tiny footprint"]),
    "garden": Place("garden", "the garden shed", ["tool box", "flower pot", "bench"], ["bench", "step", "bucket"], ["soil mark", "leaf", "string"]),
    "playroom": Place("playroom", "the playroom", ["toy bin", "pillow fort", "game shelf"], ["rug", "stool", "crate"], ["block trail", "doll shoe", "pencil"]),
}

MISSING = {
    "compass": MissingThing("compass", "the little compass", "the map table", tags={"hunt", "technic"}),
    "cookie": MissingThing("cookie", "the star-shaped cookie", "the plate tray", tags={"hunt"}),
    "pencil": MissingThing("pencil", "the blue pencil", "the cup by the window", tags={"technic"}),
}

SUSPECTS = {
    "sister": Suspect("sister", "Ava", "she was tidying the map corner", "the basket by the sofa", "empty", "she had only moved the basket", tags={"curiosity"}),
    "cat": Suspect("cat", "the cat", "it liked warm hiding spots", "under the chair", "empty", "it had only napped there", tags={"hunt"}),
    "brother": Suspect("brother", "Noah", "he borrowed it for a project", "the work table", "empty", "he had borrowed it, then put it back", tags={"technic"}),
}

TECHNICS = {
    "compare": Technic("compare", "compare-the-clues technic", "look at the clues, then match them against the right place", "the path did not match the basket, but it did match the work table", 3, tags={"technic"}),
    "measure": Technic("measure", "measure-and-match technic", "measure the clue, then check whether it fits the hiding place", "the trail was too short for the basket, so the basket was not the answer", 2, tags={"technic"}),
    "follow": Technic("follow", "follow-the-trail technic", "follow the crumbs until they stop, then look for the hand that moved the thing", "the crumbs ended at the work table, where someone had been helping", 4, tags={"hunt", "technic"}),
}

GIRL_NAMES = ["Mina", "Ava", "Lily", "Zoe", "Nora"]
BOY_NAMES = ["Ben", "Noah", "Eli", "Theo", "Max"]


@dataclass
@dataclass
class StoryParams:
    place: str
    thing: str
    suspect: str
    technic: str
    detective: str
    detective_gender: str
    friend: str
    friend_gender: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit-style story for a small child that includes the words "hunt" and "technic".',
        f"Tell a curious mystery where {f['detective'].id} searches for {f['thing'].label} in {f['place'].label} and solves it with a careful technic.",
        f'Write a short story about a child who uses curiosity to hunt for a missing thing and ends with a clear answer.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    d = f["detective"]
    s = f["suspect"]
    t = f["thing"]
    tech = f["technic"]
    return [
        ("What kind of story is this?",
         "It is a small whodunit story. A curious child follows clues, checks a false lead, and finds out who moved the missing thing."),
        (f"What was {d.id} looking for?",
         f"{d.id} was looking for {t.label}. The whole hunt began because it was missing from its usual spot."),
        (f"What technic did {d.id} use?",
         f"{d.id} used the {tech.label}. That meant looking carefully, comparing clues, and testing the most likely place instead of guessing."),
        (f"Who moved {t.label}?",
         f"{s.label} moved {t.label} to {s.likely_spot}. It was not a bad trick, just a small helpful move that looked suspicious at first."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is curiosity?",
         "Curiosity is the feeling that makes you want to know more. It helps you notice clues and ask good questions."),
        ("What is a whodunit?",
         "A whodunit is a mystery story where the reader tries to figure out who did it. The fun is in following the clues to the answer."),
        ("What does the word hunt mean?",
         "A hunt is a careful search for something that is missing or hard to find. You keep looking until you find it or solve the trail."),
        ("What is a technic?",
         "A technic is a simple way of doing something. In a mystery, a technic can mean a careful method for checking clues."),
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("library", "compass", "sister", "compare", "Mina", "girl", "Ben", "boy"),
    StoryParams("garden", "cookie", "cat", "follow", "Ava", "girl", "Noah", "boy"),
    StoryParams("playroom", "pencil", "brother", "measure", "Lily", "girl", "Eli", "boy"),
]


def valid_params(p: StoryParams) -> bool:
    return (p.place in PLACES and p.thing in MISSING and p.suspect in SUSPECTS and p.technic in TECHNICS
            and valid_combo(PLACES[p.place], MISSING[p.thing], SUSPECTS[p.suspect]))


def explain_rejection(place: Place, thing: MissingThing, suspect: Suspect) -> str:
    return f"(No story: {thing.label} does not fit a good whodunit in {place.label} with {suspect.label}; the hunt needs a real clue trail.)"


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in MISSING:
        lines.append(asp.fact("thing", tid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    for pid, place in PLACES.items():
        for spot in place.hiding_spots:
            lines.append(asp.fact("hiding_spot", pid, spot))
    for tid, thing in MISSING.items():
        lines.append(asp.fact("usual_spot", tid, thing.usual_spot))
    for sid, sus in SUSPECTS.items():
        lines.append(asp.fact("likely_spot", sid, sus.likely_spot))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,S) :- place(P), thing(T), suspect(S), usual_spot(T,U), hiding_spot(P,U), likely_spot(S,L), hiding_spot(P,L).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos.")
        rc = 1
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Curious whodunit storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--thing", choices=MISSING)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--technic", choices=TECHNICS)
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
              if (args.place is None or c[0] == args.place)
              and (args.thing is None or c[1] == args.thing)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, thing, suspect = rng.choice(sorted(combos))
    technic = args.technic or rng.choice(sorted(TECHNICS))
    dg = args.detective_gender or "girl"
    fg = args.friend_gender or "boy"
    detective = args.detective or rng.choice(GIRL_NAMES if dg == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (BOY_NAMES if fg == "boy" else GIRL_NAMES) if n != detective])
    return StoryParams(place, thing, suspect, technic, detective, dg, friend, fg)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MISSING[params.thing], SUSPECTS[params.suspect], TECHNICS[params.technic],
                 params.detective, params.detective_gender, params.friend, params.friend_gender)
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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for c in asp_valid_combos():
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
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
