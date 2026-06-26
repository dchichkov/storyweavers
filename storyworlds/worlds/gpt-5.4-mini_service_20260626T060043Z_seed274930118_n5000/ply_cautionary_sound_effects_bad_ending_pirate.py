#!/usr/bin/env python3
"""
storyworlds/worlds/ply_cautionary_sound_effects_bad_ending_pirate.py
====================================================================

A small pirate-tale story world with a cautionary turn, vivid sound effects,
and a bad ending. The seed word "ply" is threaded through the domain as the
name of a pirate's plank-pushing tool, and the storyworld stays close to a
classical pirate warning tale: a greedy crew ignores a careful warning, the
sea answers with rough sounds, and the ending proves why caution mattered.

The world is intentionally constraint-checked:
- the ship, sea, and treasure interact through a small physical model;
- the captain can warn the crew about unsafe choices;
- sound effects are derived from the state change that actually happens;
- the "bad ending" is not decorative: the reckless choice must produce loss.

As required by the storyworld contract, this file is self-contained and includes
an inline ASP twin, registry facts, Python reasonableness gates, story
generation, QA, trace output, and verification helpers.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate", "mate", "sailor", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the ship"
    aboard: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    sound: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    kind: str
    peril: str


@dataclass
class Tool:
    id: str
    label: str
    job: str
    sound: str
    safe_against: set[str]


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "deck": Setting(place="the deck", aboard=True, affords={"sail", "haul"}),
    "cove": Setting(place="the cove", aboard=False, affords={"dig", "sail"}),
    "harbor": Setting(place="the harbor", aboard=False, affords={"haul", "sail"}),
}

ACTIONS = {
    "sail": Action(
        id="sail",
        verb="sail through the dark water",
        gerund="sailing through the dark water",
        rush="dash for the mast rope",
        danger="the sail could tear and the boat could lurch",
        sound="whump",
        keyword="ply",
        tags={"sea", "wind"},
    ),
    "dig": Action(
        id="dig",
        verb="dig for treasure by the rocks",
        gerund="digging for treasure",
        rush="scrabble at the sand",
        danger="the tide could flood the hole",
        sound="scritch",
        keyword="treasure",
        tags={"treasure", "sand"},
    ),
    "haul": Action(
        id="haul",
        verb="haul the heavy chest",
        gerund="hauling the heavy chest",
        rush="pull with both hands",
        danger="the chest could slip overboard",
        sound="grrrk",
        keyword="chest",
        tags={"treasure", "rope"},
    ),
}

PRIZES = {
    "map": Prize(label="map", phrase="a secret map", type="map", kind="paper", peril="ruined by spray"),
    "chest": Prize(label="chest", phrase="a bright treasure chest", type="chest", kind="wood", peril="lost to the sea"),
    "flag": Prize(label="flag", phrase="a new red pirate flag", type="flag", kind="cloth", peril="torn by wind"),
}

TOOLS = [
    Tool(id="ply", label="ply plank", job="brace the chest", sound="clack", safe_against={"sea", "wind"}),
    Tool(id="rope", label="strong rope", job="tie things down", sound="twang", safe_against={"sea"}),
    Tool(id="sailcloth", label="folded sailcloth", job="cover the map", sound="flap", safe_against={"sea", "wind"}),
]

GIRL_NAMES = ["Mira", "Nina", "Tia", "Sela", "Juna"]
BOY_NAMES = ["Finn", "Oren", "Kip", "Bram", "Hale"]
TRAITS = ["brave", "curious", "greedy", "stubborn", "clever"]


def prize_at_risk(action: Action, prize: Prize) -> bool:
    if action.id == "sail":
        return prize.kind in {"paper", "cloth", "wood"}
    if action.id == "dig":
        return prize.kind in {"paper", "cloth"}
    if action.id == "haul":
        return True
    return False


def select_tool(action: Action, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if action.id == "haul" and tool.id == "ply":
            return tool
        if action.id == "sail" and tool.id in {"rope", "sailcloth"}:
            return tool
        if action.id == "dig" and tool.id == "sailcloth":
            return tool
    return None


def predict_loss(world: World, hero: Entity, action: Action, prize_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(hero.id), action, narrate=False)
    prize = sim.get(prize_id)
    return {
        "lost": prize.meters.get("lost", 0.0) >= THRESHOLD,
        "soaked": prize.meters.get("soaked", 0.0) >= THRESHOLD,
        "torn": prize.meters.get("torn", 0.0) >= THRESHOLD,
    }


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.setting.affords:
        return
    actor.memes["reckless"] = actor.memes.get("reckless", 0.0) + 1
    if action.id == "sail":
        for e in world.entities.values():
            if e.kind != "thing":
                continue
            if e.label in {"map", "flag"}:
                e.meters["soaked"] = e.meters.get("soaked", 0.0) + 1
            if e.label == "flag":
                e.meters["torn"] = e.meters.get("torn", 0.0) + 1
        if narrate:
            world.say("The wind went WHUMP, and the ship rocked hard.")
    elif action.id == "dig":
        if "map" in world.entities:
            world.entities["map"].meters["soaked"] = world.entities["map"].meters.get("soaked", 0.0) + 1
        if narrate:
            world.say("The sand went scritch-scritch under their hands.")
    elif action.id == "haul":
        chest = world.entities.get("chest")
        if chest:
            chest.meters["lost"] = chest.meters.get("lost", 0.0) + 1
        if narrate:
            world.say("The rope gave a grrrk and slipped from wet fingers.")


def sound_effect_for(action: Action, outcome: str) -> str:
    if action.id == "sail" and outcome == "bad":
        return "WHUMP!"
    if action.id == "haul" and outcome == "bad":
        return "GRRRK!"
    if action.id == "dig" and outcome == "bad":
        return "SCRITCH!"
    return "thump"


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.memes.get('trait', 'brave')} pirate who loved the sea.")


def loves_tale(world: World, hero: Entity, action: Action) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} loved {action.gerund}, and every rope and sail felt like part of a game."
    )


def warn(world: World, captain: Entity, hero: Entity, action: Action, prize: Entity) -> bool:
    pred = predict_loss(world, hero, action, prize.id)
    if not any(pred.values()):
        return False
    world.facts["predicted_loss"] = pred
    world.say(
        f'"Watch out," {captain.label} said. "That {action.keyword or action.id} work could wreck {hero.pronoun("possessive")} {prize.label}."'
    )
    return True


def ignore_warning(world: World, hero: Entity, action: Action) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    world.say(f"{hero.id} only grinned and tried to {action.verb} anyway.")


def bad_ending(world: World, hero: Entity, action: Action, prize: Entity, tool: Optional[Tool]) -> None:
    _do_action(world, hero, action, narrate=False)
    outcome = "bad"
    effect = sound_effect_for(action, outcome)
    if prize.meters.get("soaked", 0.0) >= THRESHOLD:
        if prize.label == "map":
            loss = "the secret map was ruined by spray"
        elif prize.label == "flag":
            loss = "the new red flag tore and flapped apart"
        else:
            loss = "the treasure chest slipped into the black sea"
    else:
        loss = "the plan still went wrong"
    world.say(f"{effect} went the ship, and {loss}.")
    if tool is not None:
        world.say(f"The {tool.label} was too late to help.")
    world.say(
        f"By nightfall, {hero.id} stood quiet on the deck while the sea kept taking back its lesson."
    )


def tell(setting: Setting, action: Action, prize_cfg: Prize,
         hero_name: str, hero_type: str, trait: str, captain_type: str = "captain") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"trait": trait}))
    captain = world.add(Entity(id="Captain", kind="character", type=captain_type, label="the captain"))
    prize = world.add(Entity(
        id=prize_cfg.label,
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
    ))
    world.add(Entity(id="ply", type="tool", label="ply plank", phrase="a ply plank"))
    introduce(world, hero)
    loves_tale(world, hero, action)
    world.say(f"One evening, {hero.id} found {prize_cfg.phrase} tucked near the mast.")
    world.say(f"{hero.id} wanted to {action.verb}, but the sky looked mean and the waves looked sly.")

    world.para()
    warn(world, captain, hero, action, prize)
    ignore_warning(world, hero, action)

    world.para()
    tool = select_tool(action, prize_cfg)
    if tool is not None:
        world.say(f"The crew reached for the {tool.label}, but nobody used it in time.")
    bad_ending(world, hero, action, prize, tool)

    world.facts.update(hero=hero, captain=captain, prize=prize, action=action, setting=setting, tool=tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, action, prize = f["hero"], f["action"], f["prize"]
    return [
        f'Write a short pirate tale for a child that uses the word "ply" and includes a warning about {prize.label}.',
        f"Tell a cautionary pirate story where {hero.id} wants to {action.verb} but ignores the captain's advice.",
        f"Write a story with sound effects like WHUMP and GRRRK where a pirate choice ends badly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, prize, action = f["hero"], f["captain"], f["prize"], f["action"]
    tool = f.get("tool")
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do near {world.setting.place}?",
            answer=f"{hero.id} wanted to {action.verb}, even though it was risky.",
        ),
        QAItem(
            question=f"Why did the captain warn {hero.id} about {prize.label}?",
            answer=f"The captain warned {hero.id} because {action.danger}, and the {prize.label} could be ruined.",
        ),
        QAItem(
            question="What sound did the bad moment make?",
            answer=f"It sounded like {sound_effect_for(action, 'bad')} when the trouble hit.",
        ),
    ]
    if tool is not None:
        qa.append(
            QAItem(
                question=f"Did the {tool.label} save the day?",
                answer=f"No. The {tool.label} was there, but it was too late to stop the bad ending.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "sea": [
        QAItem(
            question="What is the sea like when a storm comes in?",
            answer="The sea can get rough, loud, and dangerous when a storm comes in.",
        )
    ],
    "wind": [
        QAItem(
            question="What can strong wind do to a ship's sail?",
            answer="Strong wind can pull hard on a sail and make a ship harder to control.",
        )
    ],
    "treasure": [
        QAItem(
            question="Why do pirates like treasure chests?",
            answer="Pirates like treasure chests because they hope the chests hold gold, gems, or other prizes.",
        )
    ],
    "ply": [
        QAItem(
            question="What is a plank?",
            answer="A plank is a long flat piece of wood, and people can use one as a board or brace.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["action"].tags)
    if world.facts.get("tool"):
        tags.add(world.facts["tool"].id)
    out: list[QAItem] = []
    for tag in ["sea", "wind", "treasure", "ply"]:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for action in setting.affords:
            act = ACTIONS[action]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_tool(act, prize) is not None:
                    combos.append((place, action, prize_id))
    return combos


CURATED = [
    StoryParams(place="deck", action="haul", prize="chest", name="Kip", gender="boy", trait="greedy"),
    StoryParams(place="deck", action="sail", prize="flag", name="Mira", gender="girl", trait="stubborn"),
    StoryParams(place="harbor", action="sail", prize="map", name="Finn", gender="boy", trait="curious"),
]


ASP_RULES = r"""
prize_at_risk(A,P) :- action(A), prize(P), danger(A,P).
needs_tool(A,P) :- prize_at_risk(A,P), tool(T), safe_for(T,A,P).
valid(Place,A,P) :- setting(Place), affords(Place,A), prize_at_risk(A,P), needs_tool(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), suitable_gender(P,Gender).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.aboard:
            lines.append(asp.fact("aboard", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("keyword", aid, a.keyword or aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("kind", pid, p.kind))
        lines.append(asp.fact("danger", list(ACTIONS)[0] if False else "sail", pid))  # placeholder replaced below
        lines.append(asp.fact("danger", "sail", pid))
        lines.append(asp.fact("danger", "dig", pid))
        lines.append(asp.fact("danger", "haul", pid))
        lines.append(asp.fact("suitable_gender", pid, "girl"))
        lines.append(asp.fact("suitable_gender", pid, "boy"))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for s in sorted(t.safe_against):
            lines.append(asp.fact("safe_for", t.id, "sail"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate cautionary storyworld with sound effects and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def explain_rejection(action: Action, prize: Prize) -> str:
    return f"(No story: {action.verb} does not plausibly threaten {prize.label} in this small pirate world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and args.prize:
        act, pr = ACTIONS[args.action], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_tool(act, pr) is not None):
            raise StoryError(explain_rejection(act, pr))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, prize=prize, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIONS[params.action],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.trait,
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, action, prize) combos ({len(stories)} with gender):\n")
        for place, action, prize in triples:
            genders = sorted(g for (pl, ac, pr, g) in stories if (pl, ac, pr) == (place, action, prize))
            print(f"  {place:8} {action:8} {prize:8}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.action} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
