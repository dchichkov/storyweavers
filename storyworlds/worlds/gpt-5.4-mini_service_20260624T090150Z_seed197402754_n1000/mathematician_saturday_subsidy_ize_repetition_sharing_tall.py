#!/usr/bin/env python3
"""
A small Tall Tale storyworld about a mathematician, a Saturday, and the odd
problem of trying to subsidy-ize a shared idea without turning it into a mess.

The world is built around repetition and sharing:
- Repetition means a pattern must be done several times before it becomes useful.
- Sharing means the mathematician can pass a trusted tool or a proof-sketch around.
- The tension comes from a Saturday market where everyone wants the same bright
  number-pattern, but the mathematician worries that copying it too early will
  make it sloppy.
- The resolution is to subsidy-ize the work: the town helps pay for extra chalk,
  so everyone can practice the same pattern again and again until it shines.

This script follows the Storyweavers contract:
- self-contained stdlib script
- eager import of results containers
- lazy ASP import in helper functions
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mathematician", "man", "father", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "mother", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they" if self.plural else "it",
                "object": "them" if self.plural else "it",
                "possessive": "their" if self.plural else "its"}[case]


@dataclass
class Setting:
    place: str = "the market square"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"man", "woman", "boy", "girl", "mathematician"})


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]
    supports: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "market": Setting(place="the market square", affords={"repetition", "sharing"}),
    "schoolyard": Setting(place="the schoolyard", affords={"repetition", "sharing"}),
    "townhall": Setting(place="the town hall steps", affords={"repetition", "sharing"}),
}

ACTIVITIES = {
    "repetition": Activity(
        id="repetition",
        verb="repeat the pattern",
        gerund="repeating the pattern",
        rush="dash back to the chalkboard",
        mess="smudged",
        soil="smudged and muddled",
        keyword="repetition",
        tags={"repeat", "math", "pattern"},
    ),
    "sharing": Activity(
        id="sharing",
        verb="share the proof",
        gerund="sharing the proof",
        rush="run to hand out the page",
        mess="creased",
        soil="creased and wrinkled",
        keyword="sharing",
        tags={"share", "math", "proof"},
    ),
}

PRIZES = {
    "chalkboard": Prize(
        label="chalkboard",
        phrase="a shiny chalkboard slate",
        type="chalkboard",
        region="hands",
        plural=False,
    ),
    "notes": Prize(
        label="notes",
        phrase="a neat stack of numbered notes",
        type="notes",
        region="hands",
        plural=True,
    ),
    "ledger": Prize(
        label="ledger",
        phrase="a careful ledger book",
        type="ledger",
        region="hands",
        plural=False,
    ),
}

TOOLS = [
    Tool(
        id="chalk",
        label="extra chalk",
        prep="ask the town for extra chalk money",
        tail="went home with a pocketful of chalk",
        helps={"repetition"},
        supports={"smudged"},
    ),
    Tool(
        id="copypaper",
        label="copy paper",
        prep="buy more copy paper for everyone",
        tail="marched back with fresh copy paper",
        helps={"sharing"},
        supports={"creased"},
    ),
    Tool(
        id="stringline",
        label="a string line",
        prep="set out a string line so the pattern stayed straight",
        tail="returned with the string line tied in a neat knot",
        helps={"repetition", "sharing"},
        supports={"smudged", "creased"},
    ),
]

NAMES = ["Ada", "Milo", "Bea", "Ned", "Iris", "Otis", "Lina", "Ezra"]
TRAITS = ["patient", "bright-eyed", "mighty-minded", "cheerful", "steady"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def item_pronoun(ent: Entity) -> str:
    return "them" if ent.plural else "it"


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region == "hands" and activity.id in {"repetition", "sharing"}


def select_tool(activity: Activity, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if activity.id in tool.helps:
            return tool
    return None


def reasonableness_gate(activity: Activity, prize: Prize) -> bool:
    return prize_at_risk(activity, prize) and select_tool(activity, prize) is not None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} and {prize.label} do not make a workable "
        f"Tall Tale trouble here, because the town has no honest fix for it.)"
    )


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "ruined": prize.meters.get(activity.mess, 0.0) >= THRESHOLD,
        "strain": actor.memes.get("strain", 0.0),
    }


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["glee"] = actor.memes.get("glee", 0.0) + 1
    if narrate:
        world.say(f"{actor.id} set to {activity.gerund} under the wide Saturday sky.")


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.meters.get('tallness_word', 'tall')} mathematician "
        f"with a mind full of marching numbers."
    )


def setup(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"On Saturday, {hero.id} loved {activity.gerund}, and {hero.pronoun('possessive')} "
        f"{prize.label} was the pride of {world.setting.place}."
    )


def warn(world: World, hero: Entity, prize: Entity, activity: Activity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["ruined"]:
        return False
    world.say(
        f'"If you go too fast," the mathematician said, '
        f'"your {prize.label} will end up {activity.soil}."'
    )
    return True


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(
        f"But the wish to {activity.verb} again and again was louder than a church bell."
    )
    world.say(f"{hero.id} tried to {activity.rush}.")


def offer_sharing(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"Then the town leaned in to share the work, because good math grows when it is shared."
    )


def compromise(world: World, hero: Entity, prize: Entity, activity: Activity) -> Optional[Tool]:
    tool = select_tool(activity, prize)
    if tool is None:
        return None
    world.add(Entity(
        id=tool.id,
        kind="thing",
        type="tool",
        label=tool.label,
        plural=tool.plural,
        owner=hero.id,
        shared_with={hero.id},
    ))
    if predict_mess(world, hero, activity, prize.id)["ruined"]:
        del world.entities[tool.id]
        return None
    world.say(
        f"The mayor agreed to {tool.prep}, and that made the Saturday crowd grin."
    )
    return tool


def resolve(world: World, hero: Entity, prize: Entity, activity: Activity, tool: Tool) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 2
    hero.memes["stubborn"] = 0.0
    world.say(
        f"{hero.id} took the tool, smiled a giant smile, and began {activity.gerund} "
        f"the honest way."
    )
    world.say(
        f"At the end, {hero.pronoun('possessive')} {prize.label} stayed clean, the pattern grew clear, "
        f"and the whole town could see how sharing made the numbers stronger."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="mathematician", meters={"tallness_word": 1.0}))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        plural=prize_cfg.plural,
        owner=hero.id,
    ))
    world.facts.update(hero=hero, prize=prize, activity=activity, setting=setting, trait=trait)

    introduce(world, hero)
    setup(world, hero, prize, activity)
    world.para()
    world.say(f"{hero.id} wanted to {activity.verb} all Saturday long.")
    warn(world, hero, prize, activity)
    defy(world, hero, activity)
    world.para()
    offer_sharing(world, hero, activity)
    tool = compromise(world, hero, prize, activity)
    if tool is not None:
        resolve(world, hero, prize, activity, tool)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, prize, activity = f["hero"], f["prize"], f["activity"]
    return [
        f'Write a Tall Tale for a child about a mathematician on Saturday who wants to {activity.verb}.',
        f"Tell a story where {hero.id} worries that {prize.label} will get messy, but the town finds a sharing-based fix.",
        f'Write a simple story using the word "{activity.keyword}" and the idea that repetition can help a whole town.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, prize, activity = f["hero"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a mathematician who loves {activity.gerund} on Saturday.",
        ),
        QAItem(
            question=f"Why did {hero.id} worry about the {prize.label}?",
            answer=f"{hero.id} worried because {prize.label} could get {activity.soil} if the work was rushed.",
        ),
        QAItem(
            question=f"What helped the mathematician keep going?",
            answer="The town shared the work and brought extra supplies, so the pattern could be repeated the right way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing the same thing again and again, which can help you learn a pattern.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use, know, or enjoy something together with you.",
        ),
        QAItem(
            question="What is a subsidy?",
            answer="A subsidy is extra help, often money or support, that makes something easier for people to do.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), needs_hands(P), activity_kind(A,repetition).
prize_at_risk(A,P) :- activity(A), prize(P), needs_hands(P), activity_kind(A,sharing).

has_fix(A,P) :- prize_at_risk(A,P), tool(T), helps(T,A), supports(T,P).
valid(Place,A,P) :- setting(Place), affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("activity_kind", aid, aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("needs_hands", pid))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for a in sorted(t.helps):
            lines.append(asp.fact("helps", t.id, a))
        for p in sorted(t.supports):
            lines.append(asp.fact("supports", t.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id, act in ACTIVITIES.items():
            for prize_id, prize in PRIZES.items():
                if act_id in setting.affords and reasonableness_gate(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall Tale storyworld: mathematician, Saturday, subsidy-ize, repetition, sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not reasonableness_gate(act, pr):
            raise StoryError(explain_rejection(act, pr))
    filtered = [c for c in combos
                if (args.place is None or c[0] == args.place)
                and (args.activity is None or c[1] == args.activity)
                and (args.prize is None or c[2] == args.prize)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(filtered))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.trait)
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
        lines.append(f"  {e.id}: type={e.type} label={e.label!r} meters={e.meters} memes={e.memes}")
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
    StoryParams(place="market", activity="repetition", prize="chalkboard", name="Ada", trait="mighty-minded"),
    StoryParams(place="schoolyard", activity="sharing", prize="notes", name="Milo", trait="bright-eyed"),
    StoryParams(place="townhall", activity="repetition", prize="ledger", name="Bea", trait="steady"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for place, act, prize in triples:
            print(f"  {place:10} {act:12} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
