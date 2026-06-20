#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/patio_devoid_friend_s_backyard_sharing_humor.py
===============================================================================

A standalone story world for a small pirate-style backyard tale about sharing a
find, light humor, and a reconciliation after a childish squabble.

Seeded premise:
- setting: a friend's backyard
- style: pirate tale
- features: Sharing, Humor, Reconciliation
- seed words: patio, devoid

The world model keeps the story state-driven: children explore a friend's
backyard, find a patio that is devoid of the treasure they expected, joke about
it, share what they have, and make up after a small disagreement.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/patio_devoid_friend_s_backyard_sharing_humor.py
    python storyworlds/worlds/gpt-5.4-mini/patio_devoid_friend_s_backyard_sharing_humor.py --qa
    python storyworlds/worlds/gpt-5.4-mini/patio_devoid_friend_s_backyard_sharing_humor.py --all
    python storyworlds/worlds/gpt-5.4-mini/patio_devoid_friend_s_backyard_sharing_humor.py --verify
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
    sea_phrase: str
    patio_phrase: str
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
class Item:
    id: str
    label: str
    phrase: str
    location: str
    shareable: bool = False
    shiny: bool = False
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
class Response:
    id: str
    power: int
    text: str
    fail: str
    qa_text: str
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                out.extend([b for b in bits if not b.startswith("__")])
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["teasing"] < THRESHOLD:
            continue
        sig = ("tension", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["mood"] += 1
        out.append("__tension__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["apology"] < THRESHOLD or e.memes["forgive"] < THRESHOLD:
            continue
        sig = ("reconcile", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["peace"] += 1
        out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("tension", _r_tension), Rule("reconcile", _r_reconcile)]


def setting_for(name: str) -> Setting:
    return SETTINGS[name]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            if "backyard" in item.location and sid == "friend_backyard":
                for rid, resp in RESPONSES.items():
                    if resp.power >= 1:
                        combos.append((sid, iid, rid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    item: str
    response: str
    captain: str
    mate: str
    parent: str
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


SETTINGS = {
    "friend_backyard": Setting(
        "friend_backyard",
        "a friend's backyard",
        "The evening air smelled like grass and adventure.",
        "the patio was devoid of treasure, only a tipped pail and a squeaky chair",
        "bright but a little empty",
    )
}

ITEMS = {
    "snack": Item("snack", "a shared snack", "a shared snack in a little tin", "basket", shareable=True, tags={"sharing"}),
    "map": Item("map", "a crumpled map", "a crumpled map with a crayon X", "pocket", shareable=True, tags={"sharing"}),
    "shell": Item("shell", "a shiny shell", "a shiny shell from the garden path", "hand", shiny=True, shareable=True, tags={"sharing"}),
}

RESPONSES = {
    "laugh": Response("laugh", 2, "laughed and made a silly pirate rhyme about the empty patio",
                      "tried to joke, but the mood stayed sour",
                      "made a joke that turned the frown into a grin",
                      tags={"humor"}),
    "share": Response("share", 3, "shared the snack and the map so both friends could plan together",
                      "tried to share, but they were still too cross",
                      "shared what they had, which made the quarrel shrink",
                      tags={"sharing"}),
    "apologize": Response("apologize", 4, "said sorry, admitted the tease was too sharp, and offered the shiny shell",
                         "said sorry, but the other friend was not ready yet",
                         "apologized and offered a shiny shell to mend the mood",
                         tags={"reconciliation"}),
}

NAMES = ["Mia", "Leo", "Ava", "Noah", "Zoe", "Eli"]
BOY_NAMES = ["Leo", "Noah", "Eli"]
GIRL_NAMES = ["Mia", "Ava", "Zoe"]


def _pick_pair(rng: random.Random) -> tuple[tuple[str, str], tuple[str, str]]:
    a_gender = rng.choice(["girl", "boy"])
    b_gender = "boy" if a_gender == "girl" else "girl"
    a = rng.choice(GIRL_NAMES if a_gender == "girl" else BOY_NAMES)
    b = rng.choice(GIRL_NAMES if b_gender == "girl" else BOY_NAMES)
    return (a, a_gender), (b, b_gender)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-style backyard sharing story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--captain")
    ap.add_argument("--mate")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, response = rng.choice(sorted(combos))
    captain = args.captain or rng.choice(NAMES)
    mate = args.mate or rng.choice([n for n in NAMES if n != captain])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, item, response, captain, mate, parent)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    item = ITEMS[params.item]
    response = RESPONSES[params.response]

    captain = world.add(Entity(params.captain, kind="character", type="boy" if params.captain in BOY_NAMES else "girl",
                               role="captain", traits=["bold"]))
    mate = world.add(Entity(params.mate, kind="character", type="girl" if params.mate in GIRL_NAMES else "boy",
                            role="mate", traits=["witty"]))
    parent = world.add(Entity("Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    shared = world.add(Entity("shared", kind="thing", type="thing", label=item.label))
    shared.meters["bright"] += 1 if item.shiny else 0
    world.facts["item"] = item
    world.facts["setting"] = setting
    world.facts["response"] = response
    world.facts["captain"] = captain
    world.facts["mate"] = mate
    world.facts["parent"] = parent

    world.say(
        f"On a quiet afternoon in {setting.place}, {captain.id} and {mate.id} played like tiny pirates."
        f" {setting.sea_phrase} {setting.patio_phrase}."
    )
    world.say(
        f"They found {item.phrase}, and it felt a little like treasure."
    )
    world.para()
    world.say(
        f"But {mate.id} pointed at the patio and laughed. \"Look -- it is devoid of treasure!\""
    )
    world.say(
        f"{captain.id} snorted at the joke, then wrinkled {captain.pronoun('possessive')} nose because the tease felt sharp."
    )
    captain.memes["teasing"] += 1
    mate.memes["teasing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"For a breath, the two friends stood with crossed arms, as if the whole backyard had gone quiet."
    )
    world.para()
    if response.id == "laugh":
        world.say(
            f"Then {mate.id} broke the grumpy spell by {response.text}."
        )
        mate.memes["forgive"] += 1
        captain.memes["apology"] += 1
    elif response.id == "share":
        world.say(
            f"Then they stopped fussing and {response.text}."
        )
        captain.memes["apology"] += 1
        mate.memes["forgive"] += 1
    else:
        world.say(
            f"Then {captain.id} looked down, said sorry, and {response.text}."
        )
        captain.memes["apology"] += 1
        mate.memes["forgive"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} smiled from the porch, glad the little pirate quarrel had softened."
    )
    world.say(
        f"At the end, the friends shared {item.label}, laughed again, and sailed on across the backyard as if it were a calm little sea."
    )

    world.facts["resolved"] = captain.memes["peace"] >= THRESHOLD or mate.memes["peace"] >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a pirate-style story for a young child that includes the words "patio" and "devoid."',
        f"Tell a gentle backyard pirate story where {f['captain'].id} and {f['mate'].id} share something after a funny misunderstanding.",
        "Write a story about humor and reconciliation in a friend's backyard, with a small pirate feel and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    item = f["item"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {captain.id} and {mate.id}, two little pirate friends in a backyard adventure. They start with a joke, then make up and share what they found."
        ),
        QAItem(
            question="Why did they laugh about the patio?",
            answer="They laughed because the patio was described as devoid of treasure, which made the empty spot sound silly. That humor helped turn the mood from sharp to playful."
        ),
        QAItem(
            question="How did they get along at the end?",
            answer=f"They reconciled by apologizing, sharing {item.label}, and smiling together again. The ending shows that the quarrel was over and the friendship was back."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean if something is devoid of something else?",
            answer="If something is devoid of something else, it does not have that thing at all. In the story, the patio was devoid of treasure, so it was empty."
        ),
        QAItem(
            question="Why is sharing nice?",
            answer="Sharing is nice because it lets more than one person enjoy the same thing. It can help friends feel included and calm down after a disagreement."
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is something funny that makes people smile or laugh. A small joke can change a grumpy mood into a lighter one."
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making up after an argument or hurt feelings. It often happens when people apologize, forgive, and start being kind again."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
shareable(item(I)) :- item(I), shareable_item(I).
humor(I) :- response(I), humor_response(I).
reconcile(I) :- response(I), reconcile_response(I).
valid(setting(S), item(I), response(R)) :- setting(S), item(I), response(R), backyard_setting(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("backyard_setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.shareable:
            lines.append(asp.fact("shareable_item", iid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        if "humor" in resp.tags:
            lines.append(asp.fact("humor_response", rid))
        if "reconciliation" in resp.tags:
            lines.append(asp.fact("reconcile_response", rid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    # smoke test ordinary generation
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: empty story.")
    else:
        print("OK: story generation smoke test passed.")
    return rc


CURATED = [
    StoryParams("friend_backyard", "snack", "share", "Mia", "Leo", "mother"),
    StoryParams("friend_backyard", "map", "laugh", "Noah", "Ava", "father"),
    StoryParams("friend_backyard", "shell", "apologize", "Zoe", "Eli", "mother"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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


def resolve_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, response = rng.choice(sorted(combos))
    captain = args.captain or rng.choice(NAMES)
    mate = args.mate or rng.choice([n for n in NAMES if n != captain])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, item, response, captain, mate, parent)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_args(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
