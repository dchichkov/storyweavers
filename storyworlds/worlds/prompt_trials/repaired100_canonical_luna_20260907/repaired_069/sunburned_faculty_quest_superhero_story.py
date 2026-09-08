#!/usr/bin/env python3
"""Child-friendly superhero quests about sunburned faculty and helpful teamwork."""

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
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    faculty_member: str = "Professor Vale"
    teammate: str = "Milo"
    campus: str = "Brightstone Academy"
    quest: int = 0
    opening: int = 0
    dialogue: int = 0
    discovery: int = 0
    ending: int = 0


HEROES = ["Luna", "Nova", "Mira", "Skye", "Pax"]
FACULTY = ["Professor Vale", "Dr. Reed", "Coach Ember", "Dean Moss"]
TEAMMATES = ["Milo", "Tara", "Juno", "Finn"]
CAMPUSES = ["Brightstone Academy", "Sunbeam School", "Cedar Hill College"]

QUESTS = [
    {
        "title": "the shade-shield quest",
        "problem": "The academy's shade shield had stopped above the courtyard, leaving the faculty in the blazing sun.",
        "risk": "The sunburned faculty could not safely finish the outdoor science fair.",
        "clue": "Luna noticed that the shield's crystal glowed whenever the old bell rang.",
        "action": "Luna rang the bell in a steady rhythm while Milo held the mirror toward the crystal.",
        "result": "The shade shield unfolded like a silver flower and cooled the courtyard.",
        "lesson": "A careful signal and a helpful teammate can awaken hidden strength.",
        "object": "shade shield",
    },
    {
        "title": "the water-star quest",
        "problem": "A water-star beacon had fallen into the dry athletic field, and the faculty needed it to call the cooling clouds.",
        "risk": "The sunburned faculty were growing weak before the school celebration began.",
        "clue": "Luna saw three blue marks leading from the field to the garden pump.",
        "action": "Luna followed the marks while Tara turned the pump one slow click at a time.",
        "result": "The beacon filled with cool mist and sent a shining cloud across the field.",
        "lesson": "Following evidence is stronger than rushing toward a guess.",
        "object": "water-star beacon",
    },
    {
        "title": "the rooftop rescue quest",
        "problem": "The faculty's emergency sun umbrellas had blown onto the library roof.",
        "risk": "The sunburned faculty needed the umbrellas before the noon assembly.",
        "clue": "Luna found a trail of red ribbon caught on the rooftop vents.",
        "action": "Luna used her wind-glove to pull the ribbons into a safe line while Juno anchored the rescue rope.",
        "result": "The umbrellas floated down gently, one after another, without a single torn page.",
        "lesson": "Bravery works best when it is paired with a safe plan.",
        "object": "sun umbrellas",
    },
    {
        "title": "the solar-map quest",
        "problem": "A solar map had scrambled the paths to every shaded place on campus.",
        "risk": "The sunburned faculty might wander into the hottest part of the grounds.",
        "clue": "Luna saw that the map's gold lines matched the direction of the morning shadows.",
        "action": "Luna turned the map toward the clock tower while Finn marked each cool path with blue chalk.",
        "result": "The map straightened, revealing a shady route beneath the ivy arches.",
        "lesson": "Small observations can guide a whole group to safety.",
        "object": "solar map",
    },
    {
        "title": "the cooling-cape quest",
        "problem": "The faculty's cooling capes had tangled inside the hall's display machine.",
        "risk": "The sunburned faculty were waiting outside with no protection from the hot wind.",
        "clue": "Luna heard the machine click whenever one cape's silver clasp touched the side rail.",
        "action": "Luna counted the clicks while Milo turned the crank backward and freed each clasp.",
        "result": "The capes sprang loose and wrapped the faculty in cool, fluttering folds.",
        "lesson": "Patient listening can solve a noisy problem.",
        "object": "cooling capes",
    },
    {
        "title": "the cloud-lantern quest",
        "problem": "The cloud lantern that protected the playground had gone dark.",
        "risk": "The sunburned faculty could not supervise the children beneath the harsh afternoon light.",
        "clue": "Luna discovered that the lantern still held one warm spark under its copper lid.",
        "action": "Luna shielded the spark with her hands while Dean Moss polished the lantern's cloudy lens.",
        "result": "The lantern brightened and painted a wide, gentle cloud over the playground.",
        "lesson": "Protecting a small hope can give it room to grow.",
        "object": "cloud lantern",
    },
]

