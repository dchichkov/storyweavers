#!/usr/bin/env python3
"""
A small nursery-rhyme-style story world about a musical quest, a possible
perish risk, and a friendship that adds the right help at the right moment.

The tale shape:
- A little seeker wants to finish a quest.
- A beloved musical thing is in danger of perishing.
- A friend notices, adds help, and together they save the day.

This world is intentionally small and constraint-checked so that every sampled
story reads like a complete, child-facing rhyme with a beginning, turn, and
resolution.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the moonlit meadow"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    line: str
    turn: str
    close: str
    peril: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    line: str
    effect: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


SETTINGS = {
    "meadow": Setting(place="the moonlit meadow", affords={"song", "quest"}),
    "garden": Setting(place="the garden gate", affords={"song", "quest"}),
    "harbor": Setting(place="the harbor steps", affords={"song", "quest"}),
}

QUESTS = {
    "songstone": Quest(
        id="songstone",
        goal="find the songstone",
        line="find the songstone",
        turn="the songstone began to crack and dim",
        close="its bright note rang again",
        peril="perish",
        tags={"musical", "quest", "perish"},
    ),
    "bellflower": Quest(
        id="bellflower",
        goal="gather the bellflower",
        line="gather the bellflower",
        turn="the bellflower drooped and might perish",
        close="its bell-like bloom stood tall again",
        peril="perish",
        tags={"musical", "quest", "perish"},
    ),
    "lullaby_lantern": Quest(
        id="lullaby_lantern",
        goal="carry the lullaby lantern",
        line="carry the lullaby lantern",
        turn="the lantern's song was about to perish",
        close="its gentle glow hummed on",
        peril="perish",
        tags={"musical", "quest", "perish"},
    ),
}

PRIZES = {
    "bell": Prize(label="bell", phrase="a little silver bell", region="hand"),
    "flute": Prize(label="flute", phrase="a tiny flute with ribbons", region="hand"),
    "crown": Prize(label="crown", phrase="a paper crown", region="head"),
}

HELPERS = {
    "friendship": Helper(
        id="friendship",
        label="friendship",
        line="a friend came close and smiled",
        effect="add help",
        tags={"friendship"},
    ),
}

NAMES = {
    "girl": ["Mia", "Luna", "Nora", "Ivy", "Zoe"],
    "boy": ["Theo", "Finn", "Leo", "Max", "Oli"],
}

TRAITS = ["gentle", "brave", "curious", "cheery", "tiny"]

VALID_COMBOS = [
    ("meadow", "songstone", "bell"),
    ("garden", "bellflower", "flute"),
    ("harbor", "lullaby_lantern", "crown"),
]


ASP_RULES = r"""
% A quest is valid when the place affords it and the prize is on the
% appropriate body region for the narrative.
quest_ok(P, Q, R) :- affords(P, Q), prize(R), quest(Q), worn_on(R, hand).
quest_ok(P, Q, R) :- affords(P, Q), prize(R), quest(Q), worn_on(R, head).

% Friendship is the helpful addition when a quest peril is present.
friendship_fix(Q) :- quest(Q), peril(Q).

