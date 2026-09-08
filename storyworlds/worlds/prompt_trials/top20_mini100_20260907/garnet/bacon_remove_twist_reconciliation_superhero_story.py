#!/usr/bin/env python3
"""A small superhero storyworld about bacon, a twist, and a reconciliation."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    friend: Item
    bacon: Item
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    hero_name: str
    friend_name: str
    place: str
    seed: Optional[int] = None


HEROES = ["Nova", "Comet", "Mira", "Blaze", "Sunny", "Ruby", "Ziggy", "Pip"]
FRIENDS = ["Jules", "Tess", "Nico", "Mina", "Owen", "Lina", "Arlo", "Bea"]
PLACES = ["the rooftop garden", "the city market", "the ferry dock", "the moonlit park", "the downtown bakery"]


ASP_RULES = r"""
#show twist/1.
#show reconcile/1.
#show bacon_safe/1.

twist(H) :- detects_smoke(H).
reconcile(H) :- says_sorry(H), shares_food(H).
bacon_safe(H) :- removes_hot_pan(H).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("detects_smoke", "hero"),
        asp.fact("says_sorry", "hero"),
        asp.fact("shares_food", "hero"),
        asp.fact("removes_hot_pan", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show twist/1.\n#show reconcile/1.\n#show bacon_safe/1."))
    atoms = set((a.name, tuple(x.name if x.type != x.type.Number else x.number for x in a.arguments)) for a in model)
    expected = {("twist", ("hero",)), ("reconcile", ("hero",)), ("bacon_safe", ("hero",))}
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld about bacon, a twist, and reconciliation.")
    ap.add_argument("--hero-name", choices=HEROES)
    ap.add_argument("--friend-name", choices=FRIENDS)
    ap.add_argument("--place", choices=PLACES)
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
    return StoryParams(
        hero_name=args.hero_name or rng.choice(HEROES),
        friend_name=args.friend_name or rng.choice(FRIENDS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    hero = Item(id="hero", label=params.hero_name, phrase=f"hero {params.hero_name}", kind="character")
    friend = Item(id="friend", label=params.friend_name, phrase=params.friend_name, kind="character")
    bacon = Item(id="bacon", label="bacon", phrase="a sizzling strip of bacon", owner=hero.id)
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.hero_name}|{params.friend_name}|{params.place}")
    return World(hero=hero, friend=friend, bacon=bacon, place=params.place, seed=seed)


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record_story(
    world: World,
    *,
    twist: str,
    reconciliation: str,
    trouble: str,
    cause: str,
    resolution: str,
    ending: str,
    lines: list[str],
) -> str:
    world.facts.update(
        twist=twist,
        reconciliation=reconciliation,
        trouble=trouble,
        cause=cause,
        resolution=resolution,
        ending=ending,
    )
    return " ".join(lines)


def _smoke_arc(world: World, rng: random.Random) -> str:
    h, f, p = world.hero.label, world.friend.label, world.place
    twist = "the bacon smoke set off the rooftop alarm and a gust twisted the signal into a false emergency"
    reconciliation = "the hero and friend apologized, then cooked fresh bacon together for the whole block"
    trouble = "the alarm startled neighbors and made the breakfast cart wobble toward the edge"
    cause = "the bacon was left too long in a hot pan while the window was open to a windy rooftop"
    resolution = f"{h} lifted the pan off the flame, used a towel to remove it from the hot burner, and calmed everyone down with a smile"
    ending = "by sunrise, the bacon sat on a blue plate, the alarm was quiet, and the neighbors were laughing again"
    lines = [
        f"At {p}, {h} was cooking bacon for breakfast when the wind whipped across the roof.",
        f"The bacon sizzled, smoked, and then the siren howled. \"Oops,\" said {h}. \"That was a twist I did not want.\"",
        f"{f} rushed over and asked, \"Did the bacon catch fire?\" {h} answered, \"No, but it sure tried to become a superhero signal!\"",
        f"The alarm scared a flock of pigeons, and the breakfast cart began rolling toward the railing.",
        f"{h} reached the pan at once, carefully moved it off the flame, and used a folded towel to remove the hot handle from the table edge.",
        f"\"I'm sorry,\" said {h}. \"I should have watched the bacon more closely.\"",
        f"\"I'm sorry too,\" said {f}. \"I should have warned you about the wind.\" Together they shut the window and set the bacon back on low heat.",
        f"With the trouble cooled off, they shared the finished bacon with the neighbors. By the end of the morning, {ending}.",
    ]
    return _record_story(world, twist=twist, reconciliation=reconciliation, trouble=trouble, cause=cause, resolution=resolution, ending=ending, lines=lines)


def _museum_arc(world: World, rng: random.Random) -> str:
    h, f, p = world.hero.label, world.friend.label, world.place
    twist = "a glass case twisted open when the bacon grease on a donated tray made the latch slip"
    reconciliation = "the hero and friend worked together, apologized to the curator, and cleaned the case before the show opened"
    trouble = "a costume helmet nearly slid out of the case and bumped a display stand"
    cause = "someone had left a lunch tray near the exhibit, and the bacon grease made the latch slick"
    resolution = f"{h} caught the helmet, {f} helped remove the tray from the floor, and both heroes locked the case again"
    ending = "the exhibit stood safe, and the curator waved them goodbye with a grateful grin"
    lines = [
        f"Near {p}, {h} and {f} visited a tiny hero museum before the doors opened.",
        f"They were checking the exhibits when the glass case gave a little click. \"That sounds like a twist,\" said {f}.",
        f"Inside, a shiny costume helmet started sliding toward the floor.",
        f"{h} leaped forward and caught it just in time. \"Bacon grease!\" shouted {f}. \"That lunch tray made the latch slippery!\"",
        f"{h} nodded. \"Let's remove the tray, fix the lock, and tell the curator right away.\"",
        f"The curator thanked them for being honest, and {h} said, \"I'm sorry we touched the case before asking.\"",
        f"{f} added, \"We wanted to help, not cause a mess.\" The curator smiled and handed them a cloth for cleaning.",
        f"By opening time, {ending}. The room felt calm again, like a cape folded neatly on a chair.",
    ]
    return _record_story(world, twist=twist, reconciliation=reconciliation, trouble=trouble, cause=cause, resolution=resolution, ending=ending, lines=lines)


def _park_arc(world: World, rng: random.Random) -> str:
    h, f, p = world.hero.label, world.friend.label, world.place
    twist = "a squirrel twisted the bacon strip away from the picnic tray and dashed toward the fountain"
    reconciliation = "the hero laughed, the friend laughed, and they shared the rest of the breakfast without arguing"
    trouble = "the runaway strip tempted every hungry gull in the park"
    cause = "the bacon was left uncovered on the picnic table for just one second too long"
    resolution = f"{h} and {f} chased the squirrel only to remove the bacon from danger by setting out a safer lunch under a lid"
    ending = "the gulls drifted away, the squirrel dropped the prize, and the picnic turned into a peaceful brunch"
    lines = [
        f"At {p}, {h} and {f} set a bacon snack on a picnic table beside the fountain.",
        f"Before they could sit down, a squirrel darted in and twisted the bacon right off the plate. \"Hey!\" cried {h}.",
        f"\"That squirrel moves like a tiny villain,\" said {f}. \"Or a very fast hero,\" {h} answered, trying not to laugh.",
        f"The squirrel raced toward the fountain, and a dozen gulls began circling overhead.",
        f"{h} ran after the thief, then stopped and thought. The best move was not a big chase; it was to remove the temptation.",
        f"So {h} lifted the rest of the bacon into a covered lunch box while {f} scattered crumbs far from the table.",
        f"\"Sorry for blaming you,\" said {h} to {f}. \"I got bossy for a minute.\" \"Sorry for teasing,\" {f} said. \"Let's fix the picnic together.\"",
        f"By the time the sun climbed higher, {ending}. Even the squirrel looked pleased with the whole adventure.",
    ]
    return _record_story(world, twist=twist, reconciliation=reconciliation, trouble=trouble, cause=cause, resolution=resolution, ending=ending, lines=lines)


def _train_arc(world: World, rng: random.Random) -> str:
    h, f, p = world.hero.label, world.friend.label, world.place
    twist = "the bacon in the sandwich twisted loose from the wrapper and slid under a train bench"
    reconciliation = "the hero and friend worked side by side, apologized for the rush, and shared the rescued snack"
    trouble = "the sandwich rolled toward the tracks as the station bell rang"
    cause = "the wrapper was folded badly, so the bacon kept slipping whenever the train shook"
    resolution = f"{h} knelt down, {f} held the bag, and together they removed the loose wrapper before the next train arrived"
    ending = "the bacon stayed put in a sturdier wrap, and the two friends rode home smiling"
    lines = [
        f"At {p}, {h} and {f} waited near the station bench with a bacon sandwich for the ride home.",
        f"The train rumble shook the paper wrap, and the bacon did a silly twist, sliding straight under the bench.",
        f"\"Oh no,\" said {f}. \"The sandwich is trying to escape!\" {h} pointed at the tracks and said, \"Then we should save it now.\"",
        f"The station bell rang. A worker shouted for everyone to step back from the edge.",
        f"{h} crouched carefully, and {f} held the bag open. They removed the loose wrapper and found the bacon resting beside a dropped ticket.",
        f"\"I'm sorry I packed it badly,\" {h} said. \"I'm sorry I laughed first,\" said {f}.",
        f"They rewrapped the snack with clean paper and thanked the station worker for waiting. The train whistle blew, but the bacon stayed safe.",
        f"By the end of the ride, {ending}. The sandwich no longer twisted free, and neither did their teamwork.",
    ]
    return _record_story(world, twist=twist, reconciliation=reconciliation, trouble=trouble, cause=cause, resolution=resolution, ending=ending, lines=lines)


ARC_BUILDERS = [_smoke_arc, _museum_arc, _park_arc, _train_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x6A4E37)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    facts = world.facts
    return [
        QAItem(
            question=f"What twist caused the problem?",
            answer=f"The twist was that {facts['twist']}.",
        ),
        QAItem(
            question="What caused the trouble in the story?",
            answer=f"The trouble started because {facts['cause']}.",
        ),
        QAItem(
            question=f"How did {h} fix the problem?",
            answer=f"{facts['resolution']}.",
        ),
        QAItem(
            question="How did the story end after reconciliation?",
            answer=f"{facts['reconciliation']}. In the end, {facts['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    arc_q = {
        "smoke": QAItem("Why can bacon smoke be a problem?", "Bacon smoke can set off alarms or make a room smell strong if the pan gets too hot."),
        "museum": QAItem("Why should people be careful around glass cases?", "Glass cases can hold fragile objects that may fall or break if the latch opens."),
        "park": QAItem("Why should food be covered outside?", "Covered food is safer from animals, wind, and dirt."),
        "train": QAItem("Why can a train shake a wrapper loose?", "Train movement can jostle loose paper or bags and make them slip."),
    }[world.facts["arc"]]
    return [
        QAItem(
            question="What is a superhero story?",
            answer="A superhero story often follows a brave character who solves a problem and helps others.",
        ),
        arc_q,
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people make up after a disagreement and try to be kind again.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly superhero story about bacon, a twist, and reconciliation.",
        f"Write a short heroic story set at {world.place} where the bacon causes trouble and the heroes make up.",
        "Tell a simple story with dialogue where someone must remove a problem, then reconcile with a friend.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.friend, world.bacon]:
        lines.append(f"  {ent.id:6} {ent.kind:9} label={ent.label!r} owner={ent.owner!r} meters={ent.meters} memes={ent.memes}")
    lines.append(f"  place={world.place}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show twist/1.\n#show reconcile/1.\n#show bacon_safe/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("3 compatible logical atoms: twist(hero), reconcile(hero), bacon_safe(hero)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(hero_name="Nova", friend_name="Jules", place="the rooftop garden"),
            StoryParams(hero_name="Mira", friend_name="Tess", place="the city market"),
            StoryParams(hero_name="Blaze", friend_name="Nico", place="the ferry dock"),
            StoryParams(hero_name="Sunny", friend_name="Lina", place="the moonlit park"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.hero_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
