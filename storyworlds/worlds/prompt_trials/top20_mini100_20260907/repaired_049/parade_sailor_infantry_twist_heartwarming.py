#!/usr/bin/env python3
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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

STORYWORLDS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
sys.path.insert(0, STORYWORLDS_ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACE = "harbor town"
PEOPLE = ["sailor", "infantry", "parade"]
THEME = "Twist"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = PLACE
    affords: set[str] = field(default_factory=lambda: {"march", "watch", "share", "twist"})


@dataclass(frozen=True)
class TwistScenario:
    id: str
    opening: str
    tension: str
    clue: str
    dialogue: str
    turn: str
    resolution: str
    ending: str
    change: str


SCENARIOS = [
    TwistScenario(
        id="drum_brigade",
        opening="The harbor square was dressed for a parade, with ribbons on the lamps and drums waiting beside the fountain.",
        tension="But the loudest drum was meant for the infantry band, and the sailor who had borrowed it was too shy to ask for help carrying it back.",
        clue="A tide pool beside the pier showed that the drum straps had snapped because the wet rope had twisted tight.",
        dialogue="Could we carry it together and see what the rope is trying to tell us?",
        turn="So the sailor and the infantry captain knelt side by side, untwisted the rope, and shared the weight while the children held the drum steady.",
        resolution="When the parade began, the band marched in step, the sailor smiled, and the once-broken drum sounded warm and brave.",
        ending="By sunset, the ribbons still fluttered, but now the sailor walked at the front of the band with the infantry, laughing softly as the town cheered.",
        change="the parade team now checked every rope together before the music started",
    ),
    TwistScenario(
        id="paper_boat",
        opening="On market day, the parade stopped at the harbor gate so the townsfolk could wave to the returning sailor.",
        tension="The infantry children wanted to march in perfect lines, but their paper hats kept folding in the sea breeze.",
        clue="A little boy pointed to the fountain and saw that the hats stayed stiff when they were tucked under the bright parade banner.",
        dialogue="What if the banner is not just decoration, but a shelter we can share?",
        turn="The sailor held one side of the banner, the infantry leaders held the other, and the children marched beneath it as if under a small safe roof.",
        resolution="Their hats stayed dry, the line stayed neat, and the sailor bowed because the parade looked twice as happy when everyone had a place.",
        ending="At the end, the banner kept fluttering over smiling faces, and the sea breeze seemed less like a trick and more like a friend.",
        change="the parade route now included a shared banner walk for windy days",
    ),
    TwistScenario(
        id="lantern_count",
        opening="Evening came early, and the harbor parade lanterns were lit one by one along the stone road.",
        tension="One lantern was missing, and the infantry guard feared the march would have to end before the sailor reached the square.",
        clue="The sailor noticed a candle glow inside the bakery cart, where the missing lantern had been set down by mistake.",
        dialogue="Shall we bring the light back instead of arguing about who lost it?",
        turn="The sailor and the infantry guard carried the lantern together, and the baker apologized with a tired smile and a fresh loaf.",
        resolution="The parade resumed, the lights made a golden path, and everyone walked more gently because they knew mistakes could be mended.",
        ending="The last lantern shone on bread, ribbons, and boots moving kindly through the town.",
        change="the lanterns were counted aloud by two people instead of one",
    ),
    TwistScenario(
        id="rain_banners",
        opening="A spring shower began just as the parade drums rolled through the harbor arch.",
        tension="The infantry band worried that wet banners would drag in the mud, and the sailor worried the children would be disappointed.",
        clue="The cloth was lighter where it had dried under the awning, showing that one folded banner could cover two smaller ones.",
        dialogue="Could one good fold keep everyone dry enough to keep smiling?",
        turn="The sailor taught the infantry helper a careful fold, and together they made a shared canopy from the largest banner.",
        resolution="The parade went on in the rain, boots splashed, and the children laughed because the new canopy looked like a bright sail on land.",
        ending="When the clouds passed, the folded banner was still dry at the edges and everyone had a story to keep.",
        change="the parade crew now knew how to turn one banner into shelter",
    ),
]


@dataclass
class StoryParams:
    place: str
    theme: str
    hero: str
    ally: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def add_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = meter(e, key) + amt


def add_meme(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = meme(e, key) + amt


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming twist storyworld about a parade, a sailor, and infantry.")
    ap.add_argument("--place", choices=[PLACE])
    ap.add_argument("--theme", choices=[THEME])
    ap.add_argument("--hero")
    ap.add_argument("--ally")
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
    place = args.place or PLACE
    theme = args.theme or THEME
    hero = args.hero or rng.choice(["Mira", "Niko", "Lena", "Toma"])
    ally = args.ally or rng.choice(["sailor", "infantry"])
    return StoryParams(place=place, theme=theme, hero=hero, ally=ally)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != PLACE or params.theme != THEME:
        raise StoryError("This world only supports the harbor-town parade twist.")


def tell(world: World, params: StoryParams) -> World:
    variant = params.seed if params.seed is not None else sum((i + 1) * ord(ch) for i, ch in enumerate(f"{params.place}|{params.theme}|{params.hero}|{params.ally}"))
    scenario = SCENARIOS[variant % len(SCENARIOS)]

    hero = world.add(Entity(id=params.hero, kind="character", type="child", label=params.hero))
    sailor = world.add(Entity(id="sailor", kind="character", type="person", label="sailor"))
    infantry = world.add(Entity(id="infantry", kind="character", type="person", label="infantry"))
    parade = world.add(Entity(id="parade", kind="event", type="parade", label="parade"))
    lantern = world.add(Entity(id="lantern", kind="thing", type="lantern", label="lantern"))

    add_meme(hero, "curiosity", 1.0)
    add_meme(hero, "kindness", 1.0)
    world.say(scenario.opening)
    world.say(f"{hero.id} watched the {parade.label} and noticed that the {params.ally} looked worried.")
    world.say(f"The {sailor.label} said, \"I do not want to spoil the day.\" The {infantry.label} answered, \"Then let us fix it together.\"")
    world.para()
    world.say(scenario.tension)
    world.say(scenario.clue)
    world.say(f"{hero.id} asked, \"{scenario.dialogue}\"")
    world.say(f"The {sailor.label} nodded, and the {infantry.label} stepped closer so nobody had to carry the problem alone.")
    world.para()
    add_meter(hero, "helping", 1.0)
    add_meter(sailor, "shared_weight", 1.0)
    add_meter(infantry, "shared_weight", 1.0)
    add_meme(hero, "trust", 1.0)
    world.say(scenario.turn)
    world.say(scenario.resolution)
    add_meter(lantern, "glow", 1.0)
    world.para()
    add_meme(hero, "joy", 1.0)
    add_meme(sailor, "joy", 1.0)
    add_meme(infantry, "joy", 1.0)
    world.say(f"The next morning, the town remembered the gentle surprise: {scenario.change}.")
    world.say(f"{hero.id} smiled and said, \"I thought the trouble would stop the parade, but it taught us how to care for each other.\"")
    world.say(f"The {sailor.label} laughed, the {infantry.label} waved, and the parade ended with a warm cheer that sounded like home.")
    world.say(scenario.ending)

    world.facts.update(
        hero=hero,
        sailor=sailor,
        infantry=infantry,
        parade=parade,
        scenario=scenario,
        lantern=lantern,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World(Setting())
    world = tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming story about a {f['parade'].label}, a {f['sailor'].label}, and the {f['infantry'].label} with a gentle twist.",
        f"Tell a child-facing tale where {f['hero'].id} solves a parade problem by sharing and listening.",
        f"Include a brief dialogue that changes what the characters decide to do.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    sc = f["scenario"]
    return [
        QAItem(
            question="What was happening in the town at the beginning?",
            answer=f"The town was preparing for a parade, with the sailor and the infantry both part of the celebration.",
        ),
        QAItem(
            question="What problem needed a twist to solve?",
            answer=f"The main trouble was that {sc.tension}",
        ),
        QAItem(
            question="What clue helped the characters understand the problem?",
            answer=f"They noticed that {sc.clue}",
        ),
        QAItem(
            question="What did the child say that changed the plan?",
            answer=f'{f["hero"].id} asked, "{sc.dialogue}"',
        ),
        QAItem(
            question="How did the sailor and infantry respond?",
            answer="They worked together instead of arguing, and they shared the task so the problem became smaller.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The parade ended warmly, and the town kept the lesson that {sc.change}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a parade?", answer="A parade is a cheerful public walk or march, often with music, banners, and people celebrating together."),
        QAItem(question="Who is a sailor?", answer="A sailor is someone who works on boats or ships on the water."),
        QAItem(question="Who is infantry?", answer="Infantry are soldiers who travel and work on foot."),
        QAItem(question="What does a twist mean in a story?", answer="A twist is a surprising turn that changes how the characters understand the situation."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(harbor_town, parade, sailor, infantry, twist).
#show valid/5.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("setting", "harbor_town"),
        asp.fact("seed_word", "parade"),
        asp.fact("seed_word", "sailor"),
        asp.fact("seed_word", "infantry"),
        asp.fact("feature", "twist"),
    ])


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    return [("harbor_town", "parade", "sailor", "infantry", "twist")]


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combo).")
        return 0
    print("MISMATCH")
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(PLACE, THEME, "Mira", "sailor"),
    StoryParams(PLACE, THEME, "Niko", "infantry"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.hero} / {p.ally}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
