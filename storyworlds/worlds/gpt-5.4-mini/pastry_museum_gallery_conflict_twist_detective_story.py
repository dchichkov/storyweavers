#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pastry_museum_gallery_conflict_twist_detective_story.py
======================================================================================

A small storyworld for a museum-gallery detective tale with pastry, conflict,
and a twist.

Premise:
- In a quiet museum gallery, a child detective notices a missing pastry prop
  from a display.
- A conflict grows as suspicion falls on the wrong person.
- The twist reveals the pastry was not stolen; it was moved to protect the art.
- The ending proves the change with a calm, corrected exhibit.

The world uses typed entities with physical meters and emotional memes, a simple
forward rule engine, a Python reasonableness gate, and an inline ASP twin.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    mood: str

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
    reason: str
    innocence_hint: str

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
class Pastry:
    id: str
    label: str
    phrase: str
    scent: str
    fragile: bool = True

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
class Twist:
    id: str
    reveal: str
    reason: str
    ending_image: str

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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["alarm"] < THRESHOLD:
            continue
        sig = ("alarm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "gallery" in world.entities:
            world.get("gallery").meters["tension"] += 1
        out.append("__alarm__")
    return out


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["reassured"] < THRESHOLD:
            continue
        sig = ("soften", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] = max(0.0, e.memes["worry"] - 1)
        out.append("__soften__")
    return out


RULES = [Rule("alarm", "social", _r_alarm), Rule("soften", "social", _r_soften)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(i for i in items if not i.startswith("__"))
    if narrate:
        for item in produced:
            world.say(item)
    return produced


def reasonableness_gate(setting: Setting, pastry: Pastry, suspect: Suspect) -> bool:
    return setting.id == "museum_gallery" and pastry.fragile and bool(suspect.reason)


def clue_at_risk(pastry: Pastry) -> bool:
    return pastry.fragile


def twist_requires_conflict(twist: Twist) -> bool:
    return bool(twist.reason)


def _smoke_test_world() -> "StorySample":
    return generate(CURATED[0])


def setup(world: World, detective: Entity, guide: Entity, setting: Setting, pastry: Pastry) -> None:
    detective.memes["curiosity"] += 1
    guide.memes["calm"] += 1
    world.say(
        f"In the museum gallery, {detective.id} was a little detective with a notebook, "
        f"and {guide.id} kept the room quiet and bright. {setting.mood.capitalize()} light "
        f"glowed over the glass cases."
    )
    world.say(
        f"One display held {pastry.phrase}, and its sweet scent drifted near the paintings."
    )


def discover(world: World, detective: Entity, pastry: Pastry, suspect: Suspect) -> None:
    detective.memes["alert"] += 1
    world.say(
        f"{detective.id} stopped by the pastry display and blinked. The pastry was gone from "
        f"its plate, and {detective.id} frowned at the empty space."
    )
    world.say(
        f'"Something is wrong," {detective.id} whispered. "The missing pastry must mean trouble."'
    )
    world.say(
        f"At once, {suspect.label} looked suspicious because {suspect.reason}."
    )


def conflict(world: World, detective: Entity, guide: Entity, suspect: Suspect) -> None:
    detective.memes["worry"] += 1
    detective.meters["alarm"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{detective.id} pointed at {suspect.label} and asked hard questions. "
        f"{guide.id} held up a hand and asked everyone to slow down."
    )
    world.say(
        f'The room felt tense, because the gallery did not like loud voices near the art.'
    )


def twist_reveal(world: World, guide: Entity, pastry: Pastry, twist: Twist) -> None:
    guide.meters["reassured"] += 1
    guide.memes["calm"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the twist came. {twist.reveal} {twist.reason}."
    )
    world.say(
        f"That meant the missing pastry had not been stolen at all; it had been moved safely "
        f"away from the sun."
    )


def solve(world: World, detective: Entity, guide: Entity, pastry: Pastry, twist: Twist) -> None:
    detective.memes["joy"] += 1
    detective.memes["worry"] = 0.0
    world.say(
        f"{detective.id} nodded, wrote the new clue in the notebook, and walked the pastry "
        f"back to its proper stand."
    )
    world.say(
        f"The gallery looked right again: no more empty plate, no more worry, just {twist.ending_image}."
    )
    world.say(
        f'{detective.id} smiled. "Case closed," {detective.id} said, and the sweet pastry was safe.'
    )


def tell(setting: Setting, pastry: Pastry, suspect: Suspect, twist: Twist,
         detective_name: str = "Mina", detective_gender: str = "girl",
         guide_name: str = "Mr. Bell", guide_gender: str = "man") -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_gender, role="guide"))
    gallery = world.add(Entity(id="gallery", type="place", label=setting.place))
    world.facts.update(setting=setting, pastry=pastry, suspect=suspect, twist=twist)

    setup(world, detective, guide, setting, pastry)
    world.para()
    discover(world, detective, pastry, suspect)
    conflict(world, detective, guide, suspect)
    world.para()
    twist_reveal(world, guide, pastry, twist)
    solve(world, detective, guide, pastry, twist)

    world.facts.update(detective=detective, guide=guide, gallery=gallery, outcome="twist")
    return world


SETTINGS = {
    "museum_gallery": Setting("museum_gallery", "the museum gallery", "soft"),
}

