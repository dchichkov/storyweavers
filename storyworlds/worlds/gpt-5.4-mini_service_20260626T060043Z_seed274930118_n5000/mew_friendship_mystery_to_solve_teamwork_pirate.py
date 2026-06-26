#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mew_friendship_mystery_to_solve_teamwork_pirate.py
=============================================================================================

A small pirate-tale story world about a curious mystery, a friendly crew, and
teamwork guided by a soft little "mew".

Premise:
- A young pirate and a close friend hear a mysterious "mew" aboard ship.
- The crew must work together to solve where the sound is coming from.
- The answer should be child-facing, concrete, and end with a satisfying image
  that shows friendship and teamwork changed the world state.

This script follows the shared storyworld contract:
- It defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main.
- It supports --seed, -n, --all, --trace, --qa, --json, --asp, --verify, and
  --show-asp.
- It includes a Python reasonableness gate and an inline ASP_RULES twin.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    source: str
    fix: str
    danger: str
    requires: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: str
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.location: str = ""
        self.sound: str = ""

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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


GIRL_NAMES = ["Mira", "Nina", "Tessa", "Luna", "Poppy", "Rosa"]
BOY_NAMES = ["Finn", "Jace", "Owen", "Nico", "Bram", "Theo"]
TRAITS = ["brave", "curious", "cheerful", "quick", "kind"]


SETTINGS = {
    "deck": Setting(place="the ship's deck", affords={"crate", "sail", "hold"}),
    "hold": Setting(place="the dark cargo hold", affords={"crate", "hold"}),
    "harbor": Setting(place="the harbor pier", affords={"dock", "crate"}),
    "island": Setting(place="a small island cove", affords={"cave", "crate"}),
}

