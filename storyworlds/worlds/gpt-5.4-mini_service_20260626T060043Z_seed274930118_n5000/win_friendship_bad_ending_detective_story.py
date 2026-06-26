#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/win_friendship_bad_ending_detective_story.py
===============================================================================================================

A small detective-story world with friendship, a win-hungry case, and a bad ending.

Premise:
- A young detective and a close friend investigate a missing prize.
- The detective wants to win the contest, but suspicion grows.
- The clues are real, the accusation is wrong, and the friendship ends badly.

This is a standalone Storyweavers world script with:
- typed entities carrying physical meters and emotional memes,
- a rule-driven simulation,
- a Python reasonableness gate,
- an inline ASP twin,
- story Q&A and world knowledge Q&A,
- JSON / trace / QA / verify / ASP support.

The story style is close to a child-friendly detective story: clues, notebooks,
footsteps, lamps, a tense accusation, and a final image that proves the change.
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
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = True
    clue_sources: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    verb: str
    clue_word: str
    tension: str
    reveal: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    owner_kind: str
    location: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    case: str
    prize: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None


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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_suspicion(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    friend = world.facts.get("friend")
    if not hero or not friend:
        return out
    h = world.get(hero.id)
    f = world.get(friend.id)
    if h.memes.get("want_win", 0.0) >= THRESHOLD and f.memes.get("secretive", 0.0) >= THRESHOLD:
        sig = ("suspicion", hero.id, friend.id)
        if sig not in world.fired:
            world.fired.add(sig)
            h.memes["suspicion"] = h.memes.get("suspicion", 0.0) + 1
            out.append(f"{hero.pronoun('subject').capitalize()} started to worry that {friend.id} knew more than {hero.pronoun('subject')} said.")
    return out


def _r_conflict(world: World) -> list[str]:
    hero = world.facts.get("hero")
    friend = world.facts.get("friend")
    if not hero or not friend:
        return []
    h = world.get(hero.id)
    f = world.get(friend.id)
    if h.memes.get("suspicion", 0.0) >= THRESHOLD and f.memes.get("hurt", 0.0) >= THRESHOLD:
        sig = ("conflict", hero.id, friend.id)
        if sig not in world.fired:
            world.fired.add(sig)
            h.memes["conflict"] = h.memes.get("conflict", 0.0) + 1
            f.memes["conflict"] = f.memes.get("conflict", 0.0) + 1
            return ["__conflict__"]
    return []


CAUSAL_RULES = [Rule("suspicion", _r_suspicion), Rule("conflict", _r_conflict)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "library": Setting(place="the library", indoors=True, clue_sources={"book", "dust", "ink"}),
    "museum": Setting(place="the museum hallway", indoors=True, clue_sources={"frame", "footprint", "glass"}),
    "school": Setting(place="the school office", indoors=True, clue_sources={"paper", "stamp", "chalk"}),
    "bakery": Setting(place="the bakery back room", indoors=True, clue_sources={"flour", "tray", "crumb"}),
}

CASES = {
    "missing_ribbon": Case(
        id="missing_ribbon",
        verb="find the missing ribbon",
        clue_word="ribbon",
        tension="the contest would be won by whoever brought it back first",
        reveal="the ribbon had been tucked into a book on the high shelf",
        risk="a quick guess could turn a friend into the wrong suspect",
        tags={"clue", "win", "friendship"},
    ),
    "lost_stamp": Case(
        id="lost_stamp",
        verb="find the lost stamp",
        clue_word="stamp",
        tension="the winner would get to lead the class parade",
        reveal="the stamp had fallen behind a cabinet",
        risk="being too eager could ruin trust between friends",
        tags={"clue", "win", "friendship"},
    ),
    "hidden_key": Case(
        id="hidden_key",
        verb="find the hidden key",
        clue_word="key",
        tension="the winner would open the locked prize box",
        reveal="the key was hanging on a nail beside the sink",
        risk="a rushed accusation could break a promise",
        tags={"clue", "win", "friendship"},
    ),
}

PRIZES = {
    "ribbon": Prize(
        id="ribbon",
        label="ribbon",
        phrase="a bright blue ribbon",
        owner_kind="contest",
        location="high shelf",
        tags={"ribbon"},
    ),
    "stamp": Prize(
        id="stamp",
        label="stamp",
        phrase="the gold stamp",
        owner_kind="office",
        location="cabinet",
        tags={"stamp"},
    ),
    "key": Prize(
        id="key",
        label="key",
        phrase="a little brass key",
        owner_kind="box",
        location="nail",
        tags={"key"},
    ),
}

HERO_NAMES = ["Maya", "Nina", "Eli", "Sam", "Lina", "Theo"]
FRIEND_NAMES = ["Jo", "Ben", "Ari", "Zoe", "Milo", "Tess"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for case_id, case in CASES.items():
            for prize_id, prize in PRIZES.items():
                if case.clue_word == prize_id:
                    combos.append((place, case_id, prize_id))
    return combos


def _do_case(world: World, hero: Entity, friend: Entity, case: Case, prize: Prize, narrate: bool = True) -> None:
    hero.memes["want_win"] = hero.memes.get("want_win", 0.0) + 1
    friend.memes["secretive"] = friend.memes.get("secretive", 0.0) + 1
    if narrate:
        world.say(f"{hero.id} wanted to {case.verb} first, because winning would feel wonderful.")
        world.say(f"{friend.id} noticed the same clues, but said only a little and looked away.")
    if prize.label in case.tags:
        world.facts["case_started"] = True
    propagate(world, narrate=narrate)


def predict_conflict(world: World, hero: Entity, friend: Entity, case: Case, prize: Prize) -> dict:
    sim = world.copy()
    _do_case(sim, sim.get(hero.id), sim.get(friend.id), case, prize, narrate=False)
    h = sim.get(hero.id)
    f = sim.get(friend.id)
    return {
        "conflict": h.memes.get("conflict", 0.0) >= THRESHOLD or f.memes.get("conflict", 0.0) >= THRESHOLD,
        "suspicion": h.memes.get("suspicion", 0.0),
    }


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    trait = next((t for t in hero.traits if t != "young"), "careful")
    world.say(
        f"{hero.id} was a young {trait} detective who kept a notebook in {hero.pronoun('possessive')} pocket."
    )
    world.say(
        f"{friend.id} was {hero.id}'s best friend, and they liked solving small mysteries together."
    )


def setting_line(world: World, case: Case) -> None:
    if world.setting.place == "the library":
        world.say("The shelves were tall and quiet, and the air smelled like old paper and dust.")
    elif world.setting.place == "the museum hallway":
        world.say("The hallway was bright and echoing, with shiny frames lined up like watchful eyes.")
    elif world.setting.place == "the school office":
        world.say("The office was tidy and serious, with neat stacks of paper and a clock that ticked softly.")
    else:
        world.say("The back room was warm and busy, with flour on the counter and crumbs near the tray.")
    world.say(f"They were looking for {case.verb}, and the whole place felt like a clue waiting to be read.")


def clue_search(world: World, hero: Entity, friend: Entity, case: Case, prize: Prize) -> None:
    world.say(
        f"{hero.id} followed a tiny clue word: {case.clue_word}. {hero.id} saw marks, listened carefully, and tried to win the case quickly."
    )
    world.say(
        f"{friend.id} pointed at the hiding place, but the words were soft enough that {hero.id} did not fully trust them."
    )


def accuse(world: World, hero: Entity, friend: Entity, case: Case, prize: Prize) -> None:
    hero.memes["suspicion"] = hero.memes.get("suspicion", 0.0) + 1
    friend.memes["hurt"] = friend.memes.get("hurt", 0.0) + 1
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.id} stopped, pointed at {friend.id}, and said, \"You took it so you could win, didn't you?\""
    )
    world.say(
        f"{friend.id}'s face went still, because the guess was wrong and the friendship felt cold all at once."
    )


