#!/usr/bin/env python3
"""
storyworlds/worlds/winnings_moral_value_fable.py
=================================================

A small fable-style story world about a promised prize, the winnings it brings,
and the moral value the characters learn in the end.

Premise:
- A clever little animal wants to win a prize.
- The prize matters because it can be shared, saved, or shown off.
- Another character watches the choice and feels the moral value of it.

Tension:
- The hero can chase winnings in a selfish way or a fair way.
- The world tracks both physical gain (meters) and moral pressure (memes).
- A proper fable needs a clear turn where the character learns something.

Resolution:
- The winner's action changes the world state.
- The final image shows the winnings and the moral lesson together.

The script supports the shared Storyweavers interface:
- build_parser()
- resolve_params()
- generate()
- emit()
- main()

It also includes a lazy ASP twin for parity checking and world-generation
reasonableness.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id

    def them(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Contest:
    id: str
    name: str
    prize: str
    reward: str
    moral_axis: str  # "honesty" | "sharing" | "kindness"
    temptation: str
    virtuous_act: str
    consequence_good: str
    consequence_bad: str


@dataclass
class Setting:
    place: str
    atmosphere: str
    contest_name: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    contest: str
    hero: str
    rival: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the meadow", atmosphere="bright grass swayed in a warm breeze", contest_name="the meadow prize"),
    "market": Setting(place="the market square", atmosphere="stalls clinked and bright ribbons fluttered", contest_name="the market prize"),
    "riverbank": Setting(place="the riverbank", atmosphere="water sparkled beside the reeds", contest_name="the riverbank prize"),
}

CONTESTS = {
    "berries": Contest(
        id="berries",
        name="the berry contest",
        prize="a basket of golden berries",
        reward="the basket of golden berries",
        moral_axis="sharing",
        temptation="hide the best berries for himself",
        virtuous_act="share the berries fairly",
        consequence_good="the other animals smiled and came to help",
        consequence_bad="the basket felt heavy in his paws, and nobody cheered",
    ),
    "coins": Contest(
        id="coins",
        name="the coin race",
        prize="a pouch of bright coins",
        reward="the pouch of bright coins",
        moral_axis="honesty",
        temptation="take an extra coin and pretend not to notice",
        virtuous_act="tell the truth and leave every coin in its place",
        consequence_good="the judge nodded with a kind smile",
        consequence_bad="his ears grew hot, and the winnings did not feel sweet",
    ),
    "honey": Contest(
        id="honey",
        name="the honey fair",
        prize="a jar of sweet honey",
        reward="the jar of sweet honey",
        moral_axis="kindness",
        temptation="snatch the jar before anyone else could taste it",
        virtuous_act="wait kindly and offer a spoonful to a friend",
        consequence_good="the friend laughed and fetched a clean spoon",
        consequence_bad="the jar looked shiny, but the moment felt small",
    ),
}

HEROES = [
    ("milo", "mouse"),
    ("pippa", "rabbit"),
    ("toby", "fox"),
    ("nina", "squirrel"),
    ("oscar", "badger"),
]

RIVALS = [
    ("bruno", "crow"),
    ("lola", "mole"),
    ("finn", "duck"),
    ("greta", "hedgehog"),
]

TRAITS = ["quick", "small", "bright-eyed", "careful", "bold"]


# ---------------------------------------------------------------------------
# Fable engine
# ---------------------------------------------------------------------------
def paragraph_intro(world: World, hero: Entity, rival: Entity, contest: Contest) -> None:
    world.say(
        f"Once in {world.setting.place}, there lived {hero.phrase} and {rival.phrase}. "
        f"Every creature watched {contest.name}, because the winnings were known all around the field."
    )


def paragraph_desire(world: World, hero: Entity, contest: Contest) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"{hero.name_or_label().capitalize()} wanted the prize: {contest.prize}. "
        f"{hero.pronoun('subject').capitalize()} believed the winnings would make the day feel larger."
    )


def paragraph_test(world: World, hero: Entity, rival: Entity, contest: Contest) -> None:
    world.para()
    world.say(
        f"But the contest asked a harder question too. To win, {hero.name_or_label()} had to choose whether to "
        f"{contest.temptation} or to {contest.virtuous_act}."
    )
    world.say(
        f"{rival.name_or_label().capitalize()} watched closely, because in a fable even small choices can carry moral value."
    )


def run_reasoner(world: World, hero: Entity, contest: Contest, choice: str) -> None:
    # A simple causal gate: the chosen action changes both winnings and moral state.
    if choice == "virtuous":
        sig = ("virtue", hero.id, contest.id)
        if sig in world.fired:
            return
        world.fired.add(sig)
        hero.meters["winnings"] = hero.meters.get("winnings", 0.0) + 1
        hero.memes["moral_value"] = hero.memes.get("moral_value", 0.0) + 1
        hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1
    else:
        sig = ("selfish", hero.id, contest.id)
        if sig in world.fired:
            return
        world.fired.add(sig)
        hero.meters["winnings"] = hero.meters.get("winnings", 0.0) + 1
        hero.memes["moral_value"] = hero.memes.get("moral_value", 0.0) - 1
        hero.memes["unease"] = hero.memes.get("unease", 0.0) + 1


def paragraph_turn(world: World, hero: Entity, rival: Entity, contest: Contest, choice: str) -> None:
    world.para()
    if choice == "virtuous":
        world.say(
            f"{hero.name_or_label().capitalize()} took a breath and chose to {contest.virtuous_act}. "
            f"That was the kinder road, and the choice raised the moral value of the day."
        )
        world.say(
            f"{contest.consequence_good.capitalize()}. Soon the winnings belonged to everyone in spirit, even before the prize was lifted."
        )
    else:
        world.say(
            f"{hero.name_or_label().capitalize()} tried to {contest.temptation}. "
            f"The winnings came close, but the choice made the air feel smaller."
        )
        world.say(
            f"{contest.consequence_bad.capitalize()}."
        )


def paragraph_resolution(world: World, hero: Entity, rival: Entity, contest: Contest, choice: str) -> None:
    world.para()
    if choice == "virtuous":
        world.say(
            f"In the end, {hero.name_or_label()} won {contest.reward}, and everyone could see why the prize mattered. "
            f"The real winnings were not only the berries, coins, or honey, but the good feeling that stayed after."
        )
        world.say(
            f"{hero.name_or_label().capitalize()} went home with {contest.reward}, a calm heart, and a lesson about moral value."
        )
    else:
        world.say(
            f"{hero.name_or_label()} carried {contest.reward} away, but {hero.pronoun('possessive')} smile did not last long. "
            f"The winnings sparkled, yet the fable ended with a lesson about honesty and care."
        )
        world.say(
            f"{rival.name_or_label().capitalize()} looked on quietly, and the day taught that a prize can be heavy when the moral value is low."
        )


def tell(world: World, hero: Entity, rival: Entity, contest: Contest, choice: str) -> World:
    paragraph_intro(world, hero, rival, contest)
    paragraph_desire(world, hero, contest)
    paragraph_test(world, hero, rival, contest)
    run_reasoner(world, hero, contest, choice)
    paragraph_turn(world, hero, rival, contest, choice)
    paragraph_resolution(world, hero, rival, contest, choice)
    world.facts.update(hero=hero, rival=rival, contest=contest, choice=choice)
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_story_combo(setting_key: str, contest_key: str) -> bool:
    return setting_key in SETTINGS and contest_key in CONTESTS


def explain_rejection(setting_key: str, contest_key: str) -> str:
    return f"(No story: the setting {setting_key!r} and contest {contest_key!r} do not form a valid fable.)"


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    contest: Contest = f["contest"]  # type: ignore[assignment]
    return [
        f'Write a short fable for a young child about {hero.name_or_label()} and the winnings from {contest.name}.',
        f'Tell a gentle story where {hero.name_or_label()} must choose between {contest.temptation} and {contest.virtuous_act}.',
        f'Write a story with a clear moral value lesson that ends with {contest.reward}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    rival: Entity = f["rival"]  # type: ignore[assignment]
    contest: Contest = f["contest"]  # type: ignore[assignment]
    choice: str = f["choice"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {hero.name_or_label()} want at {world.setting.place}?",
            answer=f"{hero.name_or_label().capitalize()} wanted {contest.prize}, because the winnings seemed exciting.",
        ),
        QAItem(
            question=f"What choice did {hero.name_or_label()} have to make during {contest.name}?",
            answer=f"{hero.name_or_label().capitalize()} had to choose between {contest.temptation} and {contest.virtuous_act}.",
        ),
        QAItem(
            question=f"Who watched the contest with care?",
            answer=f"{rival.name_or_label().capitalize()} watched closely, because the choice had moral value.",
        ),
        QAItem(
            question=f"How did the story end for {hero.name_or_label()}?",
            answer=(
                f"The story ended with {contest.reward} and a lesson about moral value."
                if choice == "virtuous"
                else f"The story ended with {contest.reward}, but the winnings felt less sweet because the choice was selfish."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are winnings?",
            answer="Winnings are the things someone wins in a contest, game, or race.",
        ),
        QAItem(
            question="What does moral value mean in a fable?",
            answer="Moral value means the lesson about right and kind behavior that the story wants to teach.",
        ),
        QAItem(
            question="Why do fables often use animals?",
            answer="Fables often use animals because animals can show human behavior in a simple and memorable way.",
        ),
    ]


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting_ok(S) :- setting(S).
contest_ok(C) :- contest(C).

moral_path(hero, C) :- choice(hero, C, virtuous).
moral_drop(hero, C) :- choice(hero, C, selfish).

wins(hero, C) :- choice(hero, C, virtuous).
wins(hero, C) :- choice(hero, C, selfish).

good_end(hero, C) :- wins(hero, C), moral_path(hero, C).
lesson(hero, C) :- wins(hero, C), moral_drop(hero, C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CONTESTS:
        lines.append(asp.fact("contest", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show setting_ok/1.\n#show contest_ok/1."))
    settings = sorted(set(asp.atoms(model, "setting_ok")))
    contests = sorted(set(asp.atoms(model, "contest_ok")))
    return [(s[0], c[0]) for s in settings for c in contests if valid_story_combo(s[0], c[0])]


def asp_verify() -> int:
    py = {(s, c) for s in SETTINGS for c in CONTESTS if valid_story_combo(s, c)}
    asp_set = set(asp_reasonable_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("Only in Python:", sorted(py - asp_set))
    print("Only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about winnings and moral value.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--contest", choices=sorted(CONTESTS))
    ap.add_argument("--hero")
    ap.add_argument("--rival")
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
    combos = [(s, c) for s in SETTINGS for c in CONTESTS if valid_story_combo(s, c)]
    if args.setting:
        combos = [x for x in combos if x[0] == args.setting]
    if args.contest:
        combos = [x for x in combos if x[1] == args.contest]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, contest = rng.choice(sorted(combos))
    hero = args.hero or rng.choice([h for h, _ in HEROES])
    rival = args.rival or rng.choice([r for r, _ in RIVALS])
    return StoryParams(setting=setting, contest=contest, hero=hero, rival=rival)


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    contest = CONTESTS[params.contest]
    world = World(setting)
    hero_species = dict(HEROES).get(params.hero, "mouse")
    rival_species = dict(RIVALS).get(params.rival, "crow")
    trait = random.choice(TRAITS)

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        species=hero_species,
        phrase=f"a {trait} little {hero_species}",
    ))
    rival = world.add(Entity(
        id=params.rival,
        kind="character",
        species=rival_species,
        phrase=f"a watchful {rival_species}",
    ))
    world.facts.update(hero=hero, rival=rival, contest=contest)

    choice = "virtuous" if contest.moral_axis in {"honesty", "sharing", "kindness"} else "selfish"
    # Slight variation: sometimes the hero starts tempted but still chooses well.
    if params.setting == "market":
        choice = "virtuous"
    elif params.setting == "riverbank" and params.contest == "berries":
        choice = "selfish"
    world.facts["choice"] = choice
    return tell(world, hero, rival, contest, choice)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
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


CURATED = [
    StoryParams(setting="meadow", contest="berries", hero="milo", rival="bruno"),
    StoryParams(setting="market", contest="coins", hero="pippa", rival="lola"),
    StoryParams(setting="riverbank", contest="honey", hero="toby", rival="greta"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show setting_ok/1.\n#show contest_ok/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show setting_ok/1.\n#show contest_ok/1."))
        print("Settings:", sorted(set(asp.atoms(model, "setting_ok"))))
        print("Contests:", sorted(set(asp.atoms(model, "contest_ok"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, p in enumerate(CURATED):
            p.seed = base_seed + i
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
