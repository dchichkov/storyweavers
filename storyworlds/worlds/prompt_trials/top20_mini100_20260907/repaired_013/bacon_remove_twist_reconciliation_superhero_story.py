#!/usr/bin/env python3
"""
A tiny superhero story world about bacon, a remove gadget, a sudden twist,
and reconciliation after a small misunderstanding.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass
class StoryParams:
    city: str = "Sunrise City"
    hero: str = "Nova"
    sidekick: str = "Pip"
    rival: str = "Blink"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    city: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.name] = ent
        return ent

    def get(self, name: str) -> Entity:
        return self.entities[name]


CITY_REGISTRY = {
    "Sunrise City": {"mood": "bright", "feature": "rooftops"},
    "Rivergate": {"mood": "busy", "feature": "bridges"},
    "Pine Harbor": {"mood": "windy", "feature": "piers"},
}


@dataclass(frozen=True)
class StoryArc:
    title: str
    premise: str
    problem: str
    twist: str
    reconciliation: str
    ending: str
    problem_answer: str
    twist_answer: str
    reconciliation_answer: str


STORY_ARCS = [
    StoryArc(
        title="The Bacon Bandit Mix-Up",
        premise="Nova and Pip were patrolling the market square when a sizzling bacon cart rolled by and made everyone stop to stare.",
        problem="Blink snatched the bacon bundle, and the crowd thought the rival hero had turned greedy.",
        twist="Then the remove gadget popped open the bundle and showed a tiny smoke alarm hidden inside, set to go off near a broken stove.",
        reconciliation="Nova listened, Blink explained the warning, and Pip shared the bacon with the frightened vendors while the stove was fixed.",
        ending="By sunset, the market smelled of breakfast again, and the three heroes laughed beside the repaired cart.",
        problem_answer="Blink took the bacon bundle, and the crowd mistook that action for greed.",
        twist_answer="The remove gadget revealed that the bacon bundle hid a smoke alarm for warning people about a broken stove.",
        reconciliation_answer="Nova and Pip listened, Blink explained, and they shared the bacon while helping fix the stove.",
    ),
    StoryArc(
        title="The Rooftop Twist",
        premise="A masked flyer dropped bacon strips onto the rooftops so birds would follow her and lead children to safety during a drill.",
        problem="Nova thought the flyer was stealing food and blocked the path with a cape and a stern look.",
        twist="The remove gadget peeled away a false sign on the flyer’s pack, revealing a rescue map and a note from the city school.",
        reconciliation="Nova apologized, the flyer forgave the mistake, and Pip helped deliver the bacon to the shelter where the children waited.",
        ending="Soon the rooftops felt less tense, and the rescue team and the heroes shared a calm meal on the fire escape.",
        problem_answer="Nova blocked the flyer because Nova thought the bacon was being stolen.",
        twist_answer="The remove gadget removed a false sign and exposed a rescue map and school note.",
        reconciliation_answer="Nova apologized, the flyer forgave them, and the bacon was delivered to the shelter.",
    ),
    StoryArc(
        title="Bacon at the Bridge",
        premise="At Rivergate, the heroes found a bacon crate hanging from a bridge cable above the river.",
        problem="Blink guarded the crate so no one would slip while crossing, but the bridge walkers accused the rival of hoarding food.",
        twist="When Pip used the remove gadget, the crate door opened to reveal that the bacon was braced around a cracked cable to stop it from snapping.",
        reconciliation="Nova thanked Blink for the careful plan, and the walkers helped move the crate to the repair crew without any more arguing.",
        ending="The bridge stayed strong, the river kept flowing, and the bacon finally fed the tired repair crew.",
        problem_answer="Blink was guarding the bacon crate, and the bridge walkers misunderstood that care as hoarding.",
        twist_answer="The remove gadget opened the crate and revealed that the bacon was supporting a cracked bridge cable.",
        reconciliation_answer="Nova thanked Blink, and everyone helped the repair crew instead of arguing.",
    ),
    StoryArc(
        title="The Stadium Surprise",
        premise="During the city games, Nova carried a bacon tray to the grandstand for the victory feast.",
        problem="A sudden twist in the parade route sent the tray sliding toward Blink, who grabbed it to keep it from falling.",
        twist="The remove gadget cut away the sticky ribbon under the tray and showed that the bacon had been tied there as a thank-you gift from the coach.",
        reconciliation="Nova stopped blaming Blink, Blink smiled, and the two heroes passed the bacon around the whole team.",
        ending="The crowd cheered louder for the sharing than for the medals, and the stadium shone like a happy lantern.",
        problem_answer="Blink grabbed the bacon tray to keep it from falling, which made Nova think something was wrong.",
        twist_answer="The remove gadget exposed a sticky ribbon and a coach's thank-you note under the tray.",
        reconciliation_answer="Nova stopped blaming Blink, and the bacon was shared with the whole team.",
    ),
    StoryArc(
        title="The Alley of Smoke",
        premise="In a narrow alley, the smell of bacon drifted from a closed lunch box that Nova found beside a glowing sign.",
        problem="Blink reached for the box first, and Nova believed the rival had taken a prize meant for the neighborhood kids.",
        twist="The remove gadget clicked the latch and revealed tiny sandwiches, bacon pieces, and a list of names for the soup kitchen line.",
        reconciliation="Nova handed the box back, Blink offered an apology, and the two heroes delivered lunch together before the line grew long.",
        ending="When the last child ate, the alley felt warm and safe, and even the glowing sign seemed to smile.",
        problem_answer="Blink reached for the lunch box first, so Nova thought the prize was being taken away.",
        twist_answer="The remove gadget opened the box and revealed lunch for the soup kitchen line.",
        reconciliation_answer="Nova returned the box, Blink apologized, and they delivered lunch together.",
    ),
    StoryArc(
        title="The Helmet Twist",
        premise="Pip discovered a bacon strip stuck to a helmet on the museum steps.",
        problem="Nova assumed someone had dropped lunch during a heist and rushed to stop Blink from leaving the scene.",
        twist="The remove gadget peeled the bacon strip free and uncovered a tiny museum key taped underneath it.",
        reconciliation="Blink admitted the key belonged to the exhibit, Nova lowered the guard, and the trio used the key to open the display before it closed for the night.",
        ending="The museum lights dimmed on time, the exhibit was safe, and everyone left as friends.",
        problem_answer="Nova thought the helmet and bacon meant a heist was happening.",
        twist_answer="The remove gadget removed the bacon strip and revealed a museum key taped underneath.",
        reconciliation_answer="Blink explained, Nova lowered the guard, and they opened the exhibit together.",
    ),
]


OPENINGS = [
    "On a sunny morning in {city}, {hero} and {sidekick} flew between rooftops, looking for trouble and small chances to help.",
    "In {city}, every siren and smile meant a job for {hero}, {sidekick}, and sometimes the tricky rival, {rival}.",
    "At the edge of {city}, {hero} kept watch while {sidekick} carried snacks, and {rival} patrolled nearby in a different cape.",
    "The people of {city} knew three names well: {hero}, {sidekick}, and {rival}, whose plans often began with a surprise.",
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.city, params.hero, params.sidekick, params.rival))
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def _fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def _capitalize(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def _story_lines(world: World) -> list[str]:
    f = world.facts
    arc: StoryArc = f["arc"]
    opening = _fill(OPENINGS[f["prose_variant"]], f)
    lines = [
        f"{opening} This was the day of \"{arc.title}.\"",
        arc.premise,
        f"\"Wait,\" said {f['sidekick']}. \"Why is there bacon here?\"",
        arc.problem,
        f"\"Let me remove the cover,\" said {f['hero']}, holding up the remove gadget.",
        arc.twist,
        f"\"I was trying to help,\" said {f['rival']}. \"I only needed everyone to look closer.\"",
        f"{_capitalize(arc.reconciliation)}",
        f"At last, {arc.ending}",
        f"{f['hero']}, {f['sidekick']}, and {f['rival']} shared a small grin and a plate of bacon before flying home.",
    ]
    return lines


ASP_RULES = r"""
city(sunrise_city).
city(rivergate).
city(pine_harbor).