def reveal_and_bad_end(world: World, hero: Entity, friend: Entity, case: Case, prize: Prize) -> None:
    world.say(
        f"But the real answer was simple: {case.reveal}."
    )
    world.say(
        f"{hero.id} found {prize.phrase} too late, and the win did not feel sweet anymore."
    )
    world.say(
        f"{friend.id} walked away with tears in {friend.pronoun('possessive')} eyes, and {hero.id} stood alone with the notebook closed."
    )


def tell(setting: Setting, case: Case, prize: Prize, hero_name: str = "Maya", hero_gender: str = "girl",
         friend_name: str = "Ben", friend_gender: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, traits=["young", "careful", "stubborn"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, traits=["young", "helpful"]))
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["case"] = case
    world.facts["prize"] = prize

    introduce(world, hero, friend)
    world.para()
    setting_line(world, case)
    clue_search(world, hero, friend, case, prize)
    _do_case(world, hero, friend, case, prize, narrate=True)
    world.para()
    accuse(world, hero, friend, case, prize)
    reveal_and_bad_end(world, hero, friend, case, prize)
    world.facts["resolved_badly"] = True
    return world


KNOWLEDGE = {
    "ribbon": [
        ("What is a ribbon?", "A ribbon is a strip of cloth used for prizes, gifts, or decorations."),
    ],
    "stamp": [
        ("What is a stamp?", "A stamp is a small mark or label that can show a letter has been paid for or approved."),
    ],
    "key": [
        ("What is a key for?", "A key is used to open a lock so a box, door, or drawer can be unlocked."),
    ],
    "friendship": [
        ("What is friendship?", "Friendship is when people care about each other, help each other, and enjoy being together."),
    ],
    "win": [
        ("What does it mean to win?", "To win means to finish first or do best in a game, contest, or race."),
    ],
    "clue": [
        ("What is a clue?", "A clue is a small piece of information that helps solve a mystery."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    case = f["case"]
    prize = f["prize"]
    return [
        f'Write a short detective story for a young child that includes the word "win" and ends sadly.',
        f"Tell a mystery story where {hero.id} and {friend.id} search for {case.verb}, but a wrong guess hurts their friendship.",
        f"Write a child-friendly detective story about {prize.phrase}, clues, and a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    case: Case = f["case"]
    prize: Prize = f["prize"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who was the story mainly about at {place}?",
            answer=f"The story was about {hero.id}, a young detective, and {friend.id}, {hero.id}'s best friend.",
        ),
        QAItem(
            question=f"What were they trying to do with {prize.phrase}?",
            answer=f"They were trying to {case.verb} while searching for clues in {place}.",
        ),
        QAItem(
            question="Why did the friendship go badly at the end?",
            answer=f"{hero.id} guessed that {friend.id} had taken the prize, but that guess was wrong and it hurt {friend.id}.",
        ),
        QAItem(
            question="Did the detective win the case?",
            answer=f"{hero.id} did find the missing item in the end, so the case was solved, but the ending was still bad because the friendship was damaged.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out: list[QAItem] = []
    for tag in ["clue", "friendship", "win", f["prize"].id]:
        if tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
case_started(H,F) :- want_win(H), secretive(F).
bad_end(H,F) :- suspicion(H,F), hurt(F).
solved_but_bad(H,F) :- case_started(H,F), bad_end(H,F).

#show valid/3.
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for case_id, case in CASES.items():
        lines.append(asp.fact("case", case_id))
        lines.append(asp.fact("clue_word", case_id, case.clue_word))
    for prize_id, prize in PRIZES.items():
        lines.append(asp.fact("prize", prize_id))
        lines.append(asp.fact("prize_label", prize_id, prize.label))
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


def explain_rejection() -> str:
    return "(No story: the chosen detective setup does not make a believable clue chase.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with friendship and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
              if (args.place is None or c[0] == args.place)
              and (args.case is None or c[1] == args.case)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError(explain_rejection())
    place, case_id, prize_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    return StoryParams(
        place=place,
        case=case_id,
        prize=prize_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CASES[params.case],
        PRIZES[params.prize],
        params.hero_name,
        params.hero_gender,
        params.friend_name,
        params.friend_gender,
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
        print(f"{len(triples)} compatible (place, case, prize) combos ({len(stories)} with story form):\n")
        for place, case, prize in triples:
            print(f"  {place:20} {case:16} {prize:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place, case_id, prize_id in valid_combos():
            params = StoryParams(
                place=place,
                case=case_id,
                prize=prize_id,
                hero_name="Maya",
                hero_gender="girl",
                friend_name="Ben",
                friend_gender="boy",
            )
            samples.append(generate(params))
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
            header = f"### {p.hero_name}: {p.case} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
