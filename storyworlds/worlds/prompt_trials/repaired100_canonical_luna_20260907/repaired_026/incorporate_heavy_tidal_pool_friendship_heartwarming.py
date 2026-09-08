#!/usr/bin/env python3
"""
A heartwarming tidal-pool storyworld about incorporating a heavy shell into a
friendship project.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_here))))
if os.path.exists(os.path.join(_root, "results.py")):
    sys.path.insert(0, _root)
else:
    sys.path.insert(0, os.path.dirname(os.path.dirname(_root)))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Luna"
    friend_name: str = "Milo"
    place: str = "the tidal pool"
    object_name: str = "the heavy moon shell"


HERO_NAMES = ["Luna", "Nia", "Pia", "Sora", "Mara"]
FRIEND_NAMES = ["Milo", "Tavi", "Finn", "Wren", "Ollie"]
PLACES = ["the tidal pool", "the rocky tidal pool", "the bright tidal pool"]

ARCS = [
    {
        "discovery": "a broad moon shell wedged beneath a curtain of sea lettuce",
        "weight": "heavier than either child expected",
        "project": "a welcome sign for the smallest tide-pool creatures",
        "problem": "the shell was too heavy to lift safely and could crack the little ledge where they wanted to place it",
        "plan": "use a long piece of driftwood as a lever",
        "method": "they slid driftwood beneath one edge, pushed together, and rolled the shell onto a bed of soft kelp",
        "result": "the shell became the round center of their sign, while its empty spiral held a tiny flag",
        "ending": "When the tide returned, the shell shone beside the sign, and both friends watched a hermit crab wave from its doorway.",
    },
    {
        "discovery": "a round, silver shell resting between two dark rocks",
        "weight": "so heavy that the wet sand dimpled beneath it",
        "project": "a shared garden for sea snails and anemones",
        "problem": "dragging it would scrape the pool's living carpet and leave the creatures without a safe place",
        "plan": "make a smooth path with flat stones and move it only during the calmest moment",
        "method": "they laid flat stones across the sand, waited for a gentle wave, and guided the shell one careful inch at a time",
        "result": "the shell became a shelter at the garden's edge, where its curve protected a cluster of young anemones",
        "ending": "The next wave filled the new garden with bubbles, and Luna and Milo smiled as the anemones opened like small stars.",
    },
    {
        "discovery": "a dark spiral shell caught under a little bridge of coral",
        "weight": "heavy enough to make their arms wobble",
        "project": "a friendship plaque for visitors who cared for the shore",
        "problem": "pulling it free could loosen the coral bridge and harm the tiny animals beneath it",
        "plan": "ask the beach ranger for help instead of rushing",
        "method": "they marked the spot with a bright pebble and called the ranger, who showed them how to free the shell without touching the coral",
        "result": "the shell was incorporated into a low, safe plaque beside the pool",
        "ending": "At sunset, the plaque caught the gold light, and the friends added their names beneath the words: CARE FOR ONE ANOTHER.",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heartwarming Friendship story at a tidal pool.")
    parser.add_argument("--hero-name")
    parser.add_argument("--friend-name")
    parser.add_argument("--place")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero_name or rng.choice(HERO_NAMES)
    friend = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != hero])
    place = args.place or rng.choice(PLACES)
    if not place or "tidal pool" not in place.lower():
        raise StoryError("place must describe a tidal pool")
    if hero == friend:
        raise StoryError("the hero and friend must have different names")
    return StoryParams(
        seed=args.seed,
        hero_name=hero,
        friend_name=friend,
        place=place,
    )


def make_world(params: StoryParams) -> World:
    world = World()
    world.add(Entity(
        "hero", "child", params.hero_name,
        meters={"strength": 0.6, "safety": 0.7},
        memes={"hope": 0.8, "friendship": 0.7, "worry": 0.1},
    ))
    world.add(Entity(
        "friend", "child", params.friend_name,
        meters={"strength": 0.6, "safety": 0.7},
        memes={"hope": 0.7, "friendship": 0.7, "worry": 0.1},
    ))
    world.add(Entity(
        "shell", "natural object", params.object_name,
        meters={"weight": 1.0, "fragility": 0.5, "tide_risk": 0.6},
        memes={},
    ))
    world.facts["place"] = params.place
    return world


def tell(params: StoryParams) -> World:
    rng = random.Random(params.seed if params.seed is not None else 17)
    arc = rng.choice(ARCS)
    world = make_world(params)
    hero = world.entities["hero"]
    friend = world.entities["friend"]
    shell = world.entities["shell"]

    world.facts.update(
        discovery=arc["discovery"],
        weight=arc["weight"],
        project=arc["project"],
        problem=arc["problem"],
        plan=arc["plan"],
        method=arc["method"],
        result=arc["result"],
        ending=arc["ending"],
        arc=arc,
        resolved=False,
    )

    world.say(
        f"At {params.place}, {hero.label} and {friend.label} liked to greet every creature "
        f"that appeared between the waves."
    )
    world.say(
        f"One morning they found {arc['discovery']}. It was {arc['weight']}, but its "
        f"silver spiral made them think of a beautiful {arc['project']}."
    )
    world.para()
    world.say(f'"We can make it part of our idea," said {hero.label}. "We should incorporate it gently."')
    world.say(f'"I want to help," said {friend.label}, "but {arc["problem"]}."')
    world.say(
        f"They looked at the moving water, then at each other. Their friendship was not "
        f"about being the fastest; it was about making a careful plan together."
    )
    world.say(f'"Let us {arc["plan"]}," said {hero.label}. "We can stop if anything feels unsafe."')
    world.say(f'"Together," said {friend.label}. "I will watch the tide, and you watch the shell."')
    world.para()
    world.say(f"Slowly, {arc['method']}. They rested whenever their arms grew tired.")
    world.say(
        f"At last, {arc['result']}. The friends did not force the heavy shell into their "
        f"plan; they changed the plan so the shell and the pool could both be cared for."
    )
    world.say(
        f'{friend.label} laughed softly. "Your idea became better when we listened," {friend.label} said.'
    )
    world.say(
        f'"And your caution kept it kind," {hero.label} replied. "That is what friends do."'
    )
    world.para()
    world.say(arc["ending"])
    world.say(
        f"The tide whispered around their feet, and {hero.label} and {friend.label} knew "
        "their strongest work was the part they had done together."
    )

    hero.meters["safety"] = 1.0
    friend.meters["safety"] = 1.0
    shell.meters["tide_risk"] = 0.0
    hero.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0
    hero.memes["relief"] = 0.8
    friend.memes["relief"] = 0.8
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming Friendship story at {f['place']} where two children incorporate a heavy shell into {f['project']}.",
        f"Tell how {world.entities['hero'].label} and {world.entities['friend'].label} solve this problem together: {f['problem']}.",
        "Write a child-friendly tidal-pool story using the words incorporate and heavy, with spoken dialogue and a caring ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = world.entities["hero"].label
    friend = world.entities["friend"].label
    return [
        QAItem(
            question=f"What did {hero} and {friend} find at {f['place']}?",
            answer=f"{hero} and {friend} found {f['discovery']}, a shell that was {f['weight']}.",
        ),
        QAItem(
            question="Why could they not simply move the shell?",
            answer=f"They could not simply move it because {f['problem']}.",
        ),
        QAItem(
            question=f"How did {hero} and {friend} work together?",
            answer=f"They decided to {f['plan']}, and then {f['method']}.",
        ),
        QAItem(
            question="How did friendship change the result?",
            answer=f"The friends listened to each other and changed their plan so that {f['result']}.",
        ),
        QAItem(
            question="What showed that the problem was resolved?",
            answer=f"{f['ending']} Their careful work left the tidal pool safe and brought them closer together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tidal pool?",
            answer="A tidal pool is a small pool of seawater left among rocks when the tide goes out.",
        ),
        QAItem(
            question="What does incorporate mean?",
            answer="Incorporate means to include something as part of a larger whole.",
        ),
        QAItem(
            question="What does heavy mean?",
            answer="Heavy means weighing a lot and needing more effort to lift or move.",
        ),
        QAItem(
            question="What makes a friendship caring?",
            answer="A caring friendship includes listening, helping, and making choices that keep both friends and their surroundings safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items()}
        memes = {k: round(v, 2) for k, v in entity.memes.items()}
        lines.append(f"{entity.id}: meters={meters}, memes={memes}")
    lines.append(f"resolved={world.facts.get('resolved')}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_plan :- friendship(hero,friend), heavy(shell), protects_pool.
incorporated(shell) :- safe_plan.
happy_ending :- incorporated(shell), safe_plan.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("friendship", "hero", "friend"),
        asp.fact("heavy", "shell"),
        asp.fact("protects_pool"),
    ])


def asp_program(show: str = "#show safe_plan/0. #show incorporated/1. #show happy_ending/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    names = {sym.name for sym in model}
    expected = {"safe_plan", "happy_ending"}
    incorporated = any(sym.name == "incorporated" and str(sym.arguments[0]) == "shell" for sym in model)
    if expected.issubset(names) and incorporated:
        sample = generate(StoryParams(seed=4))
        if "together" not in sample.story.lower() or "friend" not in sample.story.lower():
            print("MISMATCH: generated story does not exercise Friendship.")
            return 1
        print("OK: ASP and Python friendship assumptions agree.")
        return 0
    print("MISMATCH between ASP and Python assumptions.")
    return 1


CURATED = [
    StoryParams(seed=1, hero_name="Luna", friend_name="Milo", place="the tidal pool"),
    StoryParams(seed=2, hero_name="Nia", friend_name="Finn", place="the rocky tidal pool"),
    StoryParams(seed=3, hero_name="Sora", friend_name="Wren", place="the bright tidal pool"),
]


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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        print("ASP atoms:")
        for atom in asp.one_model(asp_program()):
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + offset)
            params = resolve_params(args, rng)
            params.seed = base_seed + offset
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
