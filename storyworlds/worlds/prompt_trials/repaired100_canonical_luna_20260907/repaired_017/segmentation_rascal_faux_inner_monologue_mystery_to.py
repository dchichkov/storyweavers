#!/usr/bin/env python3
"""
A tall tale about a rascal, a faux clue, and a mystery solved by careful segmentation.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
for path in (ROOT, os.path.join(ROOT, "storyworlds")):
    if path not in sys.path:
        sys.path.insert(0, path)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Scene:
    place: str
    landmark: str
    object_name: str
    object_plural: str


@dataclass
class World:
    scene: Scene
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    rascal_name: str
    rascal_type: str
    object_kind: str
    seed: Optional[int] = None


SCENES = {
    "prairie": Scene(
        place="the wide prairie",
        landmark="the tallest windmill in the county",
        object_name="brass weather vane",
        object_plural="brass weather vanes",
    ),
    "canyon": Scene(
        place="the red canyon",
        landmark="a stone arch taller than a courthouse",
        object_name="silver compass",
        object_plural="silver compasses",
    ),
    "harbor": Scene(
        place="the windy harbor",
        landmark="the lighthouse on Gull Rock",
        object_name="blue signal flag",
        object_plural="blue signal flags",
    ),
}

HEROES = {
    "Luna": "girl",
    "Milo": "boy",
    "Tessa": "girl",
    "Jun": "boy",
    "Nell": "girl",
    "Otis": "boy",
}

RASCALS = {
    "Pip": "boy",
    "Rory": "girl",
    "Bram": "boy",
    "Zig": "boy",
    "Faye": "girl",
}

OBJECT_KINDS = {
    "vane": "weather vane",
    "compass": "compass",
    "flag": "signal flag",
}

OPENINGS = (
    "In {place}, where the wind could lift a wagon and carry it two counties, {hero} was known for noticing small things.",
    "Folks in {place} told a tall tale about {hero}, who could spot one crooked stitch from the top of a mountain.",
    "On a morning so bright that the shadows wore hats, {hero} reached {landmark} and found trouble waiting.",
)

INNER_THOUGHTS = (
    "“A grand mystery may wear a tiny disguise,” {hero} thought.",
    "“If the clue looks too perfect, it may be pretending,” {hero} told {hero_pronoun}self.",
    "“I must not chase the loudest answer,” {hero} thought. “I must listen to the smallest one.”",
)

ARCS = (
    {
        "title": "the backwards trail",
        "problem": "{rascal} claimed that the {object} had vanished and scattered three painted markers along the ground.",
        "faux": "The middle marker showed a giant arrow pointing straight toward the dry creek.",
        "turn": "{hero} noticed that the arrow was painted on a loose scrap, while the two real markers were nailed to old fence posts.",
        "action": "{hero} used segmentation, separating the clue into paint, wood, nail, and direction instead of treating it as one grand sign.",
        "reveal": "The loose marker was faux. It pointed away from a small burrow where {rascal} had tucked the missing {object}.",
        "ending": "The wind spun the recovered {object} so hard that every hat nearby flew into the same fence.",
    },
    {
        "title": "the giant footprint",
        "problem": "{rascal} announced that a monster had stolen the {object}, leaving a trail of enormous footprints.",
        "faux": "The prints marched from {landmark} toward the tallest hill.",
        "turn": "{hero} saw that each print had the same tiny notch at its heel, exactly like the sole of {rascal}'s boot.",
        "action": "{hero} practiced segmentation again, separating toe marks, heel marks, and the spaces between them.",
        "reveal": "The monster prints were faux footprints made by pressing one boot twice in each patch of mud, and the missing {object} was hidden beneath {rascal}'s cape.",
        "ending": "When {rascal} returned the {object}, the real wind made a footprint-shaped splash that reached clear across the road.",
    },
    {
        "title": "the singing clue",
        "problem": "{rascal} said the missing {object} had sung a secret message before disappearing.",
        "faux": "A row of bottles hummed whenever the wind blew past {landmark}.",
        "turn": "{hero} heard that only every third bottle made a sound, while the others merely rattled.",
        "action": "{hero} divided the sounds into segments and followed the repeating hum-rattle-hum pattern.",
        "reveal": "The bottle song was faux news. Its real pattern spelled a hiding place beneath {rascal}'s basket.",
        "ending": "The recovered {object} rang once, loudly enough to wake a sleeping crow three valleys away.",
    },
)

DIALOGUES = (
    '"Did you see the clue?" {rascal} asked. "I saw a clue, a trick, and a very nervous boot," {hero} replied.',
    '"The mystery is enormous!" {rascal} cried. "Then we can solve it one small piece at a time," {hero} said.',
    '{hero} asked, "Why is this mark different?" {rascal} swallowed. "Different is not the same as guilty," {hero} added gently.',
)

RESPONSES = (
    '"You caught my trick," {rascal} said. {hero} answered, "You can use your cleverness for helping next time."',
    "{rascal}'s shoulders dropped. Then {rascal} smiled, because solving the mystery felt better than hiding it.",
    '"I thought a tall tale needed a tall trick," {rascal} admitted. "A true answer is taller," {hero} said.',
)


def pronoun(kind: str, case: str = "subject") -> str:
    if kind == "girl":
        return {"subject": "she", "object": "her", "possessive": "her", "self": "her"}[case]
    return {"subject": "he", "object": "him", "possessive": "his", "self": "him"}[case]


def render(text: str, world: World, hero: Entity, rascal: Entity, obj: Entity) -> str:
    return text.format(
        place=world.scene.place,
        landmark=world.scene.landmark,
        object=obj.label,
        hero=hero.id,
        hero_pronoun=pronoun(hero.type, "self"),
        rascal=rascal.id,
    )


def simulate(params: StoryParams) -> World:
    scene = SCENES[params.place]
    world = World(scene)
    hero = world.add(Entity(params.hero_name, "character", params.hero_type, params.hero_name))
    rascal = world.add(Entity(params.rascal_name, "character", params.rascal_type, params.rascal_name))
    obj = world.add(
        Entity(
            "mystery_object",
            "thing",
            params.object_kind,
            scene.object_name,
            owner="townsfolk",
        )
    )
    rng = random.Random(params.seed if params.seed is not None else 0)
    arc = rng.choice(ARCS)
    dialogue = rng.choice(DIALOGUES)
    response = rng.choice(RESPONSES)
    opening = rng.choice(OPENINGS)
    thought = rng.choice(INNER_THOUGHTS)

    world.facts.update(hero=hero, rascal=rascal, obj=obj, arc=arc)
    world.say(render(opening, world, hero, rascal, obj))
    world.say(
        f"The townsfolk had trusted {obj.label} to keep watch, but it disappeared before breakfast."
    )
    world.say(render(arc["problem"], world, hero, rascal, obj))
    world.para()

    obj.meters["missing"] = 1.0
    rascal.memes["mischief"] = 1.0
    world.say(render(arc["faux"], world, hero, rascal, obj))
    world.say(render(thought, world, hero, rascal, obj))
    world.say(render(dialogue, world, hero, rascal, obj))
    world.para()

    hero.memes["curious"] = 1.0
    world.say(render(arc["turn"], world, hero, rascal, obj))
    world.say(render(arc["action"], world, hero, rascal, obj))
    world.para()

    obj.meters["found"] = 1.0
    obj.meters["missing"] = 0.0
    rascal.memes["honest"] = 1.0
    world.say(render(arc["reveal"], world, hero, rascal, obj))
    world.say(render(response, world, hero, rascal, obj))
    world.para()

    hero.memes["relief"] = 1.0
    rascal.memes["pride"] = 1.0
    world.say(
        f"{hero.id} returned the {obj.label} to its place, and {rascal.id} helped secure it with a proper knot."
    )
    world.say(render(arc["ending"], world, hero, rascal, obj))
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    arc = f["arc"]
    hero: Entity = f["hero"]
    obj: Entity = f["obj"]
    return [
        f"Write a Tall Tale about {hero.id} solving {arc['title']} involving a missing {obj.label}.",
        "Include a rascal, a faux clue, segmentation, an inner monologue, and a mystery to solve.",
        f"Make the ending prove how {hero.id} used careful observation rather than guessing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    rascal: Entity = world.facts["rascal"]
    obj: Entity = world.facts["obj"]
    arc = world.facts["arc"]
    return [
        QAItem(
            f"What mystery did {hero.id} solve?",
            f"{hero.id} solved the mystery of the missing {obj.label}. The clue was designed to send everyone toward the wrong answer.",
        ),
        QAItem(
            f"Why was the clue faux?",
            f"The clue was faux because {arc['faux'].replace('{rascal}', rascal.id).replace('{hero}', hero.id).replace('{object}', obj.label)} {hero.id} found a detail that did not belong with the genuine clues.",
        ),
        QAItem(
            f"How did segmentation help {hero.id}?",
            f"{hero.id} separated the clue into smaller parts instead of accepting it as one object. That revealed which part had been planted by {rascal.id}.",
        ),
        QAItem(
            f"What did {rascal.id} do after the mystery was solved?",
            f"{rascal.id} returned the {obj.label}, admitted the trick, and helped {hero.id} secure it properly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does segmentation mean?",
            "Segmentation means dividing something into smaller parts so each part can be examined more clearly.",
        ),
        QAItem(
            "What is a faux clue?",
            "A faux clue is a false or misleading sign that looks as if it belongs to a mystery but points away from the truth.",
        ),
        QAItem(
            "Why is careful observation useful?",
            "Careful observation helps a solver notice small differences, test claims, and choose an answer supported by evidence.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(H,R,O) :- hero(H), rascal(R), object(O), missing(O), observes(H).
solved(H,O) :- reasonable(H,_,O), segments(H), found(O).
honest(R) :- rascal(R), found(_).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for place in SCENES:
        lines.append(asp.fact("place", place))
    lines.extend(
        [
            asp.fact("hero", "luna"),
            asp.fact("rascal", "pip"),
            asp.fact("object", "mystery_object"),
            asp.fact("missing", "mystery_object"),
            asp.fact("observes", "luna"),
            asp.fact("segments", "luna"),
            asp.fact("found", "mystery_object"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str = "#show solved/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        solved = asp.atoms(model, "solved")
        if ("luna", "mystery_object") not in solved:
            print("ASP verification failed: expected solved(luna,mystery_object).")
            return 1
        print("OK: ASP rules agree that careful segmentation solves the mystery.")
        return 0
    except Exception as exc:
        print(f"ASP verification failed: {exc}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tall Tale segmentation mystery storyworld.")
    parser.add_argument("--place", choices=sorted(SCENES))
    parser.add_argument("--hero-name", choices=sorted(HEROES))
    parser.add_argument("--rascal-name", choices=sorted(RASCALS))
    parser.add_argument("--object-kind", choices=sorted(OBJECT_KINDS), default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SCENES))
    hero_name = args.hero_name or rng.choice(list(HEROES))
    rascal_name = args.rascal_name or rng.choice(list(RASCALS))
    if hero_name == rascal_name:
        raise StoryError("Hero and rascal must be different people.")
    kind = args.object_kind or {
        "prairie": "vane",
        "canyon": "compass",
        "harbor": "flag",
    }[place]
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=HEROES[hero_name],
        rascal_name=rascal_name,
        rascal_type=RASCALS[rascal_name],
        object_kind=kind,
        seed=rng.randrange(2**31),
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
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
    if trace and sample.world:
        print("\n--- trace ---")
        for entity in sample.world.entities.values():
            print(entity.id, entity.type, dict(entity.meters), dict(entity.memes))
    if qa:
        print("\n" + format_qa(sample))


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

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("prairie", "Luna", "girl", "Pip", "boy", "vane", 11),
            StoryParams("canyon", "Milo", "boy", "Rory", "girl", "compass", 22),
            StoryParams("harbor", "Tessa", "girl", "Bram", "boy", "flag", 33),
        ]
    else:
        params_list = [
            resolve_params(args, random.Random(seed + i))
            for i in range(max(1, args.n))
        ]

    samples = [generate(p) for p in params_list]
    if args.json:
        print(
            samples[0].to_json()
            if len(samples) == 1
            else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False)
        )
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### story {i + 1}" if len(samples) > 1 else "",
        )
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