OPENINGS = [
    "At {campus}, young hero {hero} was practicing kind courage before the first bell.",
    "The morning sun blazed over {campus}, where {hero} kept watch from the training steps.",
    "At {campus}, {hero} wore a bright cape and carried a notebook for every superhero quest.",
    "The courtyard of {campus} shimmered like gold when {hero} heard an urgent call.",
    "Everyone at {campus} expected a normal school day, but {hero} knew adventures rarely send invitations.",
]

DIALOGUES = [
    "'The faculty need help,' called {faculty}. 'Can your hero power reach the problem?' 'My power is not enough alone,' said {hero}. 'That is why I brought a team.'",
    "'I am sunburned and stuck,' said {faculty}. {hero} answered, 'Tell me what you noticed.' 'The crystal flashes near the bell,' replied {faculty}. 'Then we have our first clue,' said {hero}.",
    "'Should we hurry?' asked {teammate}. 'Not until we know the danger,' said {hero}. {faculty} pointed to the hot courtyard. 'Good thinking. The sunburned faculty need a safe answer.'",
    "'I thought superheroes solved everything with one blast,' said {faculty}. 'A quest needs listening too,' replied {hero}. '{teammate}, will you help me test the careful plan?'",
]

DISCOVERIES = [
    "{hero} paused, drew the clue in the dust, and saw how the pieces belonged together.",
    "Instead of guessing, {hero} asked {teammate} to check the clue from the other side.",
    "The quest became clearer when {hero} compared the warm mark with the cool shadow beside it.",
    "{hero} remembered that a superpower is most useful when it makes room for other people's skills.",
]

ENDINGS = [
    "The faculty rested beneath the cool cover while {hero} and the team received three grateful cheers.",
    "By sunset, the rescued tool gleamed beside the school bell, ready for the next quest.",
    "The courtyard became a place of shade, teamwork, and quiet superhero smiles.",
    "The faculty thanked {hero}, but {hero} pointed to the whole team as the true heroes of the day.",
]


