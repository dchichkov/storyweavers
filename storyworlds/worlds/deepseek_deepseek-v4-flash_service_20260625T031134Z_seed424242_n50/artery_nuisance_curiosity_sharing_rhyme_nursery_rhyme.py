#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/artery_nuisance_curiosity_sharing_rhyme_nursery_rhyme.py
===========================================================================================================

A standalone story world sketch for a tiny nursery-rhyme domain about curiosity,
sharing, and the nuisance of a blocked artery (a stream that feeds the village).

Core premise: A little child named Pip lives by a singing stream (the "artery" of
the meadow).  One day a fallen log blocks the stream — a real nuisance.  Pip's
curiosity leads them to investigate, and by sharing the problem with a friend they
unblock it together.  The world uses physical meters (water, debris, mud) and
emotional memes (curiosity, sharing, joy, worry).  Every generated story follows
the rhyme-and-reason arc: notice, ask, share, fix.
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

MESS_KINDS = {"wet", "muddy", "leafy", "stuck"}

REGIONS = {"hands", "feet", "legs"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mum", "father": "dad", "aunt": "auntie"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the meadow"
    stream_name: str = "the Singing Stream"
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    what: str
    rhyme_noun: str
    rhyme_verb: str
    fix: str
    mess: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


PROBLEMS = {
    "log": Problem(
        id="log",
        what="a heavy fallen log",
        rhyme_noun="log",
        rhyme_verb="drag",
        fix="pull the log away together",
        mess="stuck",
        zone={"hands"},
        tags={"log", "stuck"},
    ),
    "stones": Problem(
        id="stones",
        what="a pile of slipped stones",
        rhyme_noun="stones",
        rhyme_verb="roll",
        fix="roll the stones aside together",
        mess="leafy",
        zone={"hands"},
        tags={"stones", "leafy"},
    ),
    "mud_slide": Problem(
        id="mud_slide",
        what="a thick wall of mud",
        rhyme_noun="mud",
        rhyme_verb="shove",
        fix="scoop and shovel the mud away",
        mess="muddy",
        zone={"hands", "feet"},
        tags={"mud", "dirty"},
    ),
}


@dataclass
class Friend:
    label: str
    phrase: str
    type: str
    traits: list[str] = field(default_factory=list)


FRIENDS = {
    "rabbit": Friend(label="rabbit", phrase="a quick-eared rabbit by the hedge",
                     type="rabbit", traits=["gentle", "clever"]),
    "duck": Friend(label="duck", phrase="a waddling duck from the pond",
                   type="duck", traits=["cheerful", "helpful"]),
    "badger": Friend(label="badger", phrase="a sleepy badger from the burrow",
                     type="badger", traits=["strong", "kind"]),
}


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.problem_zone: set[str] = set()
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.problem_zone = set(self.problem_zone)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mess_spread(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            sig = ("messed", actor.id, mess)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(
                f"{actor.pronoun('possessive').capitalize()} {actor.label} "
                f"got all {mess}."
            )
    return out


def _r_shared_joy(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["shared_with"] >= THRESHOLD and actor.memes["curiosity"] >= THRESHOLD:
            sig = ("shared_joy", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["joy"] += 1
            out.append(
                f"{actor.id} felt warm and glad, sharing the fix with a friend."
            )
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="mess_spread", tag="physical", apply=_r_mess_spread),
    Rule(name="shared_joy", tag="social", apply=_r_shared_joy),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Verbs / screenplay
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, stream_name: str) -> None:
    world.say(
        f"Down in {world.setting.place}, where the grasses grew tall,"
    )
    world.say(
        f"Little {hero.id} heard {stream_name} call."
    )
    world.say(
        f"The stream was the {world.setting.place}'s happy artery,"
    )
    world.say(
        f"Carrying water for flower and tree."
    )


def curiosity_wakes(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"One morning the stream gave a gurgle and sigh —"
    )
    world.say(
        f"The water stopped running.  \"Oh me, oh my!\""
    )
    world.say(
        f"{hero.id} was curious, wondering why."
    )
    world.say(
        f"\"I'll go and see,\" said {hero.id} with a sigh."
    )


def discover_nuisance(world: World, hero: Entity, problem: Problem) -> None:
    world.problem_zone = set(problem.zone)
    world.say(
        f"There in the stream was {problem.what},"
    )
    world.say(
        f"A terrible, troublesome, clogging {problem.rhyme_noun}!"
    )
    hero.memes["nuisance_found"] += 1
    world.say(
        f"\"What a {problem.rhyme_noun}!\" cried {hero.id}.  \"What a nuisance!  "
        f"The water is stuck — it's a {problem.rhyme_noun} of a fuss!\""
    )


def try_alone(world: World, hero: Entity, problem: Problem) -> None:
    hero.meters[problem.mess] += 1
    hero.memes["frustration"] += 1
    world.say(
        f"{hero.id} pulled and {problem.rhyme_verb}ed, once, twice, thrice —"
    )
    world.say(
        f"But {problem.rhyme_noun} was heavy, not very nice."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} hands got all {problem.mess} "
        f"and muddy and sore,"
    )
    propagate(world)
    world.say(
        f"\"I cannot do this alone any more.\""
    )


def share_problem(world: World, hero: Entity, friend: Entity, problem: Problem) -> None:
    hero.memes["shared_with"] += 1
    friend.memes["shared_with"] += 1
    world.say(
        f"Then {hero.id} saw {friend.label} nearby,"
    )
    world.say(
        f"\"Come here!\" called {hero.id} with a curious cry."
    )
    world.say(
        f"\"The stream is all blocked, the water won't run —"
    )
    world.say(
        f"Can you help me, {friend.label}?  It won't be no fun"
    )
    world.say(
        f"If the {world.setting.place} goes thirsty today."
    )
    world.say(
        f"Let's {problem.fix} and save the day!\""
    )


def fix_together(world: World, hero: Entity, friend: Entity, problem: Problem) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["frustration"] = 0.0
    hero.meters[problem.mess] = 0.0
    world.say(
        f"Together they tugged and {problem.rhyme_verb}ed with all their might,"
    )
    world.say(
        f"Working as partners from morning till night —"
    )
    world.say(
        f"Well, just a short while, but long enough to see"
    )
    world.say(
        f"The {problem.rhyme_noun} give way and the water run free!"
    )
    propagate(world)
    world.say(
        f"The stream sang again — {world.setting.stream_name} flowed,"
    )
    world.say(
        f"\"Thank you!\" it splashed.  \"Thank you!\" it crowed."
    )
    world.say(
        f"{hero.id} and {friend.label} stood side by side,"
    )
    world.say(
        f"Curiosity and sharing, with nothing to hide."
    )
    world.say(
        f"The {world.setting.place} was saved, the nuisance was gone,"
    )
    world.say(
        f"And the water went singing from dawn till dusk on."
    )


# ---------------------------------------------------------------------------
# The screenplay: a nursery-rhyme-shaped three-act.
# ---------------------------------------------------------------------------
def tell(setting: Setting, problem: Problem, friend_cfg: Friend,
         hero_name: str = "Pip", hero_type: str = "girl") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        label=hero_name,
        traits=["curious", "stubborn"],
    ))
    friend = world.add(Entity(
        id=friend_cfg.label, kind="character", type=friend_cfg.type,
        label=friend_cfg.label, phrase=friend_cfg.phrase,
        traits=friend_cfg.traits,
    ))

    # Act 1: The artery sings
    introduce(world, hero, setting.stream_name)
    world.para()

    # Act 2: Curiosity finds the nuisance
    curiosity_wakes(world, hero, problem)
    discover_nuisance(world, hero, problem)
    try_alone(world, hero, problem)
    world.para()

    # Act 3: Sharing the fix
    share_problem(world, hero, friend, problem)
    fix_together(world, hero, friend, problem)

    world.facts.update(hero=hero, friend=friend, problem=problem,
                       setting=setting, friend_cfg=friend_cfg)
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the meadow", stream_name="the Singing Stream",
                      affords={"log", "stones", "mud_slide"}),
    "woodland": Setting(place="the woodland", stream_name="the Twinkly Brook",
                        affords={"log", "stones"}),
    "valley": Setting(place="the valley", stream_name="the Happy River",
                      affords={"stones", "mud_slide"}),
}