valid_story(P, Q, R) :- quest_ok(P, Q, R), friendship_fix(Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("peril", qid))
        for t in sorted(q.tags):
            lines.append(asp.fact("tag", qid, t))
        if qid in {"songstone", "bellflower"}:
            lines.append(asp.fact("musical", qid))
    for rid, r in PRIZES.items():
        lines.append(asp.fact("prize", rid))
        lines.append(asp.fact("worn_on", rid, r.region))
    lines.append(asp.fact("helper", "friendship"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid_combos() -> list[tuple[str, str, str]]:
    return list(VALID_COMBOS)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world: musical quest, peril, friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    if args.place and args.quest and args.prize:
        if (args.place, args.quest, args.prize) not in VALID_COMBOS:
            raise StoryError("That combination does not make a reasonable nursery-rhyme quest.")
    combos = [c for c in VALID_COMBOS
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combo matches those options.")
    place, quest, prize = rng.choice(combos)
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.name or rng.choice(NAMES[hero_gender])
    friend_name = args.friend_name or rng.choice(NAMES[friend_gender])
    return StoryParams(
        place=place,
        quest=quest,
        prize=prize,
        hero_name=hero_name,
        hero_type=hero_gender,
        friend_name=friend_name,
        friend_type=friend_gender,
    )


def _intro(world: World, hero: Entity, prize: Entity, quest: Quest) -> None:
    trait = hero.traits[0]
    world.say(
        f"Little {trait} {hero.id} went with a soft step and a bright grin, "
        f"for {hero.pronoun('subject')} loved a musical quest."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} treasure was {prize.phrase}, "
        f"and the little one meant to {quest.line}."
    )


def _turn(world: World, hero: Entity, friend: Entity, quest: Quest, prize: Entity) -> None:
    world.para()
    world.say(
        f"At {world.setting.place}, {hero.id} reached out to {quest.goal}, "
        f"but {quest.turn}."
    )
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"{hero.id} trembled a bit, for if the tune went quiet, the quest might {quest.peril}."
    )
    world.say(
        f"Then {friend.id} came near, and friendship had a way of adding hope."
    )
    friend.memes["care"] = friend.memes.get("care", 0.0) + 1
    world.facts["peril"] = True
    world.facts["turn"] = quest.turn
    world.facts["prize"] = prize


def _resolution(world: World, hero: Entity, friend: Entity, quest: Quest, prize: Entity) -> None:
    world.para()
    world.say(
        f"{friend.id} said, 'I can help,' and together they sang a tiny rhyme."
    )
    world.say(
        f"That little song added steady courage, and {hero.id} held {prize.label} close."
    )
    world.say(
        f"With friendship beside {hero.pronoun('object')}, {quest.close}; "
        f"the quest was not lost after all."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=["little", rng_trait(params.hero_name)],
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_type,
        traits=["kind"],
    ))
    quest = QUESTS[params.quest]
    prize = world.add(Entity(
        id=params.prize,
        kind="thing",
        type=params.prize,
        label=params.prize,
        phrase=PRIZES[params.prize].phrase,
        owner=hero.id,
        caretaker=friend.id,
    ))
    world.facts.update(hero=hero, friend=friend, quest=quest, prize=prize, params=params)
    _intro(world, hero, prize, quest)
    _turn(world, hero, friend, quest, prize)
    _resolution(world, hero, friend, quest, prize)
    return world


def rng_trait(name: str) -> str:
    return TRAITS[sum(ord(c) for c in name) % len(TRAITS)]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    quest = f["quest"]
    prize = f["prize"]
    return [
        f"Write a short nursery rhyme about {hero.id} on a {quest.id} quest with {prize.phrase}.",
        f"Tell a gentle story where friendship adds help when {quest.goal} might perish.",
        f"Write a child-friendly rhyme about a musical quest in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    quest: Quest = f["quest"]
    prize: Entity = f["prize"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {quest.line} in a musical little quest.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel worried when the quest turned hard?",
            answer=f"{hero.id} felt worried because {quest.turn}, so the music might {quest.peril}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} in the end?",
            answer=f"{friend.id} helped by adding friendship and calm, so the quest could finish safely.",
        ),
        QAItem(
            question=f"What happened to {prize.phrase} by the end?",
            answer=f"{prize.phrase.capitalize()} stayed with {hero.id}, and the ending sounded bright again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is the warm bond between people who care about each other and help one another.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task where someone goes looking for something important.",
        ),
        QAItem(
            question="What makes a musical sound?",
            answer="Musical sounds are notes, beats, or tunes that people can sing or play on instruments.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: type={e.type} memes={dict(e.memes)}")
    out.append(f"facts={world.facts}")
    return "\n".join(out)


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


def explain_rejection() -> str:
    return "That story shape would not be a sensible nursery-rhyme quest."


def asp_verify() -> int:
    import asp
    py = set(python_valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid stories.")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only Python:", sorted(py - cl))
    print("Only ASP:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        stories = asp_valid()
        print(f"{len(stories)} compatible stories:")
        for item in stories:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place, quest, prize in VALID_COMBOS:
            p = StoryParams(
                place=place,
                quest=quest,
                prize=prize,
                hero_name=NAMES["girl"][0],
                hero_type="girl",
                friend_name=NAMES["boy"][0],
                friend_type="boy",
                seed=base_seed,
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