ASP_RULES = r"""
#show quest/1.
#show protected/1.
quest(Q) :- chosen_quest(Q), clue(Q), solved(Q).
protected(F) :- faculty(F), solved(Q), protects(Q,F).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("faculty", "professor_vale"),
            asp.fact("chosen_quest", "shade_shield"),
            asp.fact("clue", "shade_shield"),
            asp.fact("solved", "shade_shield"),
            asp.fact("protects", "shade_shield", "professor_vale"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld: a quest to help sunburned faculty."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--faculty", dest="faculty_member", choices=FACULTY)
    parser.add_argument("--teammate", choices=TEAMMATES)
    parser.add_argument("--campus", choices=CAMPUSES)
    parser.add_argument("--quest", type=int, choices=range(len(QUESTS)))
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
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(HEROES),
        faculty_member=args.faculty_member or rng.choice(FACULTY),
        teammate=args.teammate or rng.choice(TEAMMATES),
        campus=args.campus or rng.choice(CAMPUSES),
        quest=args.quest if args.quest is not None else rng.randrange(len(QUESTS)),
        opening=rng.randrange(len(OPENINGS)),
        dialogue=rng.randrange(len(DIALOGUES)),
        discovery=rng.randrange(len(DISCOVERIES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.faculty_member or params.hero == params.teammate:
        raise StoryError("The hero, faculty member, and teammate must be different characters.")
    if not params.campus:
        raise StoryError("A superhero quest needs a campus setting.")

    world = World()
    hero = world.add(Entity(params.hero, "hero", params.hero))
    faculty = world.add(Entity(params.faculty_member, "faculty", params.faculty_member))
    teammate = world.add(Entity(params.teammate, "teammate", params.teammate))
    quest = QUESTS[params.quest % len(QUESTS)]

    hero.meters.update({"energy": 1.0, "reach": 8.0})
    hero.memes.update({"courage": 1.0, "curiosity": 1.0})
    faculty.meters["sun_exposure"] = 0.9
    faculty.memes["worry"] = 1.0
    teammate.memes["trust"] = 1.0

    values = {
        "hero": hero.id,
        "faculty": faculty.id,
        "teammate": teammate.id,
        "campus": params.campus,
    }

    def fill(text: str) -> str:
        return text.format(**values)

    world.say(fill(OPENINGS[params.opening % len(OPENINGS)]))
    world.say(f"The {quest['title']} began when {quest['problem']}")
    world.say(quest["risk"])
    world.say(fill(DIALOGUES[params.dialogue % len(DIALOGUES)]))
    world.say(fill(DISCOVERIES[params.discovery % len(DISCOVERIES)]))
    world.say(f"{hero.id} spotted the key clue: {quest['clue']}")
    world.say(f"{hero.id} and {teammate.id} began the quest. {quest['action']}")
    world.say(quest["result"])

    hero.memes["courage"] = 1.5
    faculty.meters["sun_exposure"] = 0.1
    faculty.memes["worry"] = 0.0
    world.say(f"The {faculty.id} smiled as the shade reached the last warm step.")
    world.say(fill(ENDINGS[params.ending % len(ENDINGS)]))
    world.say(f"Lesson learned: {quest['lesson']}")

    world.facts.update(
        hero=hero,
        faculty=faculty,
        teammate=teammate,
        campus=params.campus,
        quest=quest,
        quest_title=quest["title"],
        solved=True,
        protected=True,
        lesson=quest["lesson"],
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    faculty = world.facts["faculty"]
    quest = world.facts["quest"]
    return [
        f"Write a child-friendly superhero story about {hero.id} completing {quest['title']}.",
        f"Tell a story in which {hero.id} helps sunburned faculty using a clue and a teammate.",
        f"Create a superhero quest ending with the faculty safe and a clear lesson about teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    faculty = world.facts["faculty"]
    teammate = world.facts["teammate"]
    quest = world.facts["quest"]
    return [
        QAItem(
            question=f"What problem did {hero.id} face?",
            answer=f"{hero.id} had to complete {quest['title']}: {quest['problem']}",
        ),
        QAItem(
            question=f"Why did {faculty.id} need help?",
            answer=f"The faculty were sunburned and needed protection before they could safely finish their work.",
        ),
        QAItem(
            question=f"What clue helped {hero.id}?",
            answer=quest["clue"],
        ),
        QAItem(
            question=f"How did {hero.id} and {teammate.id} solve the quest?",
            answer=quest["action"],
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The quest succeeded, and the faculty became safe and cool. {quest['result']}",
        ),
        QAItem(
            question="What lesson was learned?",
            answer=f"The lesson was: {quest['lesson']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sunburned mean?",
            answer="Sunburned means skin has become sore and red from too much strong sunlight.",
        ),
        QAItem(
            question="What is faculty?",
            answer="Faculty are the teachers and other people who work at a school or college.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a purposeful adventure in which someone tries to complete an important task.",
        ),
        QAItem(
            question="Why should people seek shade in strong sunlight?",
            answer="Shade helps protect people from too much sunlight and can help them stay cooler.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for number, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{number}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: type={entity.type}, "
            f"meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_valid() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest/1.\n#show protected/1."))
    return set(asp.atoms(model, "quest"))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show quest/1.\n#show protected/1."))
    quests = set(asp.atoms(model, "quest"))
    protected = set(asp.atoms(model, "protected"))
    if quests == {("shade_shield",)} and protected == {("professor_vale",)}:
        print("OK: ASP quest and protection facts match the Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("  quests:", sorted(quests))
    print("  protected:", sorted(protected))
    return 1


CURATED = [
    StoryParams(
        hero="Luna",
        faculty_member="Professor Vale",
        teammate="Milo",
        campus="Brightstone Academy",
        quest=0,
    ),
    StoryParams(
        hero="Nova",
        faculty_member="Dr. Reed",
        teammate="Tara",
        campus="Sunbeam School",
        quest=1,
        opening=1,
        dialogue=2,
        discovery=1,
        ending=3,
    ),
    StoryParams(
        hero="Skye",
        faculty_member="Dean Moss",
        teammate="Juno",
        campus="Cedar Hill College",
        quest=3,
        opening=3,
        dialogue=3,
        discovery=2,
        ending=1,
    ),
]


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
        print(asp_program("#show quest/1.\n#show protected/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        facts = sorted(asp_valid())
        print(f"{len(facts)} ASP quest facts")
        for fact in facts:
            print(fact)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        limit = max(50, args.n * 30)
        while len(samples) < args.n and attempt < limit:
            params = resolve_params(args, random.Random(base_seed + attempt))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

        if len(samples) < args.n:
            raise StoryError("Could not produce enough distinct superhero quests.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            header = f"### {sample.params.hero}: {sample.params.campus}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
