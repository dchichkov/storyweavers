#!/usr/bin/env python3
"""
A small superhero story world about a grizzly-sized cleanup quest, where a
hero must terminate a dangerous scour and earn a happy ending.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

from storyworlds.results import QAItem, StoryError, StorySample  # eager import


@dataclass
class StoryParams:
    city: str = "Brightharbor"
    hero: str = "Nova"
    ally: str = "Patch"
    villain: str = "the Grizzle Scour"
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
    "Brightharbor": {"mood": "busy and hopeful", "type": "port city"},
    "Sunspire": {"mood": "bright and windy", "type": "skyline city"},
    "Mossgate": {"mood": "green and close-knit", "type": "river city"},
}

HERO_REGISTRY = {
    "Nova": {"power": "beam light", "tone": "brave"},
    "Vector": {"power": "lift rubble", "tone": "steady"},
    "Comet": {"power": "speed through crowds", "tone": "quick"},
}

ALLY_REGISTRY = {
    "Patch": {"role": "mechanic", "tone": "practical"},
    "Relay": {"role": "messenger", "tone": "sharp"},
    "Mina": {"role": "medic", "tone": "kind"},
}

VILLAIN_REGISTRY = {
    "the Grizzle Scour": {"kind": "beastlike threat", "form": "grizzly shadow"},
    "the Rust Scour": {"kind": "storm threat", "form": "red dust"},
    "the Frost Scour": {"kind": "cold threat", "form": "white fog"},
}


@dataclass(frozen=True)
class Arc:
    title: str
    opening: str
    problem: str
    inner_monologue: str
    quest: str
    turn: str
    resolution: str
    ending_image: str
    problem_answer: str
    turn_answer: str
    resolution_answer: str


ARCS = [
    Arc(
        title="Terminate the Grizzly Scour",
        opening="A grizzly-shaped scour tore through the subway vents and scared every commuter off the platform.",
        problem="Its gray fur was only a shell, but its claws kept scraping sparks from the rails and making the city shake.",
        inner_monologue="{hero} thought, If I rush in, I may scare the crowd more, but if I wait, the scour will spread again.",
        quest="{hero} and {ally} chose a rescue quest: guide the people out, find the scour's weak seam, and terminate it before dusk.",
        turn="At the tunnel mouth, {ally} whispered, 'You do not have to win by force.' {hero} answered, 'Then I will win by care.'",
        resolution="They used a bright signal, a cooling spray, and one careful beam to split the shell apart and end the scour for good.",
        ending_image="the platform lights blinked on above a clean track, and children waved at {hero} from a safe train window",
        problem_answer="A grizzly-shaped scour was shaking the subway and scaring commuters away.",
        turn_answer="The ally reminded the hero to act with care instead of only force, and the hero agreed.",
        resolution_answer="They found the scour's weak seam and terminated it with a careful rescue plan.",
    ),
    Arc(
        title="The Rooftop Quest",
        opening="Smoke curled over the rooftops when a grizzly grime-scour began clogging the rain collectors.",
        problem="Without clean water, the bakery ovens went cold, and the whole block looked tired and gray.",
        inner_monologue="{hero} wondered, Should I chase the scour now, or first help the baker families stay calm?",
        quest="{hero} set out on a quest across the fire escapes with {ally}, carrying brushes, rope, and a scanner that could hear hidden grime.",
        turn="When the scour roared from a chimney, {ally} called, 'Look up, not at its teeth!' That small advice gave {hero} a clearer plan.",
        resolution="They sealed the chimney gap, swept the grime into a safe net, and washed the collectors until rain could shine through them again.",
        ending_image="fresh water glittered in every rooftop tank while the baker waved flour from both hands like white flags",
        problem_answer="A grizzly grime-scour clogged the rain collectors on the rooftops.",
        turn_answer="The ally told the hero to look up instead of at the villain's teeth, which helped the hero focus.",
        resolution_answer="They sealed the gap, trapped the grime safely, and restored the water collectors.",
    ),
    Arc(
        title="Happy Ending at Harbor Square",
        opening="Harbor Square was packed with balloons, until a grizzly shadow-scour slipped between the statues and dimmed every smile.",
        problem="It made the music sound flat, and even the ice cream melted too fast in worried hands.",
        inner_monologue="{hero} told themself, A happy ending cannot be forced, but it can be protected.",
        quest="{hero} and {ally} began a careful quest through the square, following the shadow's chill to the old fountain below.",
        turn="{ally} said, 'The crowd trusts you.' {hero} breathed in and replied, 'Then I will give them something to trust.'",
        resolution="A single shield of light pinned the shadow to the fountain stone, and the city cameras caught the final spark as the scour vanished.",
        ending_image="the fountain danced again while the children laughed under balloons that bobbed like tiny moons",
        problem_answer="A grizzly shadow-scour dimmed the festival in Harbor Square.",
        turn_answer="The ally reminded the hero that the crowd trusted them, and the hero chose to protect that trust.",
        resolution_answer="The hero trapped the shadow with light at the fountain and made the scour vanish.",
    ),
    Arc(
        title="The Terminal Bridge",
        opening="At the old terminal bridge, a grizzly soot-scour crawled along the cables and dropped black dust on every car below.",
        problem="Drivers honked, birds fled, and the bridge began to look like a night that would not end.",
        inner_monologue="{hero} worried, If this bridge falls, the city will lose its fastest path home.",
        quest="So {hero} accepted a bridge-crossing quest with {ally}: remove the soot, protect the cables, and keep every traveler moving.",
        turn="Halfway across, {ally} said, 'The scour hates patience.' {hero} smiled behind the mask and slowed down even more.",
        resolution="That patience let them scrub each cable clean, and the soot-scour lost its grip before it could snap the bridge.",
        ending_image="sunlight slid across the bridge cables like gold thread, and the last taxi rolled home in peace",
        problem_answer="A grizzly soot-scour covered the bridge cables in black dust and threatened the crossing.",
        turn_answer="The ally pointed out that the scour hated patience, so the hero slowed down on purpose.",
        resolution_answer="Their careful scrubbed the cables clean and ended the threat to the bridge.",
    ),
    Arc(
        title="Quest for the Last Clean Alley",
        opening="Behind the comic shop, one last alley stayed clean while a grizzly mud-scour stomped closer from the storm drains.",
        problem="If the mud reached the alley, the neighborhood mural would vanish under a brown wall.",
        inner_monologue="{hero} thought, This alley is small, but small places still deserve a big rescue.",
        quest="The quest was simple and hard at once: carry sandbags, guide the runoff, and terminate the scour before it hit the mural.",
        turn="When the first sandbag slipped, {ally} laughed softly and said, 'Heroes can bend their knees.' That hint saved the plan.",
        resolution="They bent low, stacked the bags properly, and steered the mud away until the mural's bright whale could be seen again.",
        ending_image="the whale mural shone in blue and green paint while rainwater ran harmlessly down the far curb",
        problem_answer="A grizzly mud-scour was about to bury the neighborhood mural in the alley.",
        turn_answer="The ally reminded the hero to bend their knees, helping the hero set the sandbags properly.",
        resolution_answer="They redirected the mud and saved the mural from being covered.",
    ),
]

OPENINGS = [
    "{hero} had the city watch on speed dial, but this time the job needed a real quest.",
    "In the bright streets of {city}, {hero} and {ally} heard the alarm bell and ran toward trouble.",
    "People in {city} already knew the mask of {hero}, but they had never seen a grizzly scour before.",
    "On a clear afternoon, {hero} found out that even a happy city can get shaken by a dark threat.",
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.city, params.hero, params.ally, params.villain))
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def _fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def _build_story_lines(world: World) -> list[str]:
    f = world.facts
    arc: Arc = f["arc"]
    lines = [
        _fill(OPENINGS[f["opening_variant"]], f),
        f"{arc.opening}",
        f"{arc.problem}",
        f"{_fill(arc.inner_monologue, f)}",
        f"That was when {f['ally']} said, \"{f['ally_line']}\"",
        f"{_fill(arc.quest, f)}",
        f"{f['quest_detail']}",
        f"{_fill(arc.turn, f)}",
        f"{arc.resolution}",
        f"{arc.ending_image}.",
    ]
    return lines


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world about terminate, grizzly, and scour.")
    ap.add_argument("--city", choices=list(CITY_REGISTRY))
    ap.add_argument("--hero", choices=list(HERO_REGISTRY))
    ap.add_argument("--ally", choices=list(ALLY_REGISTRY))
    ap.add_argument("--villain", choices=list(VILLAIN_REGISTRY))
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
    hero = args.hero or rng.choice(list(HERO_REGISTRY))
    ally = args.ally or rng.choice(list(ALLY_REGISTRY))
    villain = args.villain or rng.choice(list(VILLAIN_REGISTRY))
    if hero == ally:
        raise StoryError("The hero and ally must be different characters.")
    return StoryParams(city=city, hero=hero, ally=ally, villain=villain)


def generate(params: StoryParams) -> StorySample:
    seed = _stable_seed(params)
    arc = ARCS[seed % len(ARCS)]
    world = World(city=params.city)

    hero_ent = world.add(Entity(name=params.hero, kind="hero", meters={"health": 10.0}, memes={"hope": 8.0}))
    ally_ent = world.add(Entity(name=params.ally, kind="ally", meters={"health": 9.0}, memes={"care": 9.0}))
    villain_ent = world.add(Entity(name=params.villain, kind="scour", meters={"stability": 3.0}, memes={"threat": 9.0}))
    world.add(Entity(name=params.city, kind="city", meters={"cleanliness": 4.0}, memes={"mood": 6.0}))

    ally_line = random.Random(seed + 17).choice(
        [
            "We can outsmart it if we stay calm.",
            "The city needs us gentle and fast.",
            "A clean plan beats a loud punch.",
            "Look for the weak seam, not the biggest roar.",
        ]
    )
    quest_detail = random.Random(seed + 29).choice(
        [
            "Their boots thudded over the rain-slick roof while sirens echoed below.",
            "The mask communicator crackled with updates from the street below.",
            "Every step had to be careful, because the scour left slippery black dust.",
            "They moved from shadow to shadow so the crowd would stay safe.",
        ]
    )

    world.facts.update(
        city=params.city,
        hero=params.hero,
        ally=params.ally,
        villain=params.villain,
        arc=arc,
        opening_variant=seed % len(OPENINGS),
        ally_line=ally_line,
        quest_detail=quest_detail,
        villain_form=VILLAIN_REGISTRY[params.villain]["form"],
        city_type=CITY_REGISTRY[params.city]["type"],
        city_mood=CITY_REGISTRY[params.city]["mood"],
        hero_power=HERO_REGISTRY[params.hero]["power"],
    )

    hero_ent.memes["determination"] += 1.0
    ally_ent.memes["trust"] += 1.0
    villain_ent.meters["stability"] -= 1.5

    story = "\n\n".join(_build_story_lines(world))
    prompts = [
        f"Write a superhero story about {params.hero} and {params.ally} in {params.city}.",
        f"Include a grizzly scour, an inner monologue, a quest, and a happy ending.",
        f"Make sure the hero must terminate the threat without losing the city's hope.",
    ]
    story_qa = [
        QAItem(question=f"What kind of threat was in the story?", answer=f"It was a {world.facts['villain_form']} that acted like a scour."),
        QAItem(question="What did the hero think during the inner monologue?", answer=_fill(arc.inner_monologue, world.facts)),
        QAItem(question="How did the ally help change the plan?", answer=f"{ally_line}"),
        QAItem(question="What happened at the end?", answer=arc.ending_image),
        QAItem(question="What did the hero and ally try to do?", answer=f"They went on a quest to terminate the scour and keep the city safe."),
    ]
    world_qa = [
        QAItem(question="What is a hero?", answer="A hero is a character who tries to protect others and do what is right."),
        QAItem(question="What is a quest?", answer="A quest is a mission or journey to accomplish an important goal."),
        QAItem(question="What is an inner monologue?", answer="An inner monologue is a character's private thoughts, not spoken out loud."),
        QAItem(question="What is a happy ending?", answer="A happy ending is when the story finishes with safety, relief, or joy."),
        QAItem(question="What does terminate mean?", answer="Terminate means to end or stop something completely."),
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


def asp_facts() -> str:
    from storyworlds import asp
    lines = [asp.fact("city", c.lower()) for c in CITY_REGISTRY]
    lines += [asp.fact("feature", "inner_monologue"), asp.fact("feature", "quest"), asp.fact("feature", "happy_ending")]
    lines += [asp.fact("seed_word", "terminate"), asp.fact("seed_word", "grizzly"), asp.fact("seed_word", "scour")]
    return "\n".join(lines)


ASP_RULES = r"""
allowed_story(City) :- city(City), feature(inner_monologue), feature(quest), feature(happy_ending).
has_seed_word(terminate) :- seed_word(terminate).
has_seed_word(grizzly) :- seed_word(grizzly).
has_seed_word(scour) :- seed_word(scour).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _valid_python() -> list[tuple]:
    return [(c.lower(),) for c in CITY_REGISTRY]


def _asp_valid() -> list[tuple]:
    from storyworlds import asp
    model = asp.one_model(asp_program("#show allowed_story/1. #show has_seed_word/1."))
    allowed = set(asp.atoms(model, "allowed_story"))
    return sorted(allowed)


def asp_verify() -> int:
    py = set(_valid_python())
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
        print(asp_program("#show allowed_story/1. #show has_seed_word/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        from storyworlds import asp
        for atom in asp.atoms(asp.one_model(asp_program("#show allowed_story/1.")), "allowed_story"):
            print(atom[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for city in CITY_REGISTRY:
            params = StoryParams(city=city, hero="Nova", ally="Patch", villain="the Grizzle Scour")
            params.seed = base_seed
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
