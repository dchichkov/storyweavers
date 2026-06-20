#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/perform_khaki_repetition_quest_mystery_to_solve.py
===================================================================================

A standalone storyworld for a tiny animal-story domain about a performer's quest,
a khaki clue, repeated tries, and a mystery that gets solved by careful animal
work rather than a frozen paragraph.

The core premise:
- An animal hero prepares for a small performance.
- A khaki item becomes the key clue in a mystery.
- Repetition matters: the hero tries again, notices patterns, and follows the
  repeated clue trail.
- The ending proves a state change: the clue is found, the mystery is solved,
  and the performance can go on.

This world follows the Storyweavers contract:
- stdlib only
- uses shared results containers from storyworlds/results.py
- has StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python validity gate plus inline ASP twin
- generated stories are state-driven, child-facing, and complete
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Place:
    id: str
    label: str
    detail: str
    repetition_spot: str
    clue_spot: str


@dataclass
class Performer:
    id: str
    label: str
    sound: str
    costume: str
    title: str
    act: str
    repetition: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    clue: str
    hiding_place: str
    solved_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    search_method: str
    payoff: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Outcome:
    id: str
    sense: int
    finish: str
    qa_finish: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    performer: str
    mystery: str
    quest: str
    outcome: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    guide_name: str
    guide_type: str
    seed: Optional[int] = None


PLACES = {
    "barn": Place("barn", "a sunny barn", "The hay smelled sweet, and the rafters made a cozy stage.", "the straw stage", "the corner behind the feed sacks"),
    "forest": Place("forest", "a quiet forest clearing", "The trees made a round green theater, and birds watched from above.", "the mossy stump stage", "the hollow under the fern"),
    "beach": Place("beach", "a bright beach boardwalk", "The sand sparkled, and the wooden planks felt like a little stage.", "the shell-strewn boardwalk stage", "the bucket pile near the net"),
}

PERFORMERS = {
    "goat_song": Performer("goat_song", "goat song", "baa", "a khaki vest", "perform", "sing a tune", "repeat the chorus", {"animal", "perform", "khaki"}),
    "rabbit_dance": Performer("rabbit_dance", "rabbit dance", "thump", "khaki ribbons", "perform", "spin and hop", "repeat the hop-step", {"animal", "perform", "khaki"}),
    "fox_juggle": Performer("fox_juggle", "fox juggling act", "flip", "a khaki scarf", "perform", "toss pinecones", "repeat the toss", {"animal", "perform", "khaki"}),
}

MYSTERIES = {
    "lost_hat": Mystery("lost_hat", "lost hat", "a khaki hat", "behind the feed sacks", "the khaki hat on the straw", {"khaki", "mystery"}),
    "missing_bell": Mystery("missing_bell", "missing bell", "a khaki ribbon tied to the bell", "under the mossy stump", "the bell with the khaki ribbon", {"khaki", "mystery"}),
    "quiet_mask": Mystery("quiet_mask", "quiet mask", "a khaki cord on the mask strap", "near the bucket pile", "the mask with the khaki cord", {"khaki", "mystery"}),
}

QUESTS = {
    "find_clue": Quest("find_clue", "follow the clue trail", "look again and again", "a steady search"),
    "solve_riddle": Quest("solve_riddle", "solve the little mystery", "check the same spots twice", "the answer in plain sight"),
    "prepare_show": Quest("prepare_show", "get the performance ready", "practice the same step again", "a ready stage"),
}

OUTCOMES = {
    "happy": Outcome("happy", 3, "the mystery was solved, and the show could begin", "solved the mystery and got the show ready"),
    "very_happy": Outcome("very_happy", 4, "the mystery was solved with a cheer, and the whole act shone", "solved the mystery and made the stage shine"),
}

GIRL_NAMES = ["Lily", "Maya", "Nora", "Zoe", "Ruby", "Ella"]
BOY_NAMES = ["Tom", "Finn", "Leo", "Max", "Theo", "Ben"]
GUIDE_NAMES = ["Milo", "Pip", "Sunny", "Dot", "Hazel", "Penny"]
TAGS = ["curious", "careful", "brave", "thoughtful", "gentle"]


def hazard_ok(place: Place, mystery: Mystery, performer: Performer) -> bool:
    return "khaki" in mystery.clue or "khaki" in performer.costume


