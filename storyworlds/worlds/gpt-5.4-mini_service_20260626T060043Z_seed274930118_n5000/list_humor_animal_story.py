#!/usr/bin/env python3
"""
storyworlds/worlds/list_humor_animal_story.py
=============================================

A small animal-comedy story world built from the seed word "list".

Premise:
An animal hero loves making lists. The list helps at first, but the joke
comes from the hero taking it far too seriously or reading it in a funny way.
Another animal helps by turning the big list into a smaller, safer plan.

This world keeps the story child-facing, concrete, and state-driven:
- the hero has a memory-meme for order and worry,
- the list has physical traits like length and whether it is readable,
- the setting and helper determine which jokes are plausible,
- the ending proves what changed in the world.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------

@dataclass
class CharacterSpec:
    kind: str
    name_pool: list[str]
    voice: str
    love: str
    personality: list[str]


@dataclass
class SettingSpec:
    place: str
    indoors: bool
    affordances: set[str]


@dataclass
class ListSpec:
    id: str
    noun: str
    purpose: str
    items: list[str]
    length: int
    comedy: str
    risk: str
    fix_hint: str


@dataclass
class HelperSpec:
    id: str
    kind: str
    line: str
    action: str
    effect: str
    fits: set[str]


CHARACTERS = {
    "rabbit": CharacterSpec(
        kind="rabbit",
        name_pool=["Ruby", "Bun", "Mimi", "Nell", "Pip"],
        voice="a quick little rabbit",
        love="neat plans",
        personality=["careful", "bright", "fussy", "kind"],
    ),
    "fox": CharacterSpec(
        kind="fox",
        name_pool=["Finn", "Tilly", "Arlo", "June", "Ziggy"],
        voice="a clever little fox",
        love="clever plans",
        personality=["smart", "playful", "proud", "cheerful"],
    ),
    "bear": CharacterSpec(
        kind="bear",
        name_pool=["Bruno", "Mabel", "Hugo", "Sally", "Taco"],
        voice="a big gentle bear",
        love="simple plans",
        personality=["slow", "warm", "patient", "jolly"],
    ),
}

SETTINGS = {
    "kitchen": SettingSpec(place="the kitchen", indoors=True, affordances={"snack", "tea", "tidy"}),
    "garden": SettingSpec(place="the garden", indoors=False, affordances={"snack", "picnic", "tidy"}),
    "porch": SettingSpec(place="the porch", indoors=False, affordances={"snack", "picnic", "tidy"}),
    "shed": SettingSpec(place="the shed", indoors=True, affordances={"tidy", "sort"}),
}

LISTS = {
    "picnic": ListSpec(
        id="picnic",
        noun="picnic list",
        purpose="packing a picnic",
        items=["jam sandwiches", "apple slices", "a cup", "a blanket", "a spoon", "a napkin"],
        length=6,
        comedy="the list was so long it curled like a noodle",
        risk="the hero would forget something important",
        fix_hint="make a tiny list with only the needed things",
    ),
    "tidy": ListSpec(
        id="tidy",
        noun="tidy list",
        purpose="cleaning up a room",
        items=["blocks", "books", "boots", "buckets", "bells"],
        length=5,
        comedy="the list was so busy it looked like it was wagging its tail",
        risk="the room would stay messy",
        fix_hint="sort the chores into a small pile",
    ),
    "snack": ListSpec(
        id="snack",
        noun="snack list",
        purpose="choosing treats",
        items=["berries", "crackers", "cheese"],
        length=3,
        comedy="the list was short, but the hero kept reading it like a poem",
        risk="the snacks would be silly, but not enough",
        fix_hint="choose only the best snack",
    ),
}

HELPERS = {
    "owl": HelperSpec(
        id="owl",
        kind="owl",
        line="the owl blinked once and looked very wise",
        action="read the list aloud",
        effect="the words became easy to hear and the mix-up vanished",
        fits={"picnic", "tidy", "snack"},
    ),
    "mouse": HelperSpec(
        id="mouse",
        kind="mouse",
        line="the mouse squeezed in with a tiny pencil",
        action="cross out the extra words",
        effect="the list got shorter and much easier to follow",
        fits={"picnic", "tidy", "snack"},
    ),
    "duck": HelperSpec(
        id="duck",
        kind="duck",
        line="the duck waddled over and quacked a helpful rhyme",
        action="sort the things into neat groups",
        effect="the hero could tell what went where without any fuss",
        fits={"picnic", "tidy"},
    ),
}

# ---------------------------------------------------------------------------
# Shared result model world
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"rabbit", "fox", "bear", "owl", "mouse", "duck"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    setting: str
    hero_kind: str
    list_kind: str
    helper_kind: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: SettingSpec) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _hero_name(spec: CharacterSpec, rng: random.Random) -> str:
    return rng.choice(spec.name_pool)


def _make_world(params: StoryParams, rng: random.Random) -> World:
    setting = SETTINGS[params.setting]
    hero_spec = CHARACTERS[params.hero_kind]
    list_spec = LISTS[params.list_kind]
    helper_spec = HELPERS[params.helper_kind]

    world = World(setting)

    hero = world.add(Entity(
        id=_hero_name(hero_spec, rng),
        kind="character",
        type=hero_spec.kind,
        label=hero_spec.voice,
        meters={"order": 0.0, "worry": 0.0, "joy": 0.0},
        memes={"care": 1.0, "humor": 0.0},
    ))
    helper = world.add(Entity(
        id=helper_spec.id,
        kind="character",
        type=helper_spec.kind,
        label=f"the {helper_spec.kind}",
        meters={"help": 0.0},
        memes={"kindness": 1.0},
    ))
    lst = world.add(Entity(
        id="list",
        kind="thing",
        type="list",
        label=list_spec.noun,
        phrase=f"a {list_spec.noun}",
        owner=hero.id,
        caretaker=hero.id,
        meters={"length": float(list_spec.length), "mess": 0.0, "readable": 1.0},
        memes={"important": 1.0},
    ))

    # Act 1: setup
    world.say(
        f"{hero.id} was {hero_spec.voice} who loved {hero_spec.love}."
    )
    world.say(
        f"Before a trip to {setting.place}, {hero.id} wrote a {list_spec.noun} for {list_spec.purpose}."
    )
    world.say(
        f"The list had {', '.join(list_spec.items[:-1])}, and {list_spec.items[-1]}."
    )

    # Act 2: turn into humor/tension
    world.para()
    world.say(
        f"But {list_spec.comedy.capitalize()}."
    )
    hero.memes["humor"] += 1.0
    hero.meters["worry"] += 1.0
    lst.meters["readable"] -= 0.4
    world.say(
        f"{hero.id} stared at it and worried that {list_spec.risk}."
    )

    # The hero overdoes it in a funny way.
    if params.list_kind == "picnic":
        world.say(
            f"{hero.id} packed three cups, two blankets, and even a spoon for a sandwich."
        )
        hero.meters["order"] += 1.0
    elif params.list_kind == "tidy":
        world.say(
            f"{hero.id} lined up the chores in a row, then lined up the row again just to be sure."
        )
        hero.meters["order"] += 1.0
    else:
        world.say(
            f"{hero.id} read the tiny snack list so seriously that every berry sounded grand."
        )
        hero.meters["humor"] = hero.memes.get("humor", 0.0) + 1.0

    # Helper arrives
    world.para()
    world.say(helper_spec.line + ".")
    world.say(
        f"{helper.id} offered to {helper_spec.action} because the list was getting too silly."
    )
    world.facts["helper_effect"] = helper_spec.effect

    # Resolution
    world.say(
        f"That small change made everything clearer: {helper_spec.effect}."
    )
    lst.meters["length"] = max(1.0, lst.meters["length"] - 2.0)
    lst.meters["readable"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["joy"] = 1.0
    world.say(
        f"At the end, {hero.id} went to {setting.place} with the smaller list, and the day felt easy."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        lst=lst,
        hero_spec=hero_spec,
        list_spec=list_spec,
        helper_spec=helper_spec,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Registries -> prompts and Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short humorous animal story about a {f["hero_spec"].kind} and a list.',
        f'Tell a child-friendly animal story where {f["hero"].id} makes a {f["list_spec"].noun} and another animal helps.',
        f'Write a funny story that includes a list, a mix-up, and a small fix at {f["setting"].place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    lst = f["lst"]
    setting = f["setting"]
    list_spec = f["list_spec"]

    return [
        QAItem(
            question=f"Who made the {lst.label}?",
            answer=f"{hero.id} made the {lst.label} before going to {setting.place}.",
        ),
        QAItem(
            question=f"Why did {hero.id} worry about the list?",
            answer=f"{hero.id} worried because {list_spec.risk}, and the long list started to feel funny and confusing.",
        ),
        QAItem(
            question=f"How did the {helper.type} help?",
            answer=f"{helper.id} helped by making the list smaller and clearer, so {hero.id} could follow it without fuss.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"The list became easier to read, {hero.id} felt calm again, and the day at {setting.place} could start happily.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "list": [
        QAItem(
            question="What is a list?",
            answer="A list is a set of words or things written in order, so you can remember what to do or bring.",
        )
    ],
    "owl": [
        QAItem(
            question="Why do owls look wise in stories?",
            answer="Owls are often shown as wise because they have big eyes and a calm, thoughtful way of looking at the world.",
        )
    ],
    "mouse": [
        QAItem(
            question="Why can mice be good helpers in stories?",
            answer="Mice are small and quick, so they can sneak around, tidy little spaces, and notice tiny details.",
        )
    ],
    "duck": [
        QAItem(
            question="Why do ducks make funny story helpers?",
            answer="Ducks are funny helpers because they waddle, quack, and seem cheerful even when things are a little messy.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = list(WORLD_KNOWLEDGE["list"])
    helper = world.facts["helper_spec"].id
    if helper in WORLD_KNOWLEDGE:
        out.extend(WORLD_KNOWLEDGE[helper])
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A list is reasonable when it belongs to the hero, matches the setting, and
% the helper can actually make it easier to follow.
list_ok(S, H, L, X) :- setting(S), hero(H), list(L), helper(X),
                       belongs(H, L), fits(X, L), can_use(S, L).

% A story is compatible when the list causes a funny worry and the helper can fix it.
story_ok(S, H, L, X) :- list_ok(S, H, L, X), causes_worry(L), fixes(X, L).

#show story_ok/4.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("can_use", sid, a))
    for hid, h in CHARACTERS.items():
        lines.append(asp.fact("hero", hid))
    for lid, l in LISTS.items():
        lines.append(asp.fact("list", lid))
        lines.append(asp.fact("causes_worry", lid))
    for xid, x in HELPERS.items():
        lines.append(asp.fact("helper", xid))
        for lk in sorted(x.fits):
            lines.append(asp.fact("fits", xid, lk))
        lines.append(asp.fact("fixes", xid, "picnic" if "picnic" in x.fits else "tidy"))
        lines.append(asp.fact("fixes", xid, "snack" if "snack" in x.fits else "tidy"))
    for lid, l in LISTS.items():
        lines.append(asp.fact("belongs", "hero", lid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program()
    model = asp.one_model(program)
    atoms = asp.atoms(model, "story_ok")
    py = set(valid_combos())
    asp_set = set(atoms)
    if asp_set == py:
        print(f"OK: ASP gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    print("ASP:", sorted(asp_set - py))
    print("PY :", sorted(py - asp_set))
    return 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for h in CHARACTERS:
            for l in LISTS:
                for x in HELPERS:
                    if s in SETTINGS and x in HELPERS and l in LISTS:
                        if l in {"picnic", "tidy", "snack"} and x in {"owl", "mouse", "duck"}:
                            combos.append((s, h, l, x))
    return combos


# ---------------------------------------------------------------------------
# Generation / resolution
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous animal story world about a list.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero-kind", choices=CHARACTERS)
    ap.add_argument("--list-kind", choices=LISTS)
    ap.add_argument("--helper-kind", choices=HELPERS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    hero_kind = args.hero_kind or rng.choice(list(CHARACTERS))
    list_kind = args.list_kind or rng.choice(list(LISTS))
    helper_kind = args.helper_kind or rng.choice(list(HELPERS))
    return StoryParams(setting=setting, hero_kind=hero_kind, list_kind=list_kind, helper_kind=helper_kind)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    world = _make_world(params, rng)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        atoms = sorted(set(asp.atoms(model, "story_ok")))
        print(f"{len(atoms)} compatible stories:")
        for atom in atoms:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("garden", "rabbit", "picnic", "mouse", base_seed),
            StoryParams("porch", "fox", "tidy", "owl", base_seed),
            StoryParams("kitchen", "bear", "snack", "duck", base_seed),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
