#!/usr/bin/env python3
"""
storyworlds/worlds/mooshy_drop_gerund_game_teamwork_nursery_rhyme.py
====================================================================

A small nursery-rhyme story world about a mooshy drop, a little game,
and the way teamwork turns a wobbly try into a happy finish.

The seed idea is simple:
- a soft, mooshy drop
- a childlike game
- teamwork as the turn
- a nursery-rhyme voice with concrete, state-driven change

The world is modeled with physical meters and emotional memes, and includes
an inline ASP twin for parity checks.
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


# ---------------------------------------------------------------------------
# Core world entities
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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the nursery yard"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Game:
    id: str
    noun: str
    gerund: str
    verb: str
    toss: str
    teamwork_need: bool
    mess: str
    soil: str
    keyword: str = "mooshy"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "nursery_yard": Setting(place="the nursery yard", indoor=False, affords={"mooshy_drop_game"}),
    "porch": Setting(place="the porch", indoor=False, affords={"mooshy_drop_game"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"mooshy_drop_game"}),
}

GAMES = {
    "mooshy_drop_game": Game(
        id="mooshy_drop_game",
        noun="mooshy drop game",
        gerund="playing the mooshy drop game",
        verb="play the mooshy drop game",
        toss="toss the mooshy drop",
        teamwork_need=True,
        mess="mooshy",
        soil="smooshed and sticky",
        keyword="mooshy",
        tags={"mooshy", "drop", "game", "teamwork"},
    ),
}

PRIZES = {
    "drop": Prize(
        id="drop",
        label="drop",
        phrase="a little mooshy drop",
        region="hands",
        plural=False,
    ),
    "cup": Prize(
        id="cup",
        label="cup",
        phrase="a tiny tin cup",
        region="hands",
        plural=False,
    ),
}

TOOLS = [
    Tool(
        id="tray",
        label="a little tray",
        prep="place the drop on a little tray",
        tail="walked the little tray back together",
        protects={"hands"},
        helps={"mooshy"},
    ),
    Tool(
        id="basket",
        label="a small basket",
        prep="nestle the drop in a small basket",
        tail="held the small basket between them",
        protects={"hands"},
        helps={"mooshy"},
    ),
    Tool(
        id="cloth",
        label="a soft cloth",
        prep="wrap the drop in a soft cloth",
        tail="tucked the soft cloth snug and neat",
        protects={"hands"},
        helps={"mooshy"},
    ),
]

NAMES = ["Mimi", "Pip", "Lulu", "Toby", "Nell", "Benny", "Sally", "Nora"]
HELPER_NAMES = ["Milo", "Dot", "Roo", "Jules", "Penny", "Wren"]
GROWNUPS = ["mother", "father", "aunt", "uncle"]


@dataclass
class StoryParams:
    setting: str
    game: str
    prize: str
    name: str
    helper: str
    grownup: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def game_needs_teamwork(game: Game) -> bool:
    return game.teamwork_need


def prize_at_risk(game: Game, prize: Prize) -> bool:
    return prize.region in {"hands"} and game.mess in {"mooshy"}


def select_tool(game: Game, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if prize.region in tool.protects and game.mess in tool.helps:
            return tool
    return None


def explain_rejection(game: Game, prize: Prize) -> str:
    return (
        f"(No story: the {game.noun} needs a helper move, but nothing in the tool set "
        f"fits a {prize.label} that gets {game.mess}. Pick the mooshy drop or another hand-held prize.)"
    )


# ---------------------------------------------------------------------------
# World helpers and story beats
# ---------------------------------------------------------------------------
def nursery_brightness(setting: Setting, game: Game) -> str:
    if setting.indoor:
        return "The playroom was bright as a penny and quiet as a mouse."
    return "The nursery yard was bright with grass and little footsteps."


def lead_in(hero: Entity, helper: Entity, grownup: Entity, prize: Entity, setting: Setting, game: Game) -> str:
    return (
        f"{hero.id} was a {hero.traits[0]} little {hero.type} who loved to laugh. "
        f"{helper.id} was always near, and {grownup.pronoun('possessive')} {grownup.label} watched with a smile. "
        f"{nursery_brightness(setting, game)}"
    )


def loves_game(hero: Entity, game: Game) -> str:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    return (
        f"{hero.pronoun().capitalize()} loved {game.gerund}; "
        f"the little rhyme of it made the day feel light and bright."
    )


def introduce_prize(hero: Entity, prize: Entity, grownup: Entity) -> str:
    prize.held_by = hero.id
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    return (
        f"Then {grownup.pronoun('possessive')} {grownup.label} brought out {prize.phrase}, "
        f"and {hero.id} held {prize.it()} as if it were a tiny treasure."
    )


def want_to_play(hero: Entity, game: Game, setting: Setting) -> str:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    return (
        f"One day at {setting.place}, {hero.id} wanted to {game.verb} at once, "
        f"but the mooshy drop was wobbly and would not stay still."
    )


def warn(grownup: Entity, hero: Entity, game: Game, prize: Entity) -> str:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    return (
        f"\"If you hurry,\" {grownup.pronoun()} said, \"that {prize.label} will turn {game.soil}.\""
    )


def team_up(hero: Entity, helper: Entity, grownup: Entity, tool: Tool, game: Game) -> str:
    hero.memes["defiance"] = hero.memes.get("defiance", 0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    return (
        f"{hero.id} reached for the drop alone, but it slid and swayed. "
        f"Then {helper.id} came near, and {grownup.pronoun('possessive')} {grownup.label} said, "
        f"\"Teamwork makes the rhythm strong.\""
    )


def compromise(hero: Entity, helper: Entity, grownup: Entity, tool: Tool, game: Game, prize: Entity) -> str:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    hero.memes["conflict"] = 0.0
    prize.held_by = "team"
    return (
        f"\"How about we {tool.prep}?\" {grownup.pronoun()} asked. "
        f"{hero.id} and {helper.id} nodded, so they used {tool.label}. "
        f"That kept the mooshy drop steady and safe."
    )


def ending(hero: Entity, helper: Entity, grownup: Entity, game: Game, prize: Entity, tool: Tool, setting: Setting) -> str:
    return (
        f"Soon {hero.id} and {helper.id} were {game.gerund}, "
        f"and the little {prize.label} stayed snug and clean. "
        f"They {tool.tail}, while {grownup.pronoun('possessive')} {grownup.label} laughed softly nearby. "
        f"That is how the mooshy drop game ended: two friends, one happy rhyme, and teamwork shining."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A game is teamwork-needed when it declares that requirement.
needs_teamwork(G) :- game(G), teamwork_needed(G).

% A prize is at risk if the game can make that held thing mooshy.
at_risk(G, P) :- game(G), prize(P), mess_of(G, M), vulnerable(P, M).

% A tool is a compatible fix when it protects the prize's region and helps with the mess.
compatible(T, G, P) :- tool(T), at_risk(G, P), protects(T, R), worn_on(P, R),
                       helps(T, M), mess_of(G, M).

has_fix(G, P) :- compatible(_, G, P).

valid_story(S, G, P) :- setting(S), game(G), prize(P), needs_teamwork(G), at_risk(G, P), has_fix(G, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for gid, g in GAMES.items():
        lines.append(asp.fact("game", gid))
        lines.append(asp.fact("teamwork_needed", gid))
        lines.append(asp.fact("mess_of", gid, g.mess))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("vulnerable", pid, "mooshy"))
        lines.append(asp.fact("worn_on", pid, p.region))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for r in sorted(t.protects):
            lines.append(asp.fact("protects", t.id, r))
        for m in sorted(t.helps):
            lines.append(asp.fact("helps", t.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for gid in setting.affords:
            game = GAMES[gid]
            for pid, prize in PRIZES.items():
                if game_needs_teamwork(game) and prize_at_risk(game, prize) and select_tool(game, prize):
                    out.append((sid, gid, pid))
    return out


def build_story(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    grownup = world.get("grownup")
    prize = world.get("prize")
    game = world.facts["game"]
    tool = world.facts["tool"]
    setting = world.setting

    world.say(lead_in(hero, helper, grownup, prize, setting, game))
    world.say(loves_game(hero, game))
    world.say(introduce_prize(hero, prize, grownup))

    world.para()
    world.say(want_to_play(hero, game, setting))
    world.say(warn(grownup, hero, game, prize))
    world.say(team_up(hero, helper, grownup, tool, game))

    world.para()
    world.say(compromise(hero, helper, grownup, tool, game, prize))
    world.say(ending(hero, helper, grownup, game, prize, tool, setting))


def choose_tool(game: Game, prize: Prize) -> Tool:
    tool = select_tool(game, prize)
    if tool is None:
        raise StoryError(explain_rejection(game, prize))
    return tool


def choose_name(rng: random.Random) -> str:
    return rng.choice(NAMES)


def choose_helper(rng: random.Random, used: str) -> str:
    choices = [n for n in HELPER_NAMES if n != used]
    return rng.choice(choices)


def choose_grownup(rng: random.Random) -> str:
    return rng.choice(GROWNUPS)


def tell(setting: Setting, game: Game, prize_cfg: Prize, name: str, helper_name: str, grownup_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="child", traits=[trait, "little"]))
    helper = world.add(Entity(id=helper_name, kind="character", type="child", traits=["kind", "small"]))
    grownup = world.add(Entity(id="grownup", kind="character", type=grownup_type, label="grownup"))
    prize = world.add(Entity(id="prize", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase))
    tool = choose_tool(game, prize_cfg)
    world.facts.update(game=game, prize=prize_cfg, tool=tool)
    build_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    game = f["game"]
    prize = f["prize"]
    return [
        f'Write a short nursery-rhyme story about a child who wants to {game.verb} with {prize.phrase}.',
        f'Tell a gentle story where teamwork helps keep {prize.phrase} from getting {game.soil}.',
        f'Write a rhyme-like story using the word "{game.keyword}" and ending with friends working together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = world.get("hero")
    helper = world.get("helper")
    game = f["game"]
    prize = f["prize"]
    tool = f["tool"]
    grownup = world.get("grownup")
    place = world.setting.place

    return [
        QAItem(
            question=f"What did {hero.id} want to do at {place}?",
            answer=f"{hero.id} wanted to {game.verb}, and the mooshy drop made the game a little tricky.",
        ),
        QAItem(
            question=f"Why did the grownup worry about {prize.label}?",
            answer=f"The grownup worried because {prize.phrase} could get {game.soil} if the game was rushed.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} fix the problem?",
            answer=f"They used {tool.label} together, so teamwork kept the drop steady and safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {helper.id} {game.gerund}, while the {prize.label} stayed clean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means two or more helpers work together on the same task so it goes better than trying alone.",
        ),
        QAItem(
            question="What does mooshy mean?",
            answer="Mooshy means soft, wet, and a little squishy, like something that can press down or smush easily.",
        ),
        QAItem(
            question="What is a nursery rhyme?",
            answer="A nursery rhyme is a short, simple story or song with a playful beat, made for little ears.",
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params and CLI
# ---------------------------------------------------------------------------
TRAITS = ["cheery", "curious", "brave", "peppy", "gentle", "spry"]


def explain_gender(_: str, __: str) -> str:
    return ""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: a mooshy drop game with teamwork."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--game", choices=GAMES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--grownup", choices=GROWNUPS)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.game and args.prize:
        game = GAMES[args.game]
        prize = PRIZES[args.prize]
        if not (game_needs_teamwork(game) and prize_at_risk(game, prize) and select_tool(game, prize)):
            raise StoryError(explain_rejection(game, prize))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.game is None or c[1] == args.game)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, game, prize = rng.choice(sorted(combos))
    name = args.name or choose_name(rng)
    helper = args.helper or choose_helper(rng, name)
    grownup = args.grownup or choose_grownup(rng)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, game=game, prize=prize, name=name, helper=helper, grownup=grownup)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type="child", traits=[params.trait, "little"]))
    helper = world.add(Entity(id=params.helper, kind="character", type="child", traits=["kind", "small"]))
    grownup = world.add(Entity(id="grownup", kind="character", type=params.grownup, label="grownup"))
    prize_cfg = PRIZES[params.prize]
    prize = world.add(Entity(id="prize", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase))
    game = GAMES[params.game]
    tool = choose_tool(game, prize_cfg)
    world.facts.update(game=game, prize=prize_cfg, tool=tool)
    build_story(world)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        cur = [
            StoryParams(setting="nursery_yard", game="mooshy_drop_game", prize="drop", name="Mimi", helper="Dot", grownup="mother", seed=base_seed),
            StoryParams(setting="porch", game="mooshy_drop_game", prize="drop", name="Pip", helper="Milo", grownup="father", seed=base_seed + 1),
            StoryParams(setting="playroom", game="mooshy_drop_game", prize="cup", name="Lulu", helper="Wren", grownup="aunt", seed=base_seed + 2),
        ]
        samples = [generate(p) for p in cur]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.game} at {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
