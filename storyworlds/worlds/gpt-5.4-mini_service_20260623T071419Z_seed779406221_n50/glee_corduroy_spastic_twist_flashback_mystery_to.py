#!/usr/bin/env python3
"""
storyworlds/worlds/glee_corduroy_spastic_twist_flashback_mystery_to.py
======================================================================

A compact superhero-style storyworld about a kid hero, a strange corduroy clue,
a spastic little distraction, a twist, a flashback, and a mystery to solve.

The domain is intentionally tiny: one child-side hero, one helper, one problem
object, one clue, and one hidden truth. The world model tracks physical meters
and emotional memes so the story is driven by simulated state rather than a
fixed paragraph template.

Story seed image:
- A bright young hero feels glee when a corduroy scrap points to a mystery.
- A spastic-looking glitchy clue causes trouble.
- A flashback reveals an earlier missed detail.
- The final twist solves the mystery and proves what changed.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Scene:
    place: str
    backdrop: str
    affordance: str


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    twist_line: str
    flashback_line: str
    solves_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    phrase: str
    motion: str
    spastic_line: str
    impact: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    phrase: str
    method: str
    finish: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World(self.scene)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


SCENES = {
    "rooftop": Scene(place="the rooftop", backdrop="the city lights glittered below", affordance="scan"),
    "alley": Scene(place="the alley", backdrop="the brick walls echoed softly", affordance="search"),
    "museum": Scene(place="the museum hall", backdrop="the glass cases shone under tall lamps", affordance="inspect"),
}

HEROES = {
    "glee": {"name": "Glee", "type": "girl", "label": "Captain Glee"},
    "bolt": {"name": "Bolt", "type": "boy", "label": "Bolt"},
    "nova": {"name": "Nova", "type": "girl", "label": "Nova"},
}

CLUES = {
    "corduroy_patch": Clue(
        id="corduroy_patch",
        label="corduroy patch",
        phrase="a soft corduroy patch with a tiny silver thread",
        twist_line="the corduroy patch was not just cloth; it matched a torn sleeve from the hero's own coat",
        flashback_line="there had been an earlier glimpse of that same ridged fabric near the scene",
        solves_line="the patch pointed straight to the missing helper",
        tags={"corduroy", "mystery"},
    ),
    "corduroy_ribbon": Clue(
        id="corduroy_ribbon",
        label="corduroy ribbon",
        phrase="a narrow corduroy ribbon tied in a neat knot",
        twist_line="the ribbon was actually a disguise for a hidden tag",
        flashback_line="a flashback showed the ribbon fluttering by the doorway before the trouble began",
        solves_line="the ribbon revealed the hiding place at once",
        tags={"corduroy", "mystery"},
    ),
}

TROUBLES = {
    "spastic_signal": Trouble(
        id="spastic_signal",
        label="spastic signal",
        phrase="a spastic little signal that kept flickering and twitching",
        motion="twitch and wobble",
        spastic_line="the signal jerked around so fast it looked like it could not sit still",
        impact="the wrong signal made the crowd point at the wrong door",
        tags={"spastic", "mystery"},
    ),
    "spastic_doodle": Trouble(
        id="spastic_doodle",
        label="spastic doodle",
        phrase="a spastic doodle drawn in hurried loops",
        motion="jitter and jump",
        spastic_line="the doodle bounced across the page in nervous little hops",
        impact="the doodle hid the real clue under a messy scribble",
        tags={"spastic", "mystery"},
    ),
}

SOLUTIONS = {
    "twist_key": Solution(
        id="twist_key",
        label="twist key",
        phrase="a tiny twist key",
        method="twisted the key just once",
        finish="the lock clicked open with a happy snap",
        tags={"Twist", "mystery"},
    ),
    "twist_glove": Solution(
        id="twist_glove",
        label="twist glove",
        phrase="a twist glove with a bright thumb button",
        method="gave the glove a careful twist",
        finish="the signal settled into a steady beam",
        tags={"Twist", "mystery"},
    ),
}


@dataclass
class StoryParams:
    scene: str
    hero: str
    clue: str
    trouble: str
    solution: str
    sidekick: str = "rookie"
    seed: Optional[int] = None


CURATED = [
    StoryParams(scene="rooftop", hero="glee", clue="corduroy_patch", trouble="spastic_signal", solution="twist_key", sidekick="rookie"),
    StoryParams(scene="museum", hero="nova", clue="corduroy_ribbon", trouble="spastic_doodle", solution="twist_glove", sidekick="helper"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for scene in SCENES:
        for hero in HEROES:
            for clue in CLUES:
                for trouble in TROUBLES:
                    if "corduroy" in clue and "spastic" in trouble:
                        combos.append((scene, hero, clue, trouble))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero-style mystery storyworld with a twist and flashback.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--sidekick")
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
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.hero is None or c[1] == args.hero)
              and (args.clue is None or c[2] == args.clue)
              and (args.trouble is None or c[3] == args.trouble)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, hero, clue, trouble = rng.choice(sorted(combos))
    solution = args.solution or rng.choice(sorted(SOLUTIONS))
    sidekick = args.sidekick or rng.choice(["rookie", "helper", "partner"])
    return StoryParams(scene=scene, hero=hero, clue=clue, trouble=trouble, solution=solution, sidekick=sidekick)


def _validate_combo(params: StoryParams) -> None:
    if (params.scene, params.hero, params.clue, params.trouble) not in valid_combos():
        raise StoryError("Invalid story combination for this mystery world.")


def tell(params: StoryParams) -> World:
    _validate_combo(params)
    scene = SCENES[params.scene]
    hero_cfg = HEROES[params.hero]
    clue = CLUES[params.clue]
    trouble = TROUBLES[params.trouble]
    solution = SOLUTIONS[params.solution]

    world = World(scene)
    hero = world.add(Entity(id=hero_cfg["name"], kind="character", type=hero_cfg["type"], label=hero_cfg["label"], role="hero"))
    sidekick = world.add(Entity(id=params.sidekick.title(), kind="character", type="child", label=params.sidekick.title(), role="sidekick"))
    clue_ent = world.add(Entity(id=clue.id, type="clue", label=clue.label, attrs={"phrase": clue.phrase}, tags=set(clue.tags)))
    trouble_ent = world.add(Entity(id=trouble.id, type="trouble", label=trouble.label, attrs={"phrase": trouble.phrase}, tags=set(trouble.tags)))
    solution_ent = world.add(Entity(id=solution.id, type="solution", label=solution.label, attrs={"phrase": solution.phrase}, tags=set(solution.tags)))

    hero.memes["glee"] = 1.0
    hero.memes["curiosity"] = 1.0
    sidekick.memes["worry"] = 0.0
    trouble_ent.meters["confusion"] = 1.0
    clue_ent.meters["importance"] = 1.0
    solution_ent.meters["readiness"] = 1.0

    world.say(f"{hero.label_word} shot onto {scene.place} with glee, while {scene.backdrop}.")
    world.say(f"{hero.label_word} and {sidekick.label_word} were a small superhero team, always ready for a mystery to solve.")
    world.say(f"Then they found {clue.phrase}, and the clue seemed to hum with promise.")

    world.para()
    world.say(f"But {trouble.phrase} darted in and spoiled the trail.")
    world.say(f"{trouble.spastic_line.capitalize()} {trouble.impact}, so the team had to slow down and look twice.")

    world.para()
    world.say(f"That was when a flashback flickered through {hero.label_word}'s mind.")
    world.say(f"{clue.flashback_line.capitalize()}.")
    world.say(f"{clue.twist_line.capitalize()}, and that was the twist.")

    world.para()
    world.say(f"{solution.method.capitalize()}, and {solution.finish}.")
    world.say(f"{clue.solves_line.capitalize()}, so the mystery to solve was solved at last.")
    world.say(f"{hero.label_word} smiled with glee again, and {scene.place} felt brighter than before.")

    world.facts.update(hero=hero, sidekick=sidekick, clue=clue, trouble=trouble, solution=solution, scene=scene, outcome="solved")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a young child where {f["hero"].label_word} finds {f["clue"].phrase} and faces a mystery to solve.',
        f"Tell a gentle adventure where {f['hero'].label_word} feels glee, notices a corduroy clue, and uses a twist to solve the problem.",
        f'Write a story with a flashback, a twist, and a clear ending image set on {f["scene"].place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue"]
    trouble = f["trouble"]
    solution = f["solution"]
    scene = f["scene"]
    return [
        QAItem(
            question=f"Who is the story about on {scene.place}?",
            answer=f"It is about {hero.label_word}, a small superhero who felt glee and wanted to solve a mystery.",
        ),
        QAItem(
            question=f"What corduroy clue did {hero.label_word} find?",
            answer=f"{hero.label_word} found {clue.phrase}. It mattered because the corduroy detail pointed toward the hidden truth.",
        ),
        QAItem(
            question=f"What made the search tricky?",
            answer=f"{trouble.phrase} made the trail jump around. The spastic trouble hid the right path for a moment.",
        ),
        QAItem(
            question=f"What was the flashback for?",
            answer=f"The flashback helped {hero.label_word} remember an earlier glimpse of the same clue, and that gave the story its twist.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{solution.method.capitalize()}, and {solution.finish}. That is how the mystery to solve was finished.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a clue?", answer="A clue is a little piece of information that helps someone solve a mystery."),
        QAItem(question="What is a flashback?", answer="A flashback is a quick memory of something that happened earlier."),
        QAItem(question="What is a twist in a story?", answer="A twist is a surprise turn that changes what you expected."),
        QAItem(question="What does glee mean?", answer="Glee means very happy excitement."),
        QAItem(question="What is corduroy?", answer="Corduroy is a cloth with soft ridges that you can feel with your fingers."),
        QAItem(question="What does spastic mean in this story?", answer="Here it means fast, jittery, and hard to follow."),
    ]


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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:12} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for s in SCENES:
        lines.append(asp.fact("scene", s))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
        lines.append(asp.fact("corduroy", c))
    for t in TROUBLES:
        lines.append(asp.fact("trouble", t))
        lines.append(asp.fact("spastic", t))
    for s in SOLUTIONS:
        lines.append(asp.fact("solution", s))
        lines.append(asp.fact("twist", s))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Scene, Hero, Clue, Trouble) :- scene(Scene), hero(Hero), clue(Clue), trouble(Trouble),
                                     corduroy(Clue), spastic(Trouble).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH:")
        print("only python:", sorted(py - asp_set))
        print("only asp:", sorted(asp_set - py))
        return 1
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story:
        print("FAIL: empty story")
        return 1
    print("OK: story generation smoke test passed.")
    return 0


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
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
