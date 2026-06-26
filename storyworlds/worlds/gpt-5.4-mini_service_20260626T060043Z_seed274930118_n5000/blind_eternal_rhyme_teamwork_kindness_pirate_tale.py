#!/usr/bin/env python3
"""
Story world: a tiny pirate tale about a blind captain, an eternal rhyme,
teamwork, and kindness.

Premise:
A crew sails by a song they share. The captain cannot see the reef, so the
mates must work together and choose kindness when the sea turns tricky.

State model:
- meters track ship repair, reef danger, treasure safety, and lantern light.
- memes track trust, worry, hope, kindness, and rhyme-stamina.

Turn:
A storm and a reef challenge the crew. The captain's blind navigation alone is
not enough, so the crew uses a rhyme as a memory aid and teamwork to keep the
ship safe.

Resolution:
Kindness keeps the crew calm, the rhyme guides them past danger, and the ship
arrives with a bright new story.

The script supports the shared Storyweavers contract, including ASP parity
verification, trace output, QA, JSON, and curated/random generation.
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
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "mate", "sailor", "pirate", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "captainess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the sea"
    detail: str = "the deck creaked under salt and spray"


@dataclass
class Tale:
    id: str
    keyword: str
    verb: str
    gerund: str
    image: str
    danger: str
    turns: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    safe_from: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = "stormy"
        self.route: str = "reef"
        self.reef_warning: bool = False

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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.weather = self.weather
        w.route = self.route
        w.reef_warning = self.reef_warning
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "sea": Setting(place="the open sea", detail="the deck creaked under salt and spray"),
    "harbor": Setting(place="the harbor waters", detail="the harbor lanterns blinked along the docks"),
    "island": Setting(place="the island cove", detail="the cove glimmered under a hard, bright sky"),
}

TALES = {
    "rhyme": Tale(
        id="rhyme",
        keyword="rhyme",
        verb="sing the rhyme",
        gerund="singing the rhyme",
        image="the old rhyme that rolled like waves",
        danger="forget the order",
        turns="kept the crew in step",
        tags={"rhyme", "song"},
    ),
    "teamwork": Tale(
        id="teamwork",
        keyword="teamwork",
        verb="work together",
        gerund="working together",
        image="hands hauling rope side by side",
        danger="pull alone",
        turns="made the whole crew stronger",
        tags={"teamwork", "rope"},
    ),
    "kindness": Tale(
        id="kindness",
        keyword="kindness",
        verb="be kind",
        gerund="being kind",
        image="a soft word passed from mate to mate",
        danger="shout back in anger",
        turns="calmed the storm in every chest",
        tags={"kindness", "heart"},
    ),
}

PRIZES = {
    "map": Item(
        label="map",
        phrase="an old sea map",
        type="map",
        region="hands",
        safe_from={"wet"},
    ),
    "lantern": Item(
        label="lantern",
        phrase="a brass lantern",
        type="lantern",
        region="hands",
        safe_from={"wind"},
    ),
    "compass": Item(
        label="compass",
        phrase="a small compass",
        type="compass",
        region="hands",
        safe_from={"splash"},
    ),
}

GEAR = {
    "rope": Item(
        label="rope",
        phrase="a sturdy rope",
        type="rope",
        region="deck",
        plural=False,
        safe_from={"storm", "reef"},
    ),
    "song": Item(
        label="song",
        phrase="an old tune",
        type="song",
        region="mind",
        plural=False,
        safe_from={"forgetfulness"},
    ),
    "lamp": Item(
        label="lamp",
        phrase="a hooded lamp",
        type="lamp",
        region="hands",
        plural=False,
        safe_from={"dark"},
    ),
}

NAMES = ["Mara", "Finn", "Nell", "Bo", "Jory", "Iris", "Tamsin", "Pip"]
ROLES = ["captain", "mate", "sailor", "pirate"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    tale: str
    prize: str
    captain_name: str
    captain_role: str
    mate_name: str
    mate_role: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def tale_at_risk(tale: Tale, prize: Item) -> bool:
    return True if prize.region == "hands" else False


def select_fix(tale: Tale, prize: Item) -> Optional[Item]:
    if tale.id == "rhyme":
        return GEAR["song"]
    if tale.id == "teamwork":
        return GEAR["rope"]
    if tale.id == "kindness":
        return GEAR["lamp"]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for tale_id in TALES:
            for prize_id in PRIZES:
                if tale_at_risk(TALES[tale_id], PRIZES[prize_id]) and select_fix(TALES[tale_id], PRIZES[prize_id]):
                    out.append((place, tale_id, prize_id))
    return out


def explain_rejection(tale: Tale, prize: Item) -> str:
    return (
        f"(No story: {tale.keyword} would not honestly threaten {prize.label} here, "
        f"so there is no real problem to solve.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def make_entity(name: str, role: str, kind: str = "character") -> Entity:
    return Entity(
        id=name,
        kind=kind,
        type=role,
        meters={"balance": 0.0, "trust": 0.0, "fear": 0.0, "hope": 0.0},
        memes={"trust": 0.0, "worry": 0.0, "hope": 0.0, "kindness": 0.0, "rhyme": 0.0, "teamwork": 0.0},
    )


def predict_crossing(world: World, hero: Entity, tale: Tale, prize: Entity) -> dict:
    sim = world.copy()
    do_turn(sim, hero.id, tale.id, prize.id, narrate=False)
    return {
        "safe": sim.facts.get("safe", False),
        "lost_rhyme": sim.facts.get("lost_rhyme", False),
    }


def do_turn(world: World, hero_id: str, tale_id: str, prize_id: str, narrate: bool = True) -> None:
    hero = world.get(hero_id)
    prize = world.get(prize_id)
    tale = TALES[tale_id]
    key = ("turn", hero_id, tale_id, prize_id)
    if key in world.fired:
        return
    world.fired.add(key)

    hero.meters["fear"] += 1
    hero.memes["worry"] += 1
    world.say(f"The sea went dark, and {hero.id} could not see the reef ahead.")
    world.say(f"{hero.id} listened for the {tale.keyword}, but the wind kept trying to hide it.")

    if tale.id == "rhyme":
        hero.memes["rhyme"] += 1
        world.facts["rhyme_heard"] = True
        world.say(f"Still, {hero.id} hummed the old rhyme: {tale.image}.")
    elif tale.id == "teamwork":
        hero.memes["teamwork"] += 1
        world.facts["teamwork_called"] = True
        world.say(f"{hero.id} called the crew to haul together, side by side.")
    else:
        hero.memes["kindness"] += 1
        world.facts["kindness_called"] = True
        world.say(f"{hero.id} chose a kind voice, and the crew answered softly.")

    fix = select_fix(tale, prize)
    if fix:
        hero.memes["hope"] += 1
        world.facts["fix"] = fix.label
        world.say(
            f"That was when {hero.id} used {fix.label} to keep the ship true, "
            f"so the {tale.keyword} could do its work."
        )
        world.facts["safe"] = True
    else:
        world.facts["safe"] = False

    if tale.id == "rhyme":
        hero.meters["balance"] += 1
        world.say(f"The rhyme stayed in the crew's heads, steady as a lantern over water.")
    elif tale.id == "teamwork":
        hero.meters["balance"] += 1
        world.say(f"With every pair of hands helping, the ship moved like one brave body.")
    else:
        hero.meters["trust"] += 1
        world.say(f"The kind word settled the quarrel before it could grow teeth.")


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    world.weather = "stormy"
    hero = world.add(make_entity(params.captain_name, params.captain_role))
    mate = world.add(make_entity(params.mate_name, params.mate_role))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=PRIZES[params.prize].type,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        meters={"wet": 0.0},
    ))

    tale = TALES[params.tale]

    # Act 1
    world.say(f"{hero.id} was a blind {hero.type} who loved the eternal {tale.keyword} of the sea.")
    world.say(f"{mate.id} stayed near, because the crew trusted {hero.pronoun('possessive')} ears more than any map.")
    world.say(f"On deck sat {prize.phrase}, and every mate knew the storm could make it trouble.")
    world.para()

    # Act 2
    world.say(f"One night, the ship slipped toward {world.setting.place}, where the water hid a sharp reef.")
    world.say(f"The old problem was plain: the sea asked the crew to {tale.danger}, but that was no safe way to sail.")
    do_turn(world, hero.id, tale.id, prize.id)
    world.para()

    # Act 3
    if world.facts.get("safe"):
        hero.memes["hope"] += 1
        hero.memes["kindness"] += 1
        mate.memes["trust"] += 1
        world.say(
            f"Together, the crew held steady, and {hero.id} smiled toward the sound of kind voices."
        )
        world.say(
            f"At last the ship passed the reef, {tale.turns}, and the sea opened into calm water."
        )
        world.say(
            f"{prize.phrase.capitalize()} stayed safe, and the deck felt bright again under the moon."
        )
    else:
        world.say(
            f"The crew still gave {hero.id} their hands, but the sea stayed rough and the tale could not finish safely."
        )

    world.facts.update(
        hero=hero,
        mate=mate,
        prize=prize,
        tale=tale,
        setting=world.setting,
        safe=world.facts.get("safe", False),
    )
    return world


# ---------------------------------------------------------------------------
# Prose and QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    tale = f["tale"]
    prize = f["prize"]
    return [
        f'Write a short pirate tale for a young child about a blind {hero.type} and the eternal {tale.keyword}.',
        f"Tell a gentle sea story where {hero.id} needs {tale.keyword}, {tale.keyword}, and more {tale.keyword} to keep {prize.label} safe.",
        f"Write a story about pirates who solve a reef problem with {tale.keyword}, teamwork, and kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    tale = f["tale"]
    prize = f["prize"]
    qa = [
        QAItem(
            question=f"Who could not see the reef in the story?",
            answer=f"{hero.id} could not see the reef because {hero.pronoun('subject')} was blind, so the crew had to help by listening and working together.",
        ),
        QAItem(
            question=f"What eternal thing helped the crew move safely through the storm?",
            answer=f"The eternal {tale.keyword} helped the crew remember what to do. It gave them a steady pattern when the sea felt confusing.",
        ),
        QAItem(
            question=f"What was the crew trying to keep safe on the ship?",
            answer=f"They were trying to keep {prize.phrase} safe while they sailed near the reef.",
        ),
        QAItem(
            question=f"Who stayed near {hero.id} during the dangerous part of the trip?",
            answer=f"{mate.id} stayed near {hero.id} and helped with the work, so {hero.id} was not alone.",
        ),
    ]
    if f.get("safe"):
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=(
                    f"The crew passed the reef safely. The {tale.keyword} did its job, "
                    f"and the ship sailed on into calmer water."
                ),
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "rhyme": (
        "What is a rhyme?",
        "A rhyme is a pattern of words or sounds that end in a similar way, like a little song you can remember.",
    ),
    "teamwork": (
        "What is teamwork?",
        "Teamwork is when people help each other and do a job together instead of trying to do it alone.",
    ),
    "kindness": (
        "What is kindness?",
        "Kindness means being gentle, helpful, and caring to other people.",
    ),
    "blind": (
        "What does blind mean?",
        "Blind means a person cannot see. They may use sound, touch, or help from others to understand where they are going.",
    ),
    "eternal": (
        "What does eternal mean?",
        "Eternal means something lasts a very long time, as if it never ends.",
    ),
    "pirate": (
        "What is a pirate?",
        "A pirate is a person who sails on the sea and looks for adventure or treasure.",
    ),
    "reef": (
        "What is a reef?",
        "A reef is a line of rocks or coral under the water, and ships must sail carefully around it.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["tale"].tags) | {"blind", "eternal", "pirate", "reef"}
    out: list[QAItem] = []
    for key, pair in WORLD_KNOWLEDGE.items():
        if key in tags:
            out.append(QAItem(question=pair[0], answer=pair[1]))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(sea).
place(harbor).
place(island).

tale(rhyme).
tale(teamwork).
tale(kindness).

prize(map).
prize(lantern).
prize(compass).

% In this tiny domain, every featured tale creates a real problem on the hands.
at_risk(T, P) :- tale(T), prize(P).

has_fix(rhyme, song).
has_fix(teamwork, rope).
has_fix(kindness, lamp).

valid_story(Place, T, P) :- place(Place), tale(T), prize(P), at_risk(T, P), has_fix(T, _).

#show valid_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t in TALES:
        lines.append(asp.fact("tale", t))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    for g in GEAR:
        lines.append(asp.fact("fix", g.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale about blindness, eternal rhyme, teamwork, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tale", choices=TALES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--mate-name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--mate-role", choices=ROLES)
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
    if args.tale and args.prize:
        if not tale_at_risk(TALES[args.tale], PRIZES[args.prize]):
            raise StoryError(explain_rejection(TALES[args.tale], PRIZES[args.prize]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.tale is None or c[1] == args.tale)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, tale, prize = rng.choice(sorted(combos))
    captain_name = args.name or rng.choice(NAMES)
    mate_name = args.mate_name or rng.choice([n for n in NAMES if n != captain_name])
    captain_role = args.role or rng.choice(ROLES)
    mate_role = args.mate_role or rng.choice([r for r in ROLES if r != captain_role])
    return StoryParams(
        place=place,
        tale=tale,
        prize=prize,
        captain_name=captain_name,
        captain_role=captain_role,
        mate_name=mate_name,
        mate_role=mate_role,
    )


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, tale, prize) combos:\n")
        for place, tale, prize in combos:
            print(f"  {place:8} {tale:9} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("sea", "rhyme", "map", "Mara", "captain", "Pip", "mate"),
            StoryParams("harbor", "teamwork", "compass", "Finn", "pirate", "Nell", "sailor"),
            StoryParams("island", "kindness", "lantern", "Tamsin", "captain", "Bo", "mate"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
