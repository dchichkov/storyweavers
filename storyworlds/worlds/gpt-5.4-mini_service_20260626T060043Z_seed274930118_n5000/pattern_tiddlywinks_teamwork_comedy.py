#!/usr/bin/env python3
"""
Standalone storyworld: pattern tiddlywinks teamwork comedy.

A tiny, child-facing comedy domain about a group of friends trying to make a
careful pattern with tiddlywinks, then solving a small mishap together.
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
# Domain data
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TeamSetting:
    place: str
    surface: str
    nearby: str
    affords: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class PatternGame:
    name: str
    verb: str
    gerund: str
    mess: str
    risk: str
    fix_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Prize:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False


@dataclass(frozen=True)
class FixGear:
    id: str
    label: str
    use: str
    outcome: str
    covers: set[str]
    guards: set[str]


SETTINGS = {
    "table": TeamSetting(
        place="the play table",
        surface="smooth wood",
        nearby="a small tray",
        affords={"tiddlywinks", "pattern"},
    ),
    "floor": TeamSetting(
        place="the carpet",
        surface="soft carpet",
        nearby="a basket of cups",
        affords={"tiddlywinks", "pattern"},
    ),
}

GAMES = {
    "tiddlywinks": PatternGame(
        name="tiddlywinks",
        verb="tap the tiddlywinks",
        gerund="tapping tiddlywinks",
        mess="scattered",
        risk="the little disks might scatter",
        fix_hint="a neat way to keep them lined up",
        tags={"tiddlywinks", "pattern", "teamwork", "comedy"},
    ),
    "pattern": PatternGame(
        name="pattern",
        verb="build a pattern",
        gerund="building a pattern",
        mess="mixed",
        risk="the rows might get mixed up",
        fix_hint="a helpful way to sort colors",
        tags={"pattern", "teamwork", "comedy"},
    ),
}

PRIZES = {
    "tiles": Prize(
        label="tiles",
        phrase="bright pattern tiles",
        type="tiles",
        location="table",
        plural=True,
    ),
    "cards": Prize(
        label="cards",
        phrase="striped picture cards",
        type="cards",
        location="table",
        plural=True,
    ),
    "cups": Prize(
        label="cups",
        phrase="tiny color cups",
        type="cups",
        location="floor",
        plural=True,
    ),
}

GEAR = [
    FixGear(
        id="bowl",
        label="a wide bowl",
        use="gather the tiddlywinks in a wide bowl",
        outcome="the disks stayed together",
        covers={"table", "floor"},
        guards={"scattered"},
    ),
    FixGear(
        id="tray",
        label="a shallow tray",
        use="sort the pieces in a shallow tray",
        outcome="the pattern pieces stayed in their lanes",
        covers={"table", "floor"},
        guards={"mixed", "scattered"},
    ),
    FixGear(
        id="ruler",
        label="a ruler",
        use="line up the cards with a ruler",
        outcome="the rows stayed neat and straight",
        covers={"table"},
        guards={"mixed"},
    ),
]

NAMES = ["Mina", "Toby", "Lina", "Owen", "Pia", "Theo", "June", "Nico"]
HELPERS = ["friend", "helper", "buddy", "teammate"]


@dataclass
class StoryParams:
    place: str
    game: str
    prize: str
    name: str
    helper: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


class World:
    def __init__(self, setting: TeamSetting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------

def risk_for(game: PatternGame, prize: Prize) -> bool:
    return prize.location == "table" and game.name in {"tiddlywinks", "pattern"}


def select_fix(game: PatternGame, prize: Prize) -> Optional[FixGear]:
    for gear in GEAR:
        if prize.location in gear.covers and (game.mess in gear.guards or "scattered" in gear.guards):
            return gear
    return None


def explain_rejection(game: PatternGame, prize: Prize) -> str:
    return (
        f"(No story: {game.gerund} does not make a believable problem for {prize.label}, "
        f"so there is no honest comedy turn to solve.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def _do_game(world: World, actor: Entity, game: PatternGame) -> None:
    actor.meters[game.mess] = actor.meters.get(game.mess, 0.0) + 1.0
    actor.memes["glee"] = actor.memes.get("glee", 0.0) + 1.0


def predict(world: World, actor: Entity, game: PatternGame, prize: Prize) -> dict:
    sim = world.copy()
    _do_game(sim, sim.get(actor.id), game)
    return {
        "scattered": actor.meters.get("scattered", 0.0) >= 1.0,
        "mixed": actor.meters.get("mixed", 0.0) >= 1.0,
    }


def tell(setting: TeamSetting, game: PatternGame, prize_cfg: Prize, hero_name: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="child", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type="child", label=helper_name))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        plural=prize_cfg.plural,
        owner=hero.id,
        location=prize_cfg.location,
    ))

    world.say(f"{hero.id} and {helper.id} were a little team with a big plan.")
    world.say(
        f"They wanted to {game.verb} and make a pretty {game.name} on {setting.place}, "
        f"because {setting.surface} made the pieces easy to see."
    )
    world.say(f"They had {prize.phrase} ready beside {setting.nearby}.")

    world.para()
    world.say(
        f"{hero.id} smiled and said the best part was the pattern, while {helper.id} said the best part was the silly little clicks."
    )
    world.say(f"Then they started {game.gerund}, and the fun began.")

    _do_game(world, hero, game)
    _do_game(world, helper, game)

    world.para()
    world.say(
        f"Oops! One wink went zip, another went plunk, and soon {game.risk}."
    )

    gear = select_fix(game, prize)
    if gear:
        world.say(
            f"{helper.id} laughed and said, 'Easy! We can {gear.use}.'"
        )
        world.say(
            f"{hero.id} nodded, and together they used {gear.label}."
        )
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
        helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1.0
        world.say(
            f"That worked, and {gear.outcome}. Soon the {game.name} looked neat again."
        )
        world.say(
            f"At the end, {hero.id} and {helper.id} finished the pattern together, and everyone had to giggle at how serious such tiny disks could be."
        )
    else:
        world.say(
            f"They tried to fix it with teamwork, but no good tool fit the job."
        )
    world.facts.update(hero=hero, helper=helper, prize=prize, game=game, gear=gear)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, game, prize = f["hero"], f["helper"], f["game"], f["prize"]
    return [
        f'Write a short comedy story for young children about {hero.id}, {helper.id}, and {game.name} on {world.setting.place}.',
        f'Write a story about teamwork where two children try to {game.verb} without messing up {prize.phrase}.',
        f'Write a simple funny story that uses the words "pattern" and "tiddlywinks" and ends with friends solving a small mess together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, game, prize, gear = f["hero"], f["helper"], f["game"], f["prize"], f["gear"]
    qa = [
        QAItem(
            question=f"What were {hero.id} and {helper.id} trying to make at {world.setting.place}?",
            answer=f"They were trying to build a pattern while playing tiddlywinks together.",
        ),
        QAItem(
            question=f"What problem happened when they started {game.gerund}?",
            answer=f"The little disks scattered, so the pattern began to look mixed up.",
        ),
        QAItem(
            question=f"How did they fix the problem?",
            answer=f"They worked together and used {gear.label} to keep the pieces together and neat.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {helper.id} finishing the pattern together and laughing at the silly little disks.",
        ),
    ]
    return qa


WORLD_QA = [
    QAItem(
        question="What is tiddlywinks?",
        answer="Tiddlywinks is a game where you tap little disks so they hop or land in a target.",
    ),
    QAItem(
        question="What is a pattern?",
        answer="A pattern is a repeated arrangement, like colors or shapes in a special order.",
    ),
    QAItem(
        question="What does teamwork mean?",
        answer="Teamwork means people help each other and do a job together.",
    ),
    QAItem(
        question="Why can comedy stories be funny?",
        answer="Comedy stories are funny because characters make silly mistakes and then solve them in a cheerful way.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_QA)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

risk(A,P) :- game(A), prize(P), aff(A,table), loc(P,table).
fix(A,P,G) :- risk(A,P), gear(G), guards(G,scatter), covers(G,table).
valid(Place, Game, Prize) :- setting(Place), game(Game), prize(Prize), aff(Game,Place), risk(Game,Prize), fix(Game,Prize,_).
valid_story(Place, Game, Prize, Name) :- valid(Place, Game, Prize), child(Name).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("aff", a, sid))
    for gid, g in GAMES.items():
        lines.append(asp.fact("game", gid))
        lines.append(asp.fact("mess", gid, g.mess))
        lines.append(asp.fact("risk_text", gid, g.risk))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("loc", pid, p.location))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, c))
        for g in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, g))
    for n in NAMES:
        lines.append(asp.fact("child", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for game_id in setting.affords:
            game = GAMES[game_id]
            for prize_id, prize in PRIZES.items():
                if risk_for(game, prize) and select_fix(game, prize):
                    out.append((place, game_id, prize_id))
    return sorted(set(out))


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: pattern tiddlywinks teamwork.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--game", choices=sorted(GAMES))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.game and args.prize:
        if not (risk_for(GAMES[args.game], PRIZES[args.prize]) and select_fix(GAMES[args.game], PRIZES[args.prize])):
            raise StoryError(explain_rejection(GAMES[args.game], PRIZES[args.prize]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.game is None or c[1] == args.game)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, game, prize = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, game=game, prize=prize, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    game = GAMES[params.game]
    prize = PRIZES[params.prize]
    world = tell(setting, game, prize, params.name, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(place="table", game="tiddlywinks", prize="tiles", name="Mina", helper="friend"),
    StoryParams(place="floor", game="pattern", prize="cards", name="Toby", helper="buddy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with names):\n")
        for place, game, prize in triples:
            names = sorted(n for (pl, g, pr, n) in stories if (pl, g, pr) == (place, game, prize))
            print(f"  {place:8} {game:12} {prize:8}  [{', '.join(names)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.game} at {p.place} ({p.prize})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
