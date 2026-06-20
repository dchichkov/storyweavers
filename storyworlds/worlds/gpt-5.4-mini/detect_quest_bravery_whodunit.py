#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/detect_quest_bravery_whodunit.py
=================================================================

A small standalone storyworld for a kid-friendly whodunit about a missing quest
token, brave sleuthing, and one careful act of detecting the truth.

Premise
-------
Two children are preparing for a pretend quest when a special token goes missing.
They do not use magic or accident-prone action to solve it. Instead, they follow
clues, notice small physical traces, and discover who moved the token and why.
Bravery here means telling the truth, asking again, and checking the facts.

The world is built around:
- detect: noticing evidence in the physical world
- quest: a pretend mission with a missing piece
- bravery: the emotional energy needed to keep looking and admit the answer
- whodunit tone: a cozy mystery with a clear reveal and a final explanation

The domain stays small on purpose so the story can remain state-driven and
constraint-checked.
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
    hiding_spot: str
    clue_surface: str
    quest_frame: str
    allowed: set[str] = field(default_factory=set)

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
class Token:
    id: str
    label: str
    phrase: str
    value: str
    size: str
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
    role: str
    alibi: str
    motive: str
    truthfulness: int
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_detect(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    token = world.get("token")
    if hero.meters["noticed"] >= THRESHOLD and token.meters["found"] < THRESHOLD:
        sig = ("detect",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["certainty"] += 1
            out.append("__detect__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    token = world.get("token")
    if token.meters["returned"] >= THRESHOLD and "celebrate" not in world.fired:
        world.fired.add(("celebrate",))
        world.get("hero").memes["relief"] += 1
        world.get("friend").memes["relief"] += 1
        out.append("__relief__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_detect, _r_relief):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def detect_clue(world: World, hero: Entity, clue: str) -> None:
    hero.meters["noticed"] += 1
    hero.memes["curiosity"] += 1
    if clue == "mud":
        world.get("token").meters["seen_mud"] += 1
        world.say(f"{hero.id} noticed a tiny muddy print by {world.setting.clue_surface}.")
    elif clue == "ribbon":
        world.get("token").meters["seen_ribbon"] += 1
        world.say(f"{hero.id} spotted a ribbon snagged on the edge of a box.")
    else:
        world.get("token").meters["seen_note"] += 1
        world.say(f"{hero.id} found a small note tucked under {world.setting.clue_surface}.")
    propagate(world)


def question(world: World, hero: Entity, friend: Entity, suspect: Entity) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f'"{suspect.id}, did you move the quest token?" {hero.id} asked, with '
        f"a steady voice."
    )
    if suspect.truthfulness >= 2:
        world.say(f'{suspect.id} looked down. "{suspect.alibi}," {suspect.id} said, but it did not sound true.')
    else:
        world.say(f'{suspect.id} blinked and gave the same story again: "{suspect.alibi}."')
    friend.memes["bravery"] += 1


def reveal(world: World, suspect: Suspect, reason: str) -> None:
    world.get("token").meters["found"] += 1
    world.get("token").meters["returned"] += 1
    world.get("hero").memes["bravery"] += 1
    world.say(
        f'At last, {world.get("hero").id} detected the truth: {suspect.id} had moved the token '
        f"to {reason} so the game could stay a surprise."
    )
    world.say(
        f'{suspect.id} admitted it with a sheepish nod, and the quest token went back '
        f"to the little table."
    )


def ending(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    token = world.get("token")
    world.say(
        f"Then the quest began at once. {hero.id} held the token high, {friend.id} "
        f"stood beside {hero.pronoun('object')}, and both of them felt brave enough to "
        f"solve the next mystery too."
    )
    if token.meters["returned"] >= THRESHOLD:
        world.say("The room looked calm again, with the clue put away and the quest ready to start.")


def tell(setting: Setting, suspect: Suspect, clue: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="Mina", kind="character", type="girl", role="detective"))
    friend = world.add(Entity(id="Jasper", kind="character", type="boy", role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type="mother", role="grownup", label="the parent"))
    token = world.add(Entity(id="token", label="quest token"))
    helper = world.add(Entity(id="helper", label=suspect.id, attrs={"suspect": suspect.id}))
    world.facts["suspect"] = suspect
    world.facts["setting"] = setting
    world.facts["clue"] = clue
    world.facts["parent"] = parent

    world.say(
        f"On a quiet afternoon in {setting.place}, Mina and Jasper were ready for a quest. "
        f"{setting.quest_frame}"
    )
    world.say(
        f"Then Mina reached for the quest token -- and it was gone from {setting.hiding_spot}."
    )
    world.say(
        f'"We have to detect where it went," Mina said. "A quest needs bravery."'
    )

    world.para()
    detect_clue(world, hero, clue)
    question(world, hero, friend, helper)

    world.para()
    reveal(world, suspect, reason=setting.hiding_spot)
    ending(world)

    world.facts.update(
        hero=hero, friend=friend, token=token, helper=helper,
        outcome="solved", brave=hero.memes["bravery"] >= THRESHOLD,
        detected=hero.meters["noticed"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "library": Setting(
        "library",
        "the library",
        "the bookmark basket",
        "the rug by the reading chair",
        "The sofa was a castle wall, the hallway was a secret tunnel, and the missing token was the crown piece.",
        allowed={"mud", "ribbon", "note"},
    ),
    "playroom": Setting(
        "playroom",
        "the playroom",
        "the toy chest",
        "the blue blanket fort",
        "The blocks became towers, the couch became a bridge, and the missing token was the shiny quest stone.",
        allowed={"mud", "ribbon", "note"},
    ),
    "kitchen": Setting(
        "kitchen",
        "the kitchen",
        "the jar lid tray",
        "the chair by the window",
        "The stools formed a lookout post, the table was a map table, and the missing token was the silver key.",
        allowed={"crumb", "ribbon", "note"},
    ),
}

SUSPECTS = {
    "pete": Suspect("Pete", "brother", "I was making a paper flag", "to keep the quest secret", truthfulness=3, tags={"ribbon"}),
    "nina": Suspect("Nina", "sister", "I was tidying the books", "to make room for the map", truthfulness=4, tags={"note"}),
    "grandpa": Suspect("Grandpa", "grandpa", "I was looking for my glasses", "because he found the token first", truthfulness=2, tags={"mud"}),
}

CLUES = ["mud", "ribbon", "note"]


TRAITS = ["careful", "brave", "curious", "steady"]


@dataclass
class StoryParams:
    setting: str
    suspect: str
    clue: str
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

CURATED = [
    ("library", "pete", "ribbon"),
    ("playroom", "nina", "note"),
    ("kitchen", "grandpa", "mud"),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for sus_id, sus in SUSPECTS.items():
            for clue in CLUES:
                if clue in setting.allowed and clue in sus.tags:
                    combos.append((sid, sus_id, clue))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit quest storyworld about detect and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
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
              and (args.suspect is None or c[1] == args.suspect)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, sus, clue = rng.choice(sorted(combos))
    return StoryParams(sid, sus, clue)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SUSPECTS[params.suspect], params.clue)
    prompts = generation_prompts(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    suspect = f["suspect"]
    clue = f["clue"]
    return [
        f'Write a cozy whodunit story for a 3-to-5-year-old that includes the word "detect" and a brave quest in {setting.place}.',
        f"Tell a mystery story where Mina and Jasper follow the clue '{clue}' to find the missing quest token and learn why {suspect.id} moved it.",
        f"Write a short story with bravery, a missing token, and a clear reveal at the end in {setting.quest_frame.lower()}",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    suspect: Suspect = f["suspect"]
    setting: Setting = f["setting"]
    clue = f["clue"]
    hero = f["hero"]
    friend = f["friend"]
    return [
        ("Who is the story about?",
         f"It is about Mina and Jasper in {setting.place}. They are the children who keep the quest going when the token disappears."),
        ("What clue helped Mina detect the answer?",
         f"A {clue} clue helped Mina detect the answer. She noticed it because she kept looking carefully instead of giving up."),
        ("Why did the suspect move the token?",
         f"{suspect.id} moved the token {suspect.motive}. That made the mystery feel secret, but it also meant the children had to be brave and ask questions."),
        ("How did the story end?",
         f"The token was returned, the truth was spoken out loud, and the quest began. Mina and Jasper felt brave because they solved the mystery together."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does it mean to detect something?",
         "To detect something means to notice it or find out it is there by paying close attention to clues."),
        ("What is bravery?",
         "Bravery means staying steady when something feels scary or uncertain, and doing the right thing anyway."),
        ("What is a quest?",
         "A quest is a mission or journey to find something, solve something, or help someone."),
        ("What is a whodunit story?",
         "A whodunit is a mystery story where the reader tries to figure out who did something and why."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
detect(H) :- noticed(H), token_missing.
solve :- detect(hero), returned(token).
valid(S, U, C) :- setting(S), suspect(U), clue(C), clue_ok(S, C), clue_tags(U, C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, setting in SETTINGS.items():
        for clue in setting.allowed:
            lines.append(asp.fact("clue_ok", sid, clue))
    for uid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", uid))
        for tag in suspect.tags:
            lines.append(asp.fact("clue_tags", uid, tag))
    for clue in CLUES:
        lines.append(asp.fact("clue", clue))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos disagree.")
        rc = 1
    try:
        sample = generate(CURATED[0] and StoryParams(*CURATED[0]))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def explain_rejection() -> str:
    return "(No story: this combination does not produce a believable clue trail or whodunit reveal.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, suspect, clue) combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(*c)) for c in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.setting}: {p.suspect} with {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        if header:
            print(header)
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
