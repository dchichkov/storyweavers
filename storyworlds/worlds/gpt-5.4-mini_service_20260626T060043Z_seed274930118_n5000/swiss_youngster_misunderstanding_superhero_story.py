#!/usr/bin/env python3
"""
storyworlds/worlds/swiss_youngster_misunderstanding_superhero_story.py
======================================================================

A compact storyworld about a Swiss youngster who misunderstands a superhero,
then learns the truth and helps save the day.

The seed premise is a child-sized superhero story:
- a Swiss youngster notices a caped hero,
- misreads a brave-looking scene,
- acts on the misunderstanding,
- then discovers the real problem and joins the fix.

The world is intentionally small and constraint-checked: the misunderstanding
must be plausible, the tension must come from what the child sees, and the
ending must prove that the child and hero changed the situation together.
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
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "youngster"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    place: str = "the station square"
    setting_detail: str = "the bells were ringing softly"


@dataclass
class Cast:
    hero_name: str
    youngster_name: str
    sidekick_name: str
    villain_name: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    youngster_name: str
    sidekick_name: str
    villain_name: str
    misunderstanding: str
    seed: Optional[int] = None


SETTING_REGISTRY = {
    "station_square": Scene(place="the station square", setting_detail="the bells were ringing softly"),
    "lake_path": Scene(place="the lake path", setting_detail="the water glittered under a pale sky"),
    "town_market": Scene(place="the town market", setting_detail="fruit stalls smelled sweet and bright"),
    "hill_bridge": Scene(place="the hill bridge", setting_detail="the wind tugged at every coat"),
}

HEROES = [
    ("Captain Alpine", "caped hero", "brave"),
    ("Silver Comet", "masked hero", "swift"),
    ("Blue Beacon", "hero in blue", "kind"),
]

YOUNGSTERS = [
    "Milo", "Lina", "Noah", "Leni", "Mira", "Jonas", "Tara", "Emil"
]

SIDEKICKS = [
    "Pip", "Sami", "Nora", "Rafi"
]

VILLAINS = [
    "Mr. Muffle", "Captain Fog", "The Clock Crow", "The Shadow Puff"
]

MISUNDERSTANDINGS = {
    "blocked_view": "thought the superhero was stopping the youngster on purpose",
    "snatched_bundle": "thought the superhero had stolen the parcel",
    "loud_order": "thought the superhero was shouting at someone in trouble",
    "rope_scene": "thought the superhero was tying up a good person",
}

WORLD_KNOWLEDGE = {
    "swiss": [
        QAItem(
            question="What does it mean if someone is Swiss?",
            answer="Swiss means they come from Switzerland, a country in Europe with mountains, lakes, and many towns."
        ),
        QAItem(
            question="What is Switzerland famous for?",
            answer="Switzerland is famous for mountains, watches, chocolate, cheese, and tidy trains that run on time."
        ),
    ],
    "youngster": [
        QAItem(
            question="What is a youngster?",
            answer="A youngster is a young child."
        ),
    ],
    "superhero": [
        QAItem(
            question="What does a superhero usually do?",
            answer="A superhero usually helps people, solves problems, and protects others when something goes wrong."
        ),
        QAItem(
            question="Why might a superhero wear a cape or mask?",
            answer="A cape or mask can make the hero feel dramatic, hide their face, or help people recognize them as a hero."
        ),
    ],
    "misunderstanding": [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone sees or hears something the wrong way and thinks the wrong thing is happening."
        ),
    ],
}


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


def setup_world(params: StoryParams) -> World:
    scene = SETTING_REGISTRY[params.place]
    world = World(scene)
    hero_title, hero_kind, hero_trait = random.choice(HEROES)

    hero = world.add(Entity(
        id=params.hero_name, kind="character", type="hero",
        label=hero_title, role=hero_trait, memes={"trust": 0.0, "calm": 1.0}
    ))
    youngster = world.add(Entity(
        id=params.youngster_name, kind="character", type="youngster",
        label="youngster", role="curious", memes={"worry": 0.0, "trust": 0.0}
    ))
    sidekick = world.add(Entity(
        id=params.sidekick_name, kind="character", type="sidekick",
        label="sidekick", role="helpful"
    ))
    villain = world.add(Entity(
        id=params.villain_name, kind="character", type="villain",
        label="villain", role="tricky", meters={"trouble": 1.0}
    ))

    world.facts.update(
        hero=hero, youngster=youngster, sidekick=sidekick, villain=villain,
        misunderstanding=params.misunderstanding, hero_kind=hero_kind,
        hero_trait=hero_trait, hero_title=hero_title,
    )
    return world


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTING_REGISTRY:
        raise StoryError("Invalid place for this storyworld.")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("Invalid misunderstanding type.")
    if not params.hero_name or not params.youngster_name:
        raise StoryError("Both the superhero and youngster need names.")
    if params.hero_name == params.youngster_name:
        raise StoryError("The hero and youngster must be different characters.")


def scene_opening(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    youngster: Entity = world.facts["youngster"]  # type: ignore[assignment]
    sidekick: Entity = world.facts["sidekick"]  # type: ignore[assignment]
    world.say(
        f"{youngster.id} was a Swiss youngster who loved walking through {world.scene.place} "
        f"when the day felt bright."
    )
    world.say(
        f"Near {world.scene.place}, {hero.label} was there too, and {sidekick.id} stayed close "
        f"with a careful look."
    )
    world.say(f"{world.scene.setting_detail.capitalize()}.")


def misunderstanding_turn(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    youngster: Entity = world.facts["youngster"]  # type: ignore[assignment]
    sidekick: Entity = world.facts["sidekick"]  # type: ignore[assignment]
    villain: Entity = world.facts["villain"]  # type: ignore[assignment]
    miss = MISUNDERSTANDINGS[world.facts["misunderstanding"]]  # type: ignore[index]

    if world.facts["misunderstanding"] == "blocked_view":
        world.say(
            f"When {hero.label} stepped in front of {youngster.id}, {youngster.id} {miss}."
        )
        world.say(
            f"{youngster.id} could not see that {hero.label} was only blocking {villain.id} from a dropped bag of wires."
        )
    elif world.facts["misunderstanding"] == "snatched_bundle":
        world.say(
            f"{youngster.id} saw {hero.label} lift a parcel from the bench and {miss}."
        )
        world.say(
            f"In truth, {hero.label} had spotted {villain.id} hiding a ticking box beneath the parcel."
        )
    elif world.facts["misunderstanding"] == "loud_order":
        world.say(
            f"{youngster.id} heard {hero.label} call out in a strong voice and {miss}."
        )
        world.say(
            f"The loud words were really for {sidekick.id}, who needed to duck under a falling sign."
        )
    else:
        world.say(
            f"{youngster.id} saw ropes in {hero.label}'s hands and {miss}."
        )
        world.say(
            f"But the ropes were for tying up {villain.id}'s runaway balloon cart before it rolled into the street."
        )

    youngster.memes["worry"] += 1.0
    youngster.memes["trust"] -= 0.5
    world.say(f"{youngster.id} felt small and worried, because the scene looked wrong from where {youngster.id} stood.")


def conflict_and_reveal(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    youngster: Entity = world.facts["youngster"]  # type: ignore[assignment]
    sidekick: Entity = world.facts["sidekick"]  # type: ignore[assignment]
    villain: Entity = world.facts["villain"]  # type: ignore[assignment]
    miss = world.facts["misunderstanding"]  # type: ignore[assignment]

    world.para()
    world.say(
        f"{youngster.id} rushed closer and asked, “Why are you doing that?” "
        f"{hero.label} blinked, then knelt so the youngster could hear the full story."
    )
    world.say(
        f"{sidekick.id} pointed to {villain.id}, and the real problem became clear: "
        f"{villain.id} was the one causing the trouble."
    )

    if miss == "blocked_view":
        world.say(f"{hero.label} had only been shielding people from a dangerous tangle of wires.")
    elif miss == "snatched_bundle":
        world.say(f"{hero.label} had only been saving the parcel before {villain.id} could steal it.")
    elif miss == "loud_order":
        world.say(f"{hero.label} had only shouted to warn {sidekick.id} about the falling sign.")
    else:
        world.say(f"{hero.label} had only been tying the runaway cart before it hit the market tables.")

    youngster.memes["trust"] += 1.0
    youngster.memes["worry"] = 0.0
    hero.memes["trust"] += 1.0


def resolution(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    youngster: Entity = world.facts["youngster"]  # type: ignore[assignment]
    sidekick: Entity = world.facts["sidekick"]  # type: ignore[assignment]
    villain: Entity = world.facts["villain"]  # type: ignore[assignment]

    world.para()
    world.say(
        f"Then {youngster.id} helped at once: {youngster.id} carried the loose parcel, "
        f"{sidekick.id} cleared the path, and {hero.label} stopped {villain.id} for good."
    )
    world.say(
        f"After that, {youngster.id} smiled at {hero.label} and said sorry for the misunderstanding."
    )
    world.say(
        f"By the end, the Swiss youngster was standing beside the superhero, and the whole square felt safe again."
    )


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = setup_world(params)
    scene_opening(world)
    misunderstanding_turn(world)
    conflict_and_reveal(world)
    resolution(world)
    return world


def prompts_for(world: World) -> list[str]:
    f = world.facts
    youngster: Entity = f["youngster"]  # type: ignore[assignment]
    hero: Entity = f["hero"]  # type: ignore[assignment]
    return [
        f'Write a short superhero story for a Swiss youngster named {youngster.id} who misunderstands {hero.label}.',
        f"Tell a gentle story where {youngster.id} sees something strange in {world.scene.place} and later learns the superhero was helping.",
        f'Write a child-friendly story that uses the word "misunderstanding" and ends with the youngster helping the superhero.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    youngster: Entity = f["youngster"]  # type: ignore[assignment]
    hero: Entity = f["hero"]  # type: ignore[assignment]
    sidekick: Entity = f["sidekick"]  # type: ignore[assignment]
    villain: Entity = f["villain"]  # type: ignore[assignment]
    miss = f["misunderstanding"]

    qa = [
        QAItem(
            question=f"Who is the Swiss youngster in the story?",
            answer=f"The Swiss youngster is {youngster.id}."
        ),
        QAItem(
            question=f"What superhero did {youngster.id} misunderstand?",
            answer=f"{youngster.id} misunderstood {hero.label}."
        ),
        QAItem(
            question="Why did the youngster feel worried at first?",
            answer=f"Because {youngster.id} saw {hero.label} doing something that looked wrong, but it was actually a misunderstanding."
        ),
        QAItem(
            question="Who showed the youngster the truth?",
            answer=f"{sidekick.id} helped point out that {villain.id} was the real problem."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{youngster.id} understood the hero, helped fix the trouble, and ended the story standing safely beside {hero.label}."
        ),
    ]
    if miss == "snatched_bundle":
        qa.append(QAItem(
            question="What was the youngster afraid the superhero had done?",
            answer=f"{youngster.id} thought {hero.label} had stolen a parcel."
        ))
    elif miss == "blocked_view":
        qa.append(QAItem(
            question="What did the youngster think the superhero was doing?",
            answer=f"{youngster.id} thought {hero.label} was blocking the youngster on purpose."
        ))
    elif miss == "loud_order":
        qa.append(QAItem(
            question="What did the youngster think the superhero was doing with the loud voice?",
            answer=f"{youngster.id} thought {hero.label} was shouting at someone in trouble."
        ))
    else:
        qa.append(QAItem(
            question="What did the youngster think the ropes meant?",
            answer=f"{youngster.id} thought the ropes meant {hero.label} was tying up a good person."
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    tags = {"swiss", "youngster", "superhero", "misunderstanding"}
    out: list[QAItem] = []
    for tag in ("swiss", "youngster", "superhero", "misunderstanding"):
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


ASP_RULES = r"""
% A misunderstanding exists if the youngster sees a hero action but not the true cause.
misunderstanding(S) :- sees(S, A), not knows_cause(S), child(S).