MYSTERIES = {
    "crate_mew": Mystery(
        id="crate_mew",
        clue="a soft mew from a crate",
        source="a trapped kitten in a crate",
        fix="open the crate with teamwork and a lantern",
        danger="the kitten could get frightened",
        requires="lantern",
        tags={"mew", "kitten", "crate"},
    ),
    "sail_mew": Mystery(
        id="sail_mew",
        clue="a tiny mew in the sail",
        source="a kitten caught in the folded sailcloth",
        fix="lower the sail and free the kitten with teamwork",
        danger="the kitten could stay stuck high above the deck",
        requires="rope",
        tags={"mew", "kitten", "sail"},
    ),
    "cave_mew": Mystery(
        id="cave_mew",
        clue="a little mew echoing from a cave",
        source="a kitten hiding behind driftwood in the cave",
        fix="follow the echo and gently lift the driftwood together",
        danger="the kitten could stay hidden in the dark",
        requires="rope",
        tags={"mew", "kitten", "cave"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="a brass lantern",
        helps="lights the dark places",
        prep="lift the lantern high",
        tail="carried the lantern so the little paws could be seen",
    ),
    "rope": Tool(
        id="rope",
        label="a sturdy rope",
        helps="helps the crew pull and lower things together",
        prep="loop the rope through their hands",
        tail="kept the rope steady while they worked together",
        plural=False,
    ),
    "bucket": Tool(
        id="bucket",
        label="a bucket",
        helps="can hold water or small things",
        prep="set the bucket nearby",
        tail="set the bucket aside once the mystery was solved",
    ),
}

CREW_NAMES = ["Captain Reed", "Pirate Pip", "Sailor June", "Matey Cal", "First Mate Bea"]


def mystery_at_risk(mystery: Mystery, setting: Setting) -> bool:
    if mystery.id == "crate_mew":
        return "crate" in setting.affords
    if mystery.id == "sail_mew":
        return "sail" in setting.affords
    if mystery.id == "cave_mew":
        return "cave" in setting.affords
    return False


def select_tool(mystery: Mystery) -> Optional[Tool]:
    if mystery.requires == "lantern":
        return TOOLS["lantern"]
    if mystery.requires == "rope":
        return TOOLS["rope"]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            if mystery_at_risk(mystery, setting) and select_tool(mystery) is not None:
                out.append((place, mid, select_tool(mystery).id))
    return out


def reason_reject(mystery: Mystery) -> str:
    return (
        f"(No story: this mystery does not have a reasonable teamwork fix here. "
        f"The crew needs a setting where {mystery.clue} can actually be found.)"
    )


def reason_gender(name: str, gender: str) -> str:
    return f"(No story: try a name that fits the chosen gender for {gender}: {name}.)"


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    friend: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate friendship mystery storyworld with a soft mew and teamwork."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    if args.mystery:
        m = MYSTERIES[args.mystery]
        if args.place and not mystery_at_risk(m, SETTINGS[args.place]):
            raise StoryError(reason_reject(m))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.mystery is None or c[1] == args.mystery)
    ]
    if not combos:
        raise StoryError("(No valid pirate mystery matches the given options.)")
    place, mystery_id, _ = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.gender and args.name:
        pass
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice(["Miri", "Pip", "Jo", "Tate"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery_id, name=name, gender=gender, friend=friend, trait=trait)


@dataclass
class Scene:
    parts: list[str] = field(default_factory=list)

    def add(self, s: str) -> None:
        self.parts.append(s)

    def text(self) -> str:
        return " ".join(self.parts)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    mystery = MYSTERIES[params.mystery]
    tool = select_tool(mystery)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["pirate", params.trait]))
    friend = world.add(Entity(id=params.friend, kind="character", type="pirate", traits=["friend"]))
    captain = world.add(Entity(id="Captain", kind="character", type="pirate", label="Captain Reed"))
    clue = world.add(Entity(id="Clue", type="thing", label="mystery clue", phrase=mystery.clue))
    kit = world.add(Entity(id="Kitten", type="thing", label="kitten", phrase="a tiny kitten"))
    if tool:
        tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label, plural=tool.plural))
    else:
        tool_ent = None

    world.sound = "mew"
    world.location = params.place

    # Act 1
    world.say(f"{hero.id} was a {params.trait} little pirate who sailed with {friend.id}.")
    world.say(f"One gray morning, they heard a soft {world.sound} aboard {world.setting.place}.")
    world.say(f"{friend.id} squeezed {hero.id}'s hand. \"That sounds like a mystery,\" {friend.id} said.")

    # Act 2
    world.para()
    world.say(f"They followed the sound to {mystery.clue}.")
    world.say(f"The captain frowned kindly and said, \"A mystery is best solved together.\"")
    world.say(f"{hero.id} held the clue still while {friend.id} looked around, and the crew listened for the next mew.")
    world.say(f"At last they found {mystery.source}, and {mystery.danger}.")

    # Act 3
    world.para()
    if tool_ent:
        world.say(f"{hero.id} and {friend.id} used {tool_ent.label} and teamwork to solve the puzzle.")
        world.say(f"{tool_ent.label.capitalize()} helped because it {tool_ent.label.split(' ', 1)[-1] if ' ' in tool_ent.label else 'helped'}.")
    world.say(f"They gently freed the kitten, and the little {world.sound} turned into a happy purr.")
    world.say(f"{hero.id} and {friend.id} laughed, and even the captain smiled at their teamwork.")
    world.say(f"By sunset, the crew was sailing on with the kitten curled safely between two good friends.")

    world.facts.update(
        hero=hero,
        friend=friend,
        captain=captain,
        clue=clue,
        kitten=kit,
        tool=tool_ent,
        mystery=mystery,
        setting=world.setting,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale for a child where a soft "{world.sound}" starts a mystery to solve.',
        f"Tell a story about {f['hero'].id} and {f['friend'].id} working together to find out where the mew is coming from.",
        f"Write a gentle pirate story with friendship, teamwork, and a happy ending on {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, mystery = f["hero"], f["friend"], f["mystery"]
    tool = f["tool"]
    qa = [
        QAItem(
            question=f"Who heard the mysterious mew first on the ship?",
            answer=f"{hero.id} and {friend.id} heard it together, and it led them to a mystery they could solve as a team.",
        ),
        QAItem(
            question=f"What were {hero.id} and {friend.id} trying to solve?",
            answer=f"They were trying to solve where the soft mew was coming from and what was hiding behind the clue.",
        ),
        QAItem(
            question=f"How did the friends solve the mystery?",
            answer=f"They stayed close, listened carefully, and used teamwork. {tool.label if tool else 'Their careful teamwork'} helped them free the kitten.",
        ),
        QAItem(
            question=f"What happened at the end of the pirate story?",
            answer=f"The kitten was safe, the mew turned into a purr, and the friends sailed on smiling.",
        ),
    ]
    if tool:
        qa.append(
            QAItem(
                question=f"Why did {tool.label} matter in the story?",
                answer=f"It mattered because it helped the crew work together and solve the mystery safely.",
            )
        )
    return qa


KNOWLEDGE = {
    "mew": [
        ("What does a kitten sound like?", "A kitten can make a soft mew, which is a tiny cat sound."),
    ],
    "kitten": [
        ("What is a kitten?", "A kitten is a baby cat."),
    ],
    "lantern": [
        ("What does a lantern do?", "A lantern gives light so people can see in dark places."),
    ],
    "rope": [
        ("What is rope for?", "Rope helps people pull, lift, tie, and hold things together."),
    ],
    "pirate": [
        ("What is a pirate?", "A pirate is a sailor who sails on the sea, often looking for adventure and treasure."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mystery"].tags)
    if world.facts.get("tool"):
        tags.add(world.facts["tool"].id)
    tags.add("pirate")
    out: list[QAItem] = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
mystery(M) :- clue(M,_).
tool(T) :- helps(T,_).

valid_combo(P,M,T) :- setting(P), clue(M,_), tool(T),
                      risk(M,P), required_tool(M,T).

risk(crate_mew, deck) :- setting(deck).
risk(crate_mew, hold) :- setting(hold).
risk(crate_mew, harbor) :- setting(harbor).
risk(crate_mew, island) :- setting(island).

risk(sail_mew, deck) :- setting(deck).
risk(cave_mew, island) :- setting(island).

required_tool(crate_mew, lantern).
required_tool(sail_mew, rope).
required_tool(cave_mew, rope).

% Story-twin output
#show valid_combo/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("source", mid, m.source))
        lines.append(asp.fact("requires", mid, m.requires))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("helps", tid, t.helps))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_story_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(args.n * 50, 50):
        i += 1
        seed = base_seed + i
        try:
            params = resolve_params(args, random.Random(seed))
        except StoryError as err:
            raise err
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def generate(params: StoryParams) -> StorySample:
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


def resolve_gender_name(args: argparse.Namespace, rng: random.Random) -> tuple[str, str]:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return gender, name


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mystery:
        m = MYSTERIES[args.mystery]
        if not mystery_at_risk(m, SETTINGS[args.place]):
            raise StoryError(reason_reject(m))
    if args.place is None or args.mystery is None:
        combos = [
            c for c in valid_combos()
            if (args.place is None or c[0] == args.place)
            and (args.mystery is None or c[1] == args.mystery)
        ]
        if not combos:
            raise StoryError("(No valid combination matches the given options.)")
        place, mystery_id, _ = rng.choice(sorted(combos))
    else:
        place, mystery_id = args.place, args.mystery
    gender, name = resolve_gender_name(args, rng)
    friend = args.friend or rng.choice(["Pip", "Miri", "Jo", "Nell"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery_id, name=name, gender=gender, friend=friend, trait=trait)


def build_parser_and_main_help() -> None:
    pass


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for p, m, t in combos:
            print(f"  {p:8} {m:10} {t}")
        return

    try:
        if args.all:
            params_list = [
                StoryParams(place=p, mystery=m, name="Mira", gender="girl", friend="Pip", trait="curious")
                for p, m, _ in valid_combos()
            ]
            samples = [generate(p) for p in params_list]
        else:
            samples = build_story_samples(args)
    except StoryError as err:
        print(err)
        return

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
