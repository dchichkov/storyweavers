#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sound_cramp_bad_ending_whodunit.py
===================================================================

A standalone story world for a tiny whodunit: a child hears a strange sound,
gets a cramp while investigating, and the mystery ends badly. The domain keeps
the story small and concrete, but the simulated state still drives the prose:
clues accumulate, suspicion shifts, the wrong choice makes things worse, and the
ending image proves the loss.

This world supports:
- normal random generation
- -n, --all, --seed
- --trace, --qa, --json
- --asp, --verify, --show-asp

The stories are intentionally bad endings in a whodunit frame: the mystery is
not solved in time, the culprit gets away, and the final scene shows what was
lost or left undone.
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
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    room_word: str
    night_word: str
    shadow_word: str

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
    innocent_hint: str
    guilty_hint: str
    can_make_sound: bool = True

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
class Clue:
    id: str
    label: str
    found_text: str
    weight: int
    points_to: str

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
class Hazard:
    id: str
    label: str
    type: str
    makes_sound: bool = False
    can_cause_cramp: bool = False
    hidden: bool = False

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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


def _r_sound(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["noise"] < THRESHOLD:
            continue
        sig = ("sound", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "detective" in world.entities:
            world.get("detective").memes["curiosity"] += 1
        out.append("__sound__")
    return out


def _r_cramp(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["strain"] < THRESHOLD:
            continue
        sig = ("cramp", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["pain"] += 1
        out.append("__cramp__")
    return out


def _r_loss(world: World) -> list[str]:
    if world.facts.get("ended"):
        return []
    if world.facts.get("mistake") and "case" in world.entities:
        case = world.get("case")
        sig = ("loss", case.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        case.meters["open"] += 1
        case.meters["ruined"] += 1
        world.get("detective").memes["regret"] += 1
        return ["__loss__"]
    return []


CAUSAL_RULES = [
    Rule("sound", "physical", _r_sound),
    Rule("cramp", "physical", _r_cramp),
    Rule("loss", "social", _r_loss),
]


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


def _investigate(world: World, detective: Entity, suspect: Entity, clue: Clue) -> None:
    detective.meters["steps"] += 1
    detective.memes["focus"] += 1
    world.say(f'{detective.id} followed the clue to {clue.label}, and the trail pointed toward {suspect.label}.')


def _wrong_turn(world: World, detective: Entity, suspect: Entity) -> None:
    detective.memes["doubt"] += 1
    world.say(f'But {detective.id} guessed wrong and stared at {suspect.label} instead of the real hiding place.')


def _cramp_beat(world: World, detective: Entity) -> None:
    detective.meters["strain"] += 1
    propagate(world, narrate=False)
    world.say(f"Then {detective.id} crouched too long, and a cramp grabbed {detective.pronoun('possessive')} leg.")


def _sound_beat(world: World, source: Hazard) -> None:
    source.meters["noise"] += 1
    propagate(world, narrate=False)
    world.say(f"Somewhere in the dark, a {source.label} made a small sound: {source.attrs.get('sound_word', 'tap')}.")


def _bad_twist(world: World, culprit: Suspect, detective: Entity, case: Entity) -> None:
    world.facts["ended"] = True
    case.meters["open"] += 1
    case.meters["ruined"] += 1
    detective.memes["loss"] += 1
    world.say(f'By the time {detective.id} looked back, {culprit.label} was gone, and the case lay open on the floor.')


def tell(setting: Setting, detective_name: str, detective_gender: str,
         partner_name: str, partner_gender: str, suspect: Suspect,
         clue1: Clue, clue2: Clue, hazard: Hazard) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="partner"))
    case = world.add(Entity(id="case", type="thing", label="the mystery box"))
    hidden = world.add(Entity(id="hidden", type=hazard.type, label=hazard.label, attrs={"sound_word": "tap" if hazard.makes_sound else "rustle"}))
    world.add(Entity(id="suspect", type="person", label=suspect.label))

    world.say(f"That night, {detective.id} and {partner.id} were in {setting.place}, where the {setting.room_word} felt extra quiet.")
    world.say(f"Then a tiny {setting.night_word} {hazard.label} sound drifted from the {setting.shadow_word}.")
    world.para()
    _sound_beat(world, hidden)
    _investigate(world, detective, world.get("suspect"), clue1)
    _cramp_beat(world, detective)
    _investigate(world, partner, world.get("suspect"), clue2)
    _wrong_turn(world, detective, world.get("suspect"))
    if suspect.can_make_sound:
        world.say(f"{partner.id} thought {suspect.label} was the culprit, but that was only half-right.")
    world.para()
    _bad_twist(world, suspect, detective, case)
    world.say("The real culprit slipped out through the open door while everyone was still arguing.")
    world.say(f"In the end, the room was left with an open case, a sore leg, and no solved mystery.")
    world.facts.update(
        detective=detective, partner=partner, suspect=suspect, clue1=clue1, clue2=clue2,
        hazard=hazard, case=case, hidden=hidden, outcome="bad"
    )
    return world


SETTINGS = {
    "museum": Setting("museum", "the little museum", "gallery", "gallery", "corner"),
    "library": Setting("library", "the old library", "reading room", "hallway", "shadow"),
    "station": Setting("station", "the train station", "waiting room", "platform", "bench"),
}

SUSPECTS = {
    "janitor": Suspect("janitor", "the janitor", "kept the rooms tidy", "might have carried the box away"),
    "cat": Suspect("cat", "the cat", "liked warm corners", "might have knocked the box open"),
    "neighbor": Suspect("neighbor", "the neighbor", "often visited after dinner", "might have come and gone quickly"),
}

CLUES = {
    "ink": Clue("ink", "an ink smudge", "found an ink smudge on the table", 1, "desk"),
    "key": Clue("key", "a tiny key", "found a tiny key under a chair", 2, "box"),
    "crumb": Clue("crumb", "a cookie crumb", "found a cookie crumb near the door", 1, "door"),
}

HAZARDS = {
    "pipe": Hazard("pipe", "loose pipe", "object", makes_sound=True, hidden=True),
    "vent": Hazard("vent", "rattling vent", "object", makes_sound=True, hidden=True),
    "toy": Hazard("toy", "wind-up toy", "object", makes_sound=True, hidden=True, can_cause_cramp=False),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    detective_name: str
    detective_gender: str
    partner_name: str
    partner_gender: str
    suspect: str
    clue1: str
    clue2: str
    hazard: str
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


KNOWLEDGE = {
    "sound": [("What is a sound?", "A sound is something you hear with your ears, like a tap, a creak, or a voice.")],
    "cramp": [("What is a cramp?", "A cramp is a sudden painful squeeze in a muscle. It can make a leg or foot hurt for a while.")],
    "mystery": [("What is a mystery?", "A mystery is something you do not know yet and need clues to figure out.")],
    "clue": [("What is a clue?", "A clue is a small piece of information that helps solve a mystery.")],
    "suspect": [("What is a suspect?", "A suspect is someone who might have done it in a mystery, but you still need proof.")],
    "case": [("Why do detectives look at clues?", "Detectives look at clues to learn what really happened and who is responsible.")],
}
ORDER = ["mystery", "sound", "cramp", "clue", "suspect", "case"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c1 in CLUES:
            for c2 in CLUES:
                if c1 != c2:
                    for h in HAZARDS:
                        combos.append((s, c1, h))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld with a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue1", choices=CLUES)
    ap.add_argument("--clue2", choices=CLUES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--name")
    ap.add_argument("--partner")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
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
    if args.clue1 and args.clue2 and args.clue1 == args.clue2:
        raise StoryError("Choose two different clues.")
    setting = args.setting or rng.choice(list(SETTINGS))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    clue1 = args.clue1 or rng.choice(list(CLUES))
    clue2 = args.clue2 or rng.choice([k for k in CLUES if k != clue1])
    hazard = args.hazard or rng.choice(list(HAZARDS))
    gender = args.gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(["Nora", "Mina", "Lena", "Ivy", "Theo", "Ben", "Milo"])
    partner = args.partner or rng.choice(["Owen", "Ruby", "Jade", "Finn", "Ari", "June"])
    return StoryParams(setting, name, gender, partner, partner_gender, suspect, clue1, clue2, hazard)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.detective_name, params.detective_gender,
                 params.partner_name, params.partner_gender, SUSPECTS[params.suspect],
                 CLUES[params.clue1], CLUES[params.clue2], HAZARDS[params.hazard])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tiny whodunit for a 3-to-5-year-old that includes the word "sound" and ends badly when the mystery is not solved.',
        f"Tell a mystery story where {f['detective'].id} hears a strange sound, gets a cramp while searching, and the wrong suspect gets the blame.",
        f'Write a child-friendly detective story with clues, a cramp, and a bad ending where the real culprit escapes.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    det = f["detective"]
    par = f["partner"]
    sus = f["suspect"]
    return [
        ("Who is the story about?", f"It is about {det.id} and {par.id}, who try to solve a mystery but do not finish it."),
        ("What strange thing did they hear?", f"They heard a small sound from the dark corner, and that made them start investigating."),
        ("What happened to the detective while searching?", f"{det.id} got a cramp in {det.pronoun('possessive')} leg because {det.id} crouched too long while looking for clues."),
        ("How did the story end?", f"It ended badly. The mystery stayed unsolved, {sus.label} got away, and the room was left messy and open."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = []
    tags = {"mystery", "sound", "cramp", "clue", "suspect", "case"}
    for tag in ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
sound(X) :- noise(X), noise_level(X, N), N >= 1.
cramp(X) :- strain(X), strain_level(X, N), N >= 1.
bad_ending :- lost_case, culprit_escaped, not solved.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for h in HAZARDS:
        lines.append(asp.fact("hazard", h))
        lines.append(asp.fact("noise", h))
        lines.append(asp.fact("noise_level", h, 1))
    lines.append(asp.fact("strain", "detective"))
    lines.append(asp.fact("strain_level", "detective", 1))
    lines.append(asp.fact("lost_case", "yes"))
    lines.append(asp.fact("culprit_escaped", "yes"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show bad_ending/0."))
    ok = bool(asp.atoms(model, "bad_ending"))
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not ok or "got away" not in sample.story:
        print("MISMATCH: ASP or generate failed.")
        return 1
    print("OK: ASP twin and story generation smoke test passed.")
    return 0


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show sound/1.\n#show cramp/1."))
    return sorted(set(asp.atoms(model, "sound")))


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def explain_rejection(args: argparse.Namespace) -> str:
    return "(No story: this whodunit is built to have a sound, a cramp, and a bad ending, but the requested combination is too narrow.)"


CURATED = [
    StoryParams("museum", "Nora", "girl", "Owen", "boy", "janitor", "ink", "key", "pipe"),
    StoryParams("library", "Mina", "girl", "Ari", "boy", "cat", "crumb", "key", "vent"),
    StoryParams("station", "Theo", "boy", "Ruby", "girl", "neighbor", "key", "crumb", "toy"),
]


def valid_for_world(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.suspect in SUSPECTS and params.clue1 in CLUES and params.clue2 in CLUES and params.hazard in HAZARDS


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP valid atoms:", asp_valid())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