% The story is valid when the youngster, a superhero, and a villain are present,
% and the hero action is plausible for helping.
valid_story(P, M) :- place(P), misunderstanding_type(M), hero_action(M, A),
                     child_name(C), hero_name(H), villain_name(V),
                     child(C), hero(H), villain(V), see_scene(P, M, A).

% There is a clear ending when the child helps and the villain is stopped.
complete_story(P, M) :- valid_story(P, M), child_helps(M), villain_stopped(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTING_REGISTRY:
        lines.append(asp.fact("place", pid))
    for m in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding_type", m))
        lines.append(asp.fact("hero_action", m, "helping"))
        lines.append(asp.fact("see_scene", "station_square", m, "helping"))
        lines.append(asp.fact("child_helps", m))
        lines.append(asp.fact("villain_stopped", m))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("villain", "villain"))
    lines.append(asp.fact("child_name", "youngster"))
    lines.append(asp.fact("hero_name", "superhero"))
    lines.append(asp.fact("villain_name", "villain"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_pairs = sorted(set(asp.atoms(model, "valid_story")))
    py_pairs = sorted((p, m) for p in SETTING_REGISTRY for m in MISUNDERSTANDINGS)
    if asp_pairs == py_pairs:
        print(f"OK: clingo gate matches Python registry ({len(asp_pairs)} stories).")
        return 0
    print("MISMATCH between clingo and Python story gate:")
    if set(asp_pairs) - set(py_pairs):
        print("  only in clingo:", sorted(set(asp_pairs) - set(py_pairs)))
    if set(py_pairs) - set(asp_pairs):
        print("  only in python:", sorted(set(py_pairs) - set(asp_pairs)))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A Swiss youngster misunderstands a superhero, then learns the truth.")
    ap.add_argument("--place", choices=SETTING_REGISTRY)
    ap.add_argument("--hero-name")
    ap.add_argument("--youngster-name")
    ap.add_argument("--sidekick-name")
    ap.add_argument("--villain-name")
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
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
    place = args.place or rng.choice(list(SETTING_REGISTRY))
    misunderstanding = args.misunderstanding or rng.choice(list(MISUNDERSTANDINGS))
    hero_name = args.hero_name or rng.choice([h[0] for h in HEROES])
    youngster_name = args.youngster_name or rng.choice(YOUNGSTERS)
    sidekick_name = args.sidekick_name or rng.choice(SIDEKICKS)
    villain_name = args.villain_name or rng.choice(VILLAINS)
    if len({hero_name, youngster_name, sidekick_name, villain_name}) < 4:
        raise StoryError("All characters in the story should have different names.")
    return StoryParams(
        place=place,
        hero_name=hero_name,
        youngster_name=youngster_name,
        sidekick_name=sidekick_name,
        villain_name=villain_name,
        misunderstanding=misunderstanding,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts_for(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="station_square",
        hero_name="Captain Alpine",
        youngster_name="Milo",
        sidekick_name="Pip",
        villain_name="Mr. Muffle",
        misunderstanding="snatched_bundle",
    ),
    StoryParams(
        place="lake_path",
        hero_name="Silver Comet",
        youngster_name="Lina",
        sidekick_name="Nora",
        villain_name="Captain Fog",
        misunderstanding="blocked_view",
    ),
    StoryParams(
        place="town_market",
        hero_name="Blue Beacon",
        youngster_name="Tara",
        sidekick_name="Rafi",
        villain_name="The Clock Crow",
        misunderstanding="loud_order",
    ),
    StoryParams(
        place="hill_bridge",
        hero_name="Captain Alpine",
        youngster_name="Jonas",
        sidekick_name="Sami",
        villain_name="The Shadow Puff",
        misunderstanding="rope_scene",
    ),
]


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for place, miss in stories:
            print(f"  {place} / {miss}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.youngster_name} / {p.hero_name} / {p.misunderstanding}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