PASTRIES = {
    "pastry": Pastry("pastry", "a flaky pastry", "a flaky pastry on a silver plate", "warm butter"),
    "tart": Pastry("tart", "a berry tart", "a berry tart under a glass dome", "sweet berries"),
}

SUSPECTS = {
    "custodian": Suspect("custodian", "the custodian", "the custodian was carrying a tray near the case", "the tray was for cleaning supplies"),
    "cook": Suspect("cook", "the museum cook", "the museum cook had flour on an apron", "the flour was from lunch"),
}

TWISTS = {
    "protective_move": Twist(
        "protective_move",
        "the custodian had moved the pastry",
        "to keep the sunlight from drying out the icing",
        "the pastry resting safely in the shade beside the frame"
    ),
    "decoy": Twist(
        "decoy",
        "the cook had used the display for a lesson",
        "so the children could compare old recipes without touching the art",
        "the pastry back on its stand beside the painted fruit"
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Tia", "Nora", "Ivy"]
BOY_NAMES = ["Finn", "Owen", "Leo", "Nico", "Theo"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for pid, pastry in PASTRIES.items():
            for sid2, suspect in SUSPECTS.items():
                for tid, twist in TWISTS.items():
                    if reasonableness_gate(setting, pastry, suspect) and twist_requires_conflict(twist):
                        out.append((sid, pid, sid2, tid))
    return out


@dataclass
@dataclass
class StoryParams:
    setting: str
    pastry: str
    suspect: str
    twist: str
    detective_name: str
    detective_gender: str
    guide_name: str
    guide_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Museum-gallery detective pastry storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--pastry", choices=PASTRIES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-gender", choices=["man", "woman"])
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
    if args.setting and args.pastry and args.suspect:
        if not reasonableness_gate(SETTINGS[args.setting], PASTRIES[args.pastry], SUSPECTS[args.suspect]):
            raise StoryError("No story: the museum-gallery setup does not create a believable conflict.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.pastry is None or c[1] == args.pastry)
              and (args.suspect is None or c[2] == args.suspect)
              and (args.twist is None or c[3] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, pastry, suspect, twist = rng.choice(sorted(combos))
    pname = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    gender = args.gender or ("girl" if pname in GIRL_NAMES else "boy")
    guide = args.guide or "Mr. Bell"
    gg = args.guide_gender or "man"
    return StoryParams(setting, pastry, suspect, twist, pname, gender, guide, gg)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a 3-to-5-year-old set in a museum gallery that includes the word "pastry".',
        f"Tell a gentle mystery where {f['detective'].id} thinks a pastry was stolen, but the truth is a twist.",
        f"Write a museum gallery story with conflict, a clue, and a twist ending about a missing pastry.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d, g, s, t = f["detective"], f["guide"], f["suspect"], f["twist"]
    return [
        QAItem(
            question="What kind of place was the story set in?",
            answer="It was set in a museum gallery with quiet lights and display cases. That made the missing pastry feel like a real mystery."
        ),
        QAItem(
            question=f"Why did {d.id} think there was trouble?",
            answer=f"{d.id} saw that the pastry was missing from its plate and thought something had gone wrong. The empty stand made {d.id} suspect {s.label} at first."
        ),
        QAItem(
            question="What was the twist?",
            answer=f"{t.reveal}. {t.reason}, so the pastry had been moved for safety instead of being stolen."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{d.id} put the pastry back in the right place and the gallery became calm again. The ending image showed {t.ending_image}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a pastry?", "A pastry is a baked food made from dough, often sweet and flaky. People may fill it with fruit or cream."),
        QAItem("Why are museum galleries quiet?", "Museum galleries are usually quiet so people can look at the art carefully. Loud voices can disturb the peaceful feeling."),
        QAItem("What is a clue in a mystery?", "A clue is a small piece of information that helps solve a problem. Detectives use clues to find out what really happened."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
    lines.append(f"  fired rules: {sorted(n for n, _ in ((x[0], x) for x in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("museum_gallery", "pastry", "custodian", "protective_move", "Mina", "girl", "Mr. Bell", "man"),
    StoryParams("museum_gallery", "tart", "cook", "decoy", "Finn", "boy", "Ms. Reed", "woman"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PASTRIES[params.pastry],
        SUSPECTS[params.suspect],
        TWISTS[params.twist],
        params.detective_name,
        params.detective_gender,
        params.guide_name,
        params.guide_gender,
    )
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


ASP_RULES = r"""
eligible(S,P,Su,T) :- setting(S), pastry(P), suspect(Su), twist(T), fragile(P), reason(Su,_), S = museum_gallery.
conflict(S,P,Su) :- eligible(S,P,Su,_).
twist_story(S,P,Su,T) :- conflict(S,P,Su), twist(T).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", sid) for sid in SETTINGS]
    lines += [asp.fact("pastry", pid) for pid in PASTRIES]
    lines += [asp.fact("fragile", pid) for pid, p in PASTRIES.items() if p.fragile]
    lines += [asp.fact("suspect", sid) for sid in SUSPECTS]
    lines += [asp.fact("twist", tid) for tid in TWISTS]
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("reason", sid, "x"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show eligible/4."))
    return sorted(set(asp.atoms(model, "eligible")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"MISMATCH: smoke test failed: {e}")
        rc = 1
    else:
        print("OK: ASP parity and smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show eligible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(str(x) for x in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
