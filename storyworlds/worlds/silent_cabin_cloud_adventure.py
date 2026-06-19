#!/usr/bin/env python3
"""
storyworlds/worlds/silent_cabin_cloud_adventure.py
==================================================

A standalone story world for the seed:

    Words: silent cabin, quiet cloud
    Features: Moral Value
    Style: Adventure

The domain is a mountain-cabin adventure.  A child wants to reach a lookout, a
quiet cloud hides the trail, and the guide's moral rule is tested: only kind,
visible, and safety-preserving responses are allowed.  The cloud is a physical
carrier for mist and an emotional carrier for loneliness; when the child helps
it, the trail clears and the moral is earned by state rather than pasted on.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Cabin:
    id: str
    phrase: str
    trail: str
    landmark: str
    visibility: int
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Cloud:
    id: str
    phrase: str
    mood: str
    mist: int
    need: str
    gift: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    phrase: str
    reason: str
    need_visibility: int
    reward: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Choice:
    id: str
    label: str
    kindness: int
    clears_mist: int
    risk: int
    line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, cabin: Cabin) -> None:
        self.cabin = cabin
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
        clone = World(self.cabin)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_cloud_blocks(world: World) -> list[str]:
    cloud = world.entities.get("cloud")
    trail = world.entities.get("trail")
    if not cloud or not trail:
        return []
    if cloud.meters["mist"] < THRESHOLD:
        return []
    sig = ("blocked", trail.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    trail.meters["hidden"] += 1
    return ["__blocked__"]


def _r_kindness_clears(world: World) -> list[str]:
    cloud = world.entities.get("cloud")
    trail = world.entities.get("trail")
    hero = world.entities.get("hero")
    if not cloud or not trail or not hero:
        return []
    if cloud.memes["comforted"] < THRESHOLD:
        return []
    sig = ("cleared", cloud.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cloud.meters["mist"] = max(0.0, cloud.meters["mist"] - cloud.meters["clearing"])
    cloud.memes["lonely"] = 0.0
    if cloud.meters["mist"] < THRESHOLD:
        trail.meters["hidden"] = 0.0
        trail.meters["visible"] += 1
        hero.memes["moral"] += 1
    return ["__cleared__"]


def _r_safe_progress(world: World) -> list[str]:
    trail = world.entities.get("trail")
    hero = world.entities.get("hero")
    if not trail or not hero:
        return []
    if trail.meters["visible"] < THRESHOLD or hero.memes["moral"] < THRESHOLD:
        return []
    sig = ("progress", trail.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["reached_goal"] += 1
    return ["__progress__"]


CAUSAL_RULES = [
    Rule("cloud_blocks", "physical", _r_cloud_blocks),
    Rule("kindness_clears", "social", _r_kindness_clears),
    Rule("safe_progress", "physical", _r_safe_progress),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def cloud_blocks(cabin: Cabin, cloud: Cloud, goal: Goal) -> bool:
    return cloud.mist > cabin.visibility - goal.need_visibility


def sensible(choice: Choice) -> bool:
    return choice.kindness >= SENSE_MIN and choice.risk <= 1 and choice.clears_mist >= 1


def compatible(cabin: Cabin, cloud: Cloud, goal: Goal, choice: Choice) -> bool:
    return (goal.id in cabin.affords and cloud_blocks(cabin, cloud, goal)
            and sensible(choice) and choice.clears_mist >= cloud.mist)


def predict_path(world: World, cloud: Cloud, goal: Goal) -> dict:
    sim = world.copy()
    sim.get("cloud").meters["mist"] += cloud.mist
    propagate(sim, narrate=False)
    return {
        "hidden": sim.get("trail").meters["hidden"] >= THRESHOLD,
        "need_visibility": goal.need_visibility,
        "mist": cloud.mist,
    }


def introduce(world: World, hero: Entity, guide: Entity) -> None:
    world.say(
        f"Once upon a time, {hero.id} stayed with {hero.pronoun('possessive')} "
        f"{guide.label_word} in {world.cabin.phrase}. The cabin was so still that "
        f"even the kettle seemed to whisper."
    )


def set_goal(world: World, hero: Entity, goal: Goal) -> None:
    hero.memes["adventure"] += 1
    world.say(
        f"{hero.id} wanted an adventure: {hero.pronoun()} hoped to reach {goal.phrase} "
        f"because {goal.reason}."
    )


def meet_cloud(world: World, hero: Entity, guide: Entity, cloud: Cloud, goal: Goal) -> None:
    cloud_ent = world.get("cloud")
    cloud_ent.meters["mist"] += cloud.mist
    cloud_ent.memes["lonely"] += 1
    pred = predict_path(world, cloud, goal)
    world.facts["prediction"] = pred
    propagate(world, narrate=False)
    world.say(
        f"At the start of {world.cabin.trail}, {cloud.phrase} rested low over "
        f"{world.cabin.landmark}. It was a quiet cloud, and it made the path hard to see."
    )
    world.say(
        f'"If we hurry through that mist, we may lose the trail," '
        f'{hero.pronoun("possessive")} {guide.label_word} said. '
        f'"A quiet thing may still need kindness."'
    )


def choose(world: World, hero: Entity, guide: Entity, cloud: Cloud, choice: Choice) -> None:
    hero.memes["desire"] += 1
    cloud_ent = world.get("cloud")
    world.say(
        f"{hero.id} wanted to rush ahead, but {hero.pronoun()} remembered the words "
        f"from the silent cabin. Instead, {choice.line}"
    )
    hero.memes["kindness"] += choice.kindness
    cloud_ent.memes["comforted"] += choice.kindness
    cloud_ent.meters["clearing"] += choice.clears_mist
    if choice.risk:
        hero.memes["worry"] += choice.risk
    propagate(world, narrate=False)


def resolve(world: World, hero: Entity, guide: Entity, cloud: Cloud, goal: Goal) -> None:
    cloud_ent = world.get("cloud")
    if cloud_ent.meters["mist"] < THRESHOLD:
        world.say(
            f"The quiet cloud loosened into silver threads. A little opening appeared, "
            f"and the trail shone safely ahead."
        )
    if hero.meters["reached_goal"] >= THRESHOLD:
        world.say(
            f"{hero.id} and {hero.pronoun('possessive')} {guide.label_word} "
            f"followed the clear path to {goal.phrase}. "
            f"There they found {goal.reward}, and {hero.id} understood the moral: "
            f"kindness can be the bravest part of an adventure."
        )


def tell(cabin: Cabin, cloud: Cloud, goal: Goal, choice: Choice,
         hero_name: str, hero_gender: str, guide_type: str, trait: str) -> World:
    world = World(cabin)
    hero = world.add(Entity("hero", kind="character", type=hero_gender,
                            label=hero_name, traits=[trait], role="hero"))
    hero.id = hero_name
    world.entities["hero"] = hero
    guide = world.add(Entity("Guide", kind="character", type=guide_type,
                             label="the guide", role="guide"))
    world.add(Entity("trail", type="trail", label=cabin.trail))
    world.add(Entity("cloud", type="cloud", label=cloud.phrase))
    introduce(world, hero, guide)
    set_goal(world, hero, goal)
    world.para()
    meet_cloud(world, hero, guide, cloud, goal)
    world.para()
    choose(world, hero, guide, cloud, choice)
    resolve(world, hero, guide, cloud, goal)
    world.facts.update(hero=hero, guide=guide, cabin=cabin, cloud=cloud, goal=goal,
                       choice=choice, reached=hero.meters["reached_goal"] >= THRESHOLD,
                       moral=hero.memes["moral"] >= THRESHOLD,
                       hidden=world.get("trail").meters["hidden"] >= THRESHOLD)
    return world


CABINS = {
    "pine_cabin": Cabin("pine_cabin", "a silent cabin under tall pines", "Pine Needle Trail",
                        "the ferny steps", 2, {"lookout", "echo_bridge"}, {"cabin", "trail"}),
    "moon_cabin": Cabin("moon_cabin", "a silent cabin beside Moon Lake", "Moon Lake Trail",
                        "the wet stepping stones", 1, {"lookout", "star_meadow"}, {"cabin", "trail"}),
    "ridge_cabin": Cabin("ridge_cabin", "a silent cabin on the high ridge", "Ridge Trail",
                         "the narrow switchback", 3, {"echo_bridge", "star_meadow"}, {"cabin", "mountain"}),
}

CLOUDS = {
    "quiet_cloud": Cloud("quiet_cloud", "a quiet cloud", "lonely", 2,
                         "a song soft enough not to scare it", "a cool pearl of rain",
                         {"cloud", "mist"}),
    "shy_cloud": Cloud("shy_cloud", "a shy gray cloud", "shy", 1,
                       "a patient greeting", "a rainbow blink", {"cloud", "mist"}),
    "heavy_cloud": Cloud("heavy_cloud", "a heavy quiet cloud", "tired", 3,
                         "help lifting its sadness", "three bright drops", {"cloud", "mist"}),
}

GOALS = {
    "lookout": Goal("lookout", "the sunrise lookout", "the first gold light touched it",
                    1, "the whole valley glowing below", {"sunrise", "adventure"}),
    "echo_bridge": Goal("echo_bridge", "Echo Bridge", "a kind echo was said to live there",
                        2, "an echo that answered kindly", {"echo", "adventure"}),
    "star_meadow": Goal("star_meadow", "Star Meadow", "blue flowers opened there before noon",
                        2, "a meadow full of tiny blue stars", {"flowers", "adventure"}),
}

CHOICES = {
    "sing_softly": Choice("sing_softly", "sing softly", 3, 2, 0,
                          f'{ "{hero}" } sang a tiny song and promised not to push the cloud away.',
                          {"kindness", "song"}),
    "share_scarf": Choice("share_scarf", "share a warm scarf", 3, 2, 0,
                          f'{ "{hero}" } held up a warm scarf so the cloud could rest on it.',
                          {"kindness", "sharing"}),
    "wait_patiently": Choice("wait_patiently", "wait patiently", 2, 1, 0,
                             f'{ "{hero}" } sat on a stump and waited until the cloud felt ready.',
                             {"kindness", "patience"}),
    "chase_cloud": Choice("chase_cloud", "chase the cloud", 0, 1, 2,
                          f'{ "{hero}" } waved a stick and tried to chase the cloud away.',
                          {"risky"}),
    "run_blindly": Choice("run_blindly", "run through the mist", 0, 0, 3,
                          f'{ "{hero}" } tried to run through the mist without looking.',
                          {"risky"}),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Sam", "Leo", "Finn", "Theo"]
TRAITS = ["curious", "brave", "gentle", "eager", "thoughtful"]


def choice_line(choice: Choice, hero: Entity) -> str:
    return choice.line.replace("{hero}", hero.id)


# Patch the templated lines into plain text at runtime without adding another
# field type. This keeps the registries compact and deterministic.
def _choice_with_line(choice: Choice, hero: Entity) -> Choice:
    return Choice(choice.id, choice.label, choice.kindness, choice.clears_mist,
                  choice.risk, choice_line(choice, hero), set(choice.tags))


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for cid, cabin in CABINS.items():
        for cloud_id, cloud in CLOUDS.items():
            for goal_id, goal in GOALS.items():
                for choice_id, choice in CHOICES.items():
                    if compatible(cabin, cloud, goal, choice):
                        out.append((cid, cloud_id, goal_id, choice_id))
    return sorted(out)


@dataclass
class StoryParams:
    cabin: str
    cloud: str
    goal: str
    choice: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "cabin": [("What is a cabin?",
               "A cabin is a small house, often in the woods or mountains. It can be a quiet place to rest before an adventure.")],
    "cloud": [("What is a cloud?",
               "A cloud is made of many tiny drops of water or ice floating in the sky.")],
    "mist": [("What is mist?",
              "Mist is like a thin cloud near the ground. It can make paths hard to see.")],
    "trail": [("Why should hikers stay on a trail?",
               "A trail helps hikers know the safe way to go. Leaving it in mist can make someone lost.")],
    "kindness": [("Why is kindness important?",
                  "Kindness helps others feel safe and seen. It can solve problems without making anyone smaller or scared.")],
    "patience": [("Why can waiting be wise?",
                  "Waiting gives people time to see clearly and choose safely. It is sometimes braver than rushing.")],
}
KNOWLEDGE_ORDER = ["cabin", "cloud", "mist", "trail", "kindness", "patience"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, cabin, cloud, goal = f["hero"], f["cabin"], f["cloud"], f["goal"]
    return [
        'Write an adventure story for young children that includes "silent cabin" and "quiet cloud".',
        f"Tell a moral-value story where {hero.id} leaves {cabin.phrase}, meets {cloud.phrase}, "
        f"and learns kindness on the way to {goal.phrase}.",
        "Write a gentle adventure where the hero cannot rush through mist and must choose a kind action.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, guide, cabin, cloud, goal, choice = (f["hero"], f["guide"], f["cabin"],
                                              f["cloud"], f["goal"], f["choice"])
    pred = f.get("prediction", {})
    return [
        ("Where did the adventure begin?",
         f"The adventure began in {cabin.phrase}. It was quiet enough that {hero.id} noticed small sounds."),
        ("What blocked the trail?",
         f"{cloud.phrase.capitalize()} made mist over {cabin.landmark}. The world model predicted the trail would be hidden because the mist was too thick for the goal."),
        ("What choice did the hero make?",
         f"{hero.id} chose to {choice.label}. That was kind and safe, so it comforted the cloud instead of scaring it."),
        ("What moral value did the story teach?",
         "The story taught that kindness and patience can be part of courage. The path cleared only after the quiet cloud was treated gently."),
        ("Did the hero reach the goal?",
         f"Yes. After the mist cleared, {hero.id} and {hero.pronoun('possessive')} {guide.label_word} reached {goal.phrase} and found {goal.reward}."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["cabin"].tags) | set(world.facts["cloud"].tags) | set(world.facts["goal"].tags) | set(world.facts["choice"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    lines += [f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("pine_cabin", "quiet_cloud", "lookout", "sing_softly", "Mia", "girl", "aunt", "curious"),
    StoryParams("moon_cabin", "shy_cloud", "lookout", "wait_patiently", "Ben", "boy", "father", "brave"),
    StoryParams("pine_cabin", "shy_cloud", "echo_bridge", "wait_patiently", "Lily", "girl", "mother", "gentle"),
    StoryParams("ridge_cabin", "quiet_cloud", "star_meadow", "sing_softly", "Sam", "boy", "uncle", "thoughtful"),
]


def explain_rejection(cabin: Cabin, cloud: Cloud, goal: Goal, choice: Choice) -> str:
    if goal.id not in cabin.affords:
        return f"(No story: {goal.phrase} is not reached from {cabin.phrase}.)"
    if not cloud_blocks(cabin, cloud, goal):
        return f"(No story: {cloud.phrase} does not hide the route enough to create the moral test.)"
    if choice.kindness < SENSE_MIN:
        return f"(No story: '{choice.label}' is not kind enough for this moral-value world.)"
    if choice.risk > 1:
        return f"(No story: '{choice.label}' is too risky in mist; the adventure must stay safe.)"
    if choice.clears_mist < 1:
        return f"(No story: '{choice.label}' does not actually help the quiet cloud clear the trail.)"
    if choice.clears_mist < cloud.mist:
        return f"(No story: '{choice.label}' is kind, but it does not clear enough mist for {goal.phrase}.)"
    return "(No story: this cabin-cloud adventure is not compatible.)"


ASP_RULES = r"""
blocks(Cabin,Cloud,Goal) :- mist(Cloud,M), visibility(Cabin,V),
                            goal_visibility(Goal,N), M > V - N.