def sensible_outcomes() -> list[Outcome]:
    return [o for o in OUTCOMES.values() if o.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    if not sensible_outcomes():
        return combos
    for pid, place in PLACES.items():
        for perf in PERFORMERS.values():
            for mid, mystery in MYSTERIES.items():
                for qid in QUESTS:
                    if hazard_ok(place, mystery, perf):
                        combos.append((pid, perf.id, mid, qid))
    return combos


def explain_rejection() -> str:
    return "(No story: this world needs a khaki clue to connect the performance, the quest, and the mystery.)"


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["tries"] < 2:
        return out
    sig = ("repetition", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["confidence"] += 1
    hero.meters["noticed_pattern"] += 1
    out.append("__pattern__")
    return out


def _r_clue_found(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    mystery = world.get("mystery")
    if hero.meters["noticed_pattern"] < THRESHOLD:
        return out
    sig = ("clue", mystery.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mystery.meters["found"] = 1
    out.append("__clue__")
    return out


def _r_solved(world: World) -> list[str]:
    out: list[str] = []
    mystery = world.get("mystery")
    guide = world.get("guide")
    if mystery.meters["found"] < THRESHOLD:
        return out
    sig = ("solved", mystery.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    guide.memes["joy"] += 1
    out.append("__solved__")
    return out


CAUSAL_RULES = [Rule("repetition", _r_repetition), Rule("clue", _r_clue_found), Rule("solved", _r_solved)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_solution(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["tries"] += 2
    propagate(sim, narrate=False)
    return {
        "pattern": sim.get("hero").meters["noticed_pattern"] >= THRESHOLD,
        "solved": sim.get("mystery").meters["found"] >= THRESHOLD,
    }


def intro(world: World, hero: Entity, sidekick: Entity, guide: Entity, place: Place, performer: Performer) -> None:
    world.say(
        f"In {place.label}, {hero.id} the {hero.label} was getting ready to {performer.act}. "
        f"{hero.id} wore {performer.costume}, and {sidekick.id} watched with wide eyes."
    )
    world.say(
        f'"Time to {performer.title}!" {hero.id} said. "{performer.sound}! {performer.sound}!" '
        f"{guide.id} laughed and clapped along.'
    )


def mystery_setup(world: World, mystery: Mystery, quest: Quest, place: Place) -> None:
    world.say(
        f"But something was missing. The little group found a mystery: {mystery.clue}. "
        f"They needed to {quest.goal}, so they began to search {quest.search_method}."
    )
    world.say(
        f"They checked {place.repetition_spot}, then looked there again. Still, the clue stayed hidden."
    )


def repeat_attempt(world: World, hero: Entity, performer: Performer) -> None:
    hero.meters["tries"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} tried once, then tried again. {hero.id} repeated the same careful step and listened for a pattern."
    )


def clue_turn(world: World, hero: Entity, mystery: Mystery, place: Place) -> None:
    hero.meters["tries"] += 1
    hero.memes["care"] += 1
    propagate(world, narrate=False)
    world.say(
        f"On the next try, {hero.id} noticed it: the khaki clue was tucked {place.clue_spot}. "
        f"It matched the mystery and pointed right to {mystery.hiding_place}."
    )


def solve(world: World, guide: Entity, mystery: Mystery, outcome: Outcome) -> None:
    mystery.meters["found"] = 1
    propagate(world, narrate=False)
    guide.memes["pride"] += 1
    world.say(
        f"{guide.id} hurried over and lifted the clue out. Soon the mystery was solved, and {outcome.finish}."
    )


def ending(world: World, hero: Entity, sidekick: Entity, performer: Performer, mystery: Mystery, quest: Quest) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"{hero.id} took a bow, {sidekick.id} smiled, and {performer.repetition} had helped them finish the quest. "
        f"The khaki clue stayed safe in plain view, and the little show could go on."
    )


def tell(place: Place, performer: Performer, mystery: Mystery, quest: Quest, outcome: Outcome,
         hero_name: str, hero_type: str, sidekick_name: str, sidekick_type: str,
         guide_name: str, guide_type: str, hero_tag: str = "curious") -> World:
    world = World()
    hero = world.add(Entity("hero", kind="character", type=hero_type, label="performer", role="hero", traits=[hero_tag]))
    sidekick = world.add(Entity("sidekick", kind="character", type=sidekick_type, label="helper", role="sidekick"))
    guide = world.add(Entity("guide", kind="character", type=guide_type, label="guide", role="guide"))
    world.add(Entity("place", type="place", label=place.label))
    world.add(Entity("performer_cfg", type="performer", label=performer.label))
    world.add(Entity("mystery", type="mystery", label=mystery.label))
    world.add(Entity("quest_cfg", type="quest", label=quest.goal))

    intro(world, hero, sidekick, guide, place, performer)
    world.para()
    mystery_setup(world, mystery, quest, place)
    repeat_attempt(world, hero, performer)
    world.para()
    clue_turn(world, hero, mystery, place)
    solve(world, guide, mystery, outcome)
    world.para()
    ending(world, hero, sidekick, performer, mystery, quest)

    world.facts.update(
        place=place, performer=performer, mystery=mystery, quest=quest, outcome=outcome,
        hero=hero, sidekick=sidekick, guide=guide,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a 3-to-5-year-old that includes the words "perform" and "khaki".',
        f"Tell a gentle quest story where a little animal wants to perform, finds a khaki clue, and solves a mystery by trying again.",
        f"Write a repeated-attempt story with animals, a mystery to solve, and a happy ending where the clue is khaki.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    guide = f["guide"]
    mystery = f["mystery"]
    quest = f["quest"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id}, {sidekick.id}, and {guide.id}. They were working together on a small animal quest."),
        ("What was the hero trying to do?",
         f"{hero.id} was trying to perform and get the little show ready. The quest gave the story a goal to work toward."),
        ("What clue did they find?",
         f"They found a khaki clue that matched the mystery. That clue led them to {mystery.hiding_place}."),
        ("Why did the hero need to try again?",
         f"The first try did not solve the mystery, so {hero.id} repeated the step and looked for a pattern. The second try helped reveal where the clue was hiding."),
        ("How did the story end?",
         f"It ended with the mystery solved and the performance ready to begin. The quest was finished, so everyone could smile at the end."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does it mean to perform?",
         "To perform means to do an act, song, dance, or show for others to watch. Animals in stories can perform too."),
        ("What is khaki?",
         "Khaki is a light brown color. It often looks sandy or dusty."),
        ("What is repetition?",
         "Repetition means doing something again and again. It can help you remember or notice a pattern."),
        ("What is a quest?",
         "A quest is a goal-filled search for something important. In stories, a quest gives the characters a mission."),
        ("What is a mystery?",
         "A mystery is something that is not explained right away. The characters have to look carefully to solve it."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, _ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid, p in PERFORMERS.items():
        lines.append(asp.fact("performer", pid))
        lines.append(asp.fact("perform", pid))
        lines.append(asp.fact("costume", pid, "khaki"))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("khaki_clue", mid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for oid, o in OUTCOMES.items():
        lines.append(asp.fact("outcome", oid))
        lines.append(asp.fact("sense", oid, o.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, F, M, Q) :- place(P), performer(F), mystery(M), quest(Q),
                     perform(F), khaki_clue(M), sense_ok.
sense_ok :- sense_min(M), M >= 2.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, performer=None, mystery=None, quest=None,
            outcome=None, hero_name=None, hero_type=None,
            sidekick_name=None, sidekick_type=None,
            guide_name=None, guide_type=None, seed=None
        ), random.Random(1)))
        assert sample.story.strip()
        print("OK: generate() smoke test produced a story.")
    except Exception as e:
        rc = 1
        print("SMOKE TEST FAILED:", e)
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal-story quest world with repetition, khaki clues, and a solved mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--performer", choices=PERFORMERS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--outcome", choices=OUTCOMES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["rabbit", "goat", "fox", "cat", "bear", "dog"])
    ap.add_argument("--sidekick-name")
    ap.add_argument("--sidekick-type", choices=["rabbit", "goat", "fox", "cat", "bear", "dog"])
    ap.add_argument("--guide-name")
    ap.add_argument("--guide-type", choices=["rabbit", "goat", "fox", "cat", "bear", "dog"])
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
    if not combos:
        raise StoryError(explain_rejection())
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.performer is None or c[1] == args.performer)
        and (args.mystery is None or c[2] == args.mystery)
        and (args.quest is None or c[3] == args.quest)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, performer, mystery, quest = rng.choice(sorted(filtered))
    outcome = args.outcome or rng.choice(sorted(OUTCOMES))
    hero_name = args.hero_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    sidekick_name = args.sidekick_name or rng.choice([n for n in GUIDE_NAMES if n != hero_name])
    guide_name = args.guide_name or rng.choice([n for n in GUIDE_NAMES if n not in {hero_name, sidekick_name}])
    hero_type = args.hero_type or rng.choice(["rabbit", "goat", "fox", "cat", "bear", "dog"])
    sidekick_type = args.sidekick_type or rng.choice(["rabbit", "goat", "fox", "cat", "bear", "dog"])
    guide_type = args.guide_type or rng.choice(["rabbit", "goat", "fox", "cat", "bear", "dog"])
    return StoryParams(place, performer, mystery, quest, outcome, hero_name, hero_type, sidekick_name, sidekick_type, guide_name, guide_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place], PERFORMERS[params.performer], MYSTERIES[params.mystery],
        QUESTS[params.quest], OUTCOMES[params.outcome],
        params.hero_name, params.hero_type, params.sidekick_name, params.sidekick_type,
        params.guide_name, params.guide_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, performer, mystery, quest) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        curated = [
            StoryParams("barn", "goat_song", "lost_hat", "find_clue", "happy", "Lily", "goat", "Pip", "rabbit", "Milo", "fox"),
            StoryParams("forest", "rabbit_dance", "missing_bell", "solve_riddle", "very_happy", "Finn", "rabbit", "Hazel", "cat", "Dot", "goat"),
            StoryParams("beach", "fox_juggle", "quiet_mask", "prepare_show", "happy", "Zoe", "fox", "Sunny", "dog", "Penny", "bear"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
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