GIRL_NAMES = ["Pip", "Tilly", "Rose", "Nell", "Posy"]
BOY_NAMES = ["Tom", "Finn", "Jake", "Pip", "Ned"]
TRAITS = ["curious", "stubborn", "cheerful", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(place, problem, friend) triples."""
    combos = []
    for place, setting in SETTINGS.items():
        for prob_id in setting.affords:
            for friend_id in FRIENDS:
                combos.append((place, prob_id, friend_id))
    return combos


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    friend: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "log": [("What is a log?",
             "A log is a thick piece of wood that has fallen from a tree. "
             "Sometimes logs block streams.")],
    "stones": [("Why do stones sometimes block water?",
                "Stones can slip into a stream when the bank gets soft, "
                "and they make a dam that stops the water.")],
    "mud": [("What happens when mud blocks a stream?",
             "Mud can make the water slow down or stop. Then the stream "
             "cannot carry water to the plants and animals.")],
    "stuck": [("What does 'stuck' mean?",
               "Stuck means something cannot move, like a log that is "
               "wedged tight in a stream.")],
    "leafy": [("What does 'leafy' mean?",
               "Leafy means full of leaves. A leafy blockage is packed "
               "with wet leaves and twigs.")],
    "curiosity": [("What is curiosity?",
                   "Curiosity is the feeling of wanting to know something. "
                   "It makes you ask 'why' and look for answers.")],
    "sharing": [("Why is sharing good?",
                 "Sharing is good because it helps people work together. "
                 "When you share a problem, it becomes easier to solve.")],
    "rabbit": [("What kind of animal is a rabbit?",
                "A rabbit is a small furry animal with long ears that "
                "lives in a burrow or under hedges.")],
    "duck": [("What kind of animal is a duck?",
              "A duck is a bird that swims on ponds, with a flat beak "
              "and webbed feet.")],
    "badger": [("What kind of animal is a badger?",
                "A badger is a strong, furry animal with black-and-white "
                "stripes on its face. It lives in a sett.")],
}
KNOWLEDGE_ORDER = ["log", "stones", "mud", "stuck", "leafy",
                   "curiosity", "sharing",
                   "rabbit", "duck", "badger"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, prob, friend = f["hero"], f["problem"], f["friend_cfg"]
    return [
        f'Write a nursery-rhyme story for a 3-to-5-year-old about a child '
        f'named {hero.id} who finds a {prob.rhyme_noun} blocking a stream.',
        f'A short rhyming tale where {hero.id} shares the problem of a blocked '
        f'artery with a {friend.label} and they fix it together.',
        f'Include the words "artery" and "nuisance" in a gentle story about '
        f'curiosity and sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, prob, friend = f["hero"], f["problem"], f["friend_cfg"]
    stream = world.setting.stream_name
    place = world.setting.place
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Why did {hero.id} go to {stream} in {place}?"
            ),
            answer=(
                f"{hero.id} went to {stream} because it stopped singing. "
                f"{hero.pronoun('possessive').capitalize()} curiosity made "
                f"{hero.pronoun('object')} wonder why the water had stopped flowing."
            ),
        ),
        QAItem(
            question=(
                f"What did {hero.id} find blocking {stream} in {place}?"
            ),
            answer=(
                f"{hero.id} found {prob.what} blocking the stream. "
                f"It was a real nuisance and the water could not get past."
            ),
        ),
        QAItem(
            question=(
                f"Who helped {hero.id} move the {prob.rhyme_noun} away?"
            ),
            answer=(
                f"A {friend.label} helped {hero.id}. "
                f"The {friend.label} was {friend.phrase} and came to share the work."
            ),
        ),
        QAItem(
            question=(
                f"How did {hero.id} feel after sharing the {prob.rhyme_noun} problem?"
            ),
            answer=(
                f"{hero.id} felt glad and joyful. The nuisance was gone, "
                f"the water sang again, and {hero.pronoun()} had a friend by "
                f"{hero.pronoun('possessive')} side."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["problem"].tags)
    tags.add(f["friend_cfg"].label)
    tags.add("curiosity")
    tags.add("sharing")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", problem="log", friend="rabbit",
                name="Pip", gender="girl", trait="curious"),
    StoryParams(place="valley", problem="stones", friend="badger",
                name="Tom", gender="boy", trait="brave"),
    StoryParams(place="woodland", problem="mud_slide", friend="duck",
                name="Tilly", gender="girl", trait="cheerful"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
affords_place(Place, P) :-
    setting(Place),
    problem(P),
    Place = "meadow";
    Place = "woodland";
    Place = "valley".
has_friend(Place, P, F) :-
    affords_place(Place, P),
    friend(F).
valid(P, F) :- problem(P), friend(F).
valid_story(Place, P, F, Gender) :-
    setting(Place),
    problem(P),
    friend(F),
    wears(Gender, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for p in sorted(s.affords):
            lines.append(asp.fact("affords", pid, p))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
    for fid, fr in FRIENDS.items():
        lines.append(asp.fact("friend", fid))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("wears", g, "any"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = set((p, f) for p in PROBLEMS for f in FRIENDS)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: curiosity, sharing, a blocked artery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    combos = [(p, pr, fr) for p in SETTINGS for pr in SETTINGS[p].affords for fr in FRIENDS
              if (args.place is None or p == args.place)
              and (args.problem is None or pr == args.problem)
              and (args.friend is None or fr == args.friend)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, friend = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, friend=friend,
                       name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROBLEMS[params.problem],
                 FRIENDS[params.friend], params.name, params.gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (problem, friend) combos:\n")
        for p, f in triples:
            print(f"  {p:10} {f:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.name}: {p.problem} at {p.place} (friend: {p.friend})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