sensible(Choice) :- kindness(Choice,K), sense_min(Min), K >= Min,
                    risk(Choice,R), R <= 1, clears(Choice,Clear), Clear >= 1.
valid(Cabin,Cloud,Goal,Choice) :- cabin(Cabin), cloud(Cloud), goal(Goal), choice(Choice),
                                  affords(Cabin,Goal), blocks(Cabin,Cloud,Goal),
                                  sensible(Choice), clears(Choice,Clear),
                                  mist(Cloud,M), Clear >= M.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, cabin in CABINS.items():
        lines.append(asp.fact("cabin", cid))
        lines.append(asp.fact("visibility", cid, cabin.visibility))
        for goal in sorted(cabin.affords):
            lines.append(asp.fact("affords", cid, goal))
    for cloud_id, cloud in CLOUDS.items():
        lines.append(asp.fact("cloud", cloud_id))
        lines.append(asp.fact("mist", cloud_id, cloud.mist))
    for goal_id, goal in GOALS.items():
        lines.append(asp.fact("goal", goal_id))
        lines.append(asp.fact("goal_visibility", goal_id, goal.need_visibility))
    for choice_id, choice in CHOICES.items():
        lines.append(asp.fact("choice", choice_id))
        lines.append(asp.fact("kindness", choice_id, choice.kindness))
        lines.append(asp.fact("clears", choice_id, choice.clears_mist))
        lines.append(asp.fact("risk", choice_id, choice.risk))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
    ap = argparse.ArgumentParser(description="Story world: silent cabin, quiet cloud, moral adventure.")
    ap.add_argument("--cabin", choices=CABINS)
    ap.add_argument("--cloud", choices=CLOUDS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["mother", "father", "aunt", "uncle"])
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
    if args.cabin and args.cloud and args.goal and args.choice:
        cabin, cloud, goal, choice = CABINS[args.cabin], CLOUDS[args.cloud], GOALS[args.goal], CHOICES[args.choice]
        if not compatible(cabin, cloud, goal, choice):
            raise StoryError(explain_rejection(cabin, cloud, goal, choice))
    combos = [c for c in valid_combos()
              if (args.cabin is None or c[0] == args.cabin)
              and (args.cloud is None or c[1] == args.cloud)
              and (args.goal is None or c[2] == args.goal)
              and (args.choice is None or c[3] == args.choice)]
    if not combos:
        raise StoryError("(No valid silent-cabin cloud adventure matches the given options.)")
    cabin, cloud, goal, choice = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(cabin, cloud, goal, choice, name, gender, guide, trait)


def generate(params: StoryParams) -> StorySample:
    base_choice = CHOICES[params.choice]
    temp_hero = Entity(params.name, kind="character", type=params.gender)
    choice = _choice_with_line(base_choice, temp_hero)
    world = tell(CABINS[params.cabin], CLOUDS[params.cloud], GOALS[params.goal],
                 choice, params.name, params.gender, params.guide, params.trait)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (cabin, cloud, goal, choice) combos:\n")
        for cabin, cloud, goal, choice in combos:
            print(f"  {cabin:12} {cloud:12} {goal:12} {choice}")
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
            header = f"### {p.name}: {p.cloud} at {p.cabin} ({p.choice})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