feature(twist).
feature(reconciliation).

can_tell_story(C) :- city(C), feature(twist), feature(reconciliation).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for city in CITY_REGISTRY:
        key = city.lower().replace(" ", "_")
        lines.append(asp.fact("city", key))
    lines.append(asp.fact("feature", "twist"))
    lines.append(asp.fact("feature", "reconciliation"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero story world with bacon, a remove gadget, twist, and reconciliation.")
    ap.add_argument("--city", choices=list(CITY_REGISTRY))
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--rival")
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
    city = args.city or rng.choice(list(CITY_REGISTRY))
    hero = args.hero or rng.choice(["Nova", "Spark", "Jet", "Comet"])
    sidekick = args.sidekick or rng.choice(["Pip", "Moss", "Lark", "Bean"])
    rival = args.rival or rng.choice(["Blink", "Vega", "Rook", "Flare"])
    if len({hero, sidekick, rival}) < 3:
        raise StoryError("Hero, sidekick, and rival must be different characters.")
    return StoryParams(city=city, hero=hero, sidekick=sidekick, rival=rival)


def generate(params: StoryParams) -> StorySample:
    seed = _stable_seed(params)
    arc = STORY_ARCS[seed % len(STORY_ARCS)]
    world = World(city=params.city)
    hero = world.add(Entity(name=params.hero, kind="hero", meters={"hope": 1.0}, memes={"calm": 1.0}))
    sidekick = world.add(Entity(name=params.sidekick, kind="sidekick", meters={"energy": 1.0}, memes={"trust": 1.0}))
    rival = world.add(Entity(name=params.rival, kind="rival", meters={"speed": 1.0}, memes={"pride": 0.6, "care": 0.4}))
    world.add(Entity(name="remove gadget", kind="tool", meters={"power": 1.0}, memes={"reveal": 1.0}))
    world.add(Entity(name="bacon", kind="food", meters={"warmth": 0.8}, memes={"comfort": 0.9}))
    world.facts.update(
        hero=hero.name,
        sidekick=sidekick.name,
        rival=rival.name,
        city=params.city,
        arc=arc,
        prose_variant=(seed // len(STORY_ARCS)) % len(OPENINGS),
        problem=arc.problem,
        twist=arc.twist,
        reconciliation=arc.reconciliation,
        ending=arc.ending,
    )
    story = "\n\n".join(_story_lines(world))
    prompts = [
        f"Write a superhero story about {params.hero}, {params.sidekick}, and {params.rival} in {params.city}.",
        "Include bacon, a remove gadget, a twist, and reconciliation.",
        "Make the story child-facing, concrete, and eventful.",
    ]
    story_qa = [
        QAItem(question=f"What made the heroes misunderstand the situation in \"{arc.title}\"?", answer=arc.problem_answer),
        QAItem(question="What twist did the remove gadget reveal?", answer=arc.twist_answer),
        QAItem(question="How did the characters reconcile?", answer=arc.reconciliation_answer),
        QAItem(question="What ending image proves the problem was solved?", answer=f"The story ends with {arc.ending}"),
    ]
    world_qa = [
        QAItem(question="What is bacon?", answer="Bacon is a kind of cooked meat that is often crispy and salty."),
        QAItem(question="What does remove mean?", answer="Remove means to take something away or lift something off."),
        QAItem(question="What is a twist?", answer="A twist is a surprising change in what seems to be happening."),
        QAItem(question="What is reconciliation?", answer="Reconciliation is when people make peace after a disagreement."),
        QAItem(question="What is a superhero story?", answer="A superhero story is a tale about heroes who use special skills or tools to help people."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(f"{e.name}: kind={e.kind}, meters={dict(e.meters)}, memes={dict(e.memes)}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def _valid_python() -> list[str]:
    return sorted(city.lower().replace(" ", "_") for city in CITY_REGISTRY)


def _asp_valid() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show can_tell_story/1."))
    return sorted(set(asp.atoms(model, "can_tell_story")))


def asp_verify() -> int:
    py = {(c,) for c in _valid_python()}
    cl = set(_asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} cities).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_tell_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in _asp_valid():
            print(item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for city in CITY_REGISTRY:
            params = StoryParams(city=city, hero="Nova", sidekick="Pip", rival="Blink")
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
