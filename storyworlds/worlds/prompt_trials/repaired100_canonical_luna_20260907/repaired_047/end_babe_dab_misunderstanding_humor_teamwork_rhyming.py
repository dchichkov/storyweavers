#!/usr/bin/env python3
"""
A standalone rhyming storyworld about a tiny mix-up, a dab of color,
and teamwork that brings laughter to the end.
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
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
story_kind(rhyming_story).
feature(misunderstanding).
feature(humor).
feature(teamwork).
seed_word(end).
seed_word(babe).
seed_word(dab).
has_turn(S) :- story(S), feature(misunderstanding), feature(humor).
has_resolution(S) :- story(S), feature(teamwork), has_turn(S).
good_story(S) :- has_resolution(S), ending_warm(S).
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    name: str
    partner: str
    object: str
    color: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    opening: str
    trouble: str
    misunderstanding: str
    clue: str
    partner_line: str
    joke: str
    repair: str
    result: str
    ending: str


@dataclass
class World:
    place: str = "a little town stage"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in self.entities.values():
            bits = []
            if entity.meters:
                bits.append(f"meters={dict(entity.meters)}")
            if entity.memes:
                bits.append(f"memes={dict(entity.memes)}")
            if entity.label:
                bits.append(f"label={entity.label!r}")
            lines.append(
                f"  {entity.id:10} ({entity.kind:9}) {' '.join(bits)}"
            )
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


SCENARIOS = [
    Scenario(
        key="painted_hat",
        opening="A village parade was ready to begin with a clap and a cheer.",
        trouble="A bright hat was waiting, but its blue feather had disappeared.",
        misunderstanding="Luna heard 'blue feather' and searched for a bird instead of the hat.",
        clue="a tiny blue dab marked the wagon wheel beside the hat box",
        partner_line='"The feather is painted, not flown," said her partner with a grin.',
        joke="Luna bowed to a pigeon, which bowed back and looked quite pleased.",
        repair="they followed the blue dabs from wheel to box and fixed the feather with a tidy knot",
        result="The hat stood tall, and the parade captain could see the road ahead.",
        ending="At the end, Luna and her partner marched beneath the hat while the pigeon strutted behind.",
    ),
    Scenario(
        key="missing_muffin",
        opening="At the end of the market lane, a music cart played a bouncing tune.",
        trouble="The performers had one muffin for two hungry helpers.",
        misunderstanding="Luna thought 'one for two' meant one muffin should be cut into two hats.",
        clue="a floury dab on the plate showed where the muffin had rolled",
        partner_line='"Two pieces, not two bonnets," her partner laughed.',
        joke="Luna placed a crumb on her head and called it a breakfast crown.",
        repair="they split the muffin neatly and shared the crumbs with the sleepy cart horse",
        result="Everyone had a bite, and the cart horse gave one thankful snort.",
        ending="At the end, the tune rhymed with 'chew,' and the whole team sang, 'Me and you!'",
    ),
    Scenario(
        key="backward_banner",
        opening="The town square shimmered with ribbons for the evening show.",
        trouble="The welcome banner hung backward, so its words faced the empty wall.",
        misunderstanding="Luna believed the wall was the audience and began waving to it.",
        clue="a red dab on the floor matched the banner's left-hand corner",
        partner_line='"The wall is quiet, but our friends are not," said her partner.',
        joke="The wall received three bows and seemed too shy to applaud.",
        repair="they turned the banner around together and tied both corners to the same rail",
        result="The words welcomed every neighbor who entered the square.",
        ending="At the end, even the quiet wall wore a stripe of sunset and looked part of the show.",
    ),
    Scenario(
        key="sleepy_drum",
        opening="Before sunrise, a little band gathered beside the bakery door.",
        trouble="The drum made no sound, though everyone tapped it with care.",
        misunderstanding="Luna whispered that the drum must be asleep and brought it a blanket.",
        clue="a small dab of flour covered the loose drum cord",
        partner_line='"It needs a knot, not a nap," her partner said.',
        joke="The drum wore the blanket like a cape and looked ready for a royal concert.",
        repair="they brushed away the flour, tightened the cord, and tested the drum together",
        result="Boom went the drum, and the bakery windows gave a happy tremble.",
        ending="At the end, the band played a warm beat while the drum kept its blanket cape nearby.",
    ),
    Scenario(
        key="wrong_wagon",
        opening="A tiny circus wagon rolled toward the field with bells on every side.",
        trouble="The team needed the wagon of props, but two wagons looked exactly alike.",
        misunderstanding="Luna chose the wagon marked with a star, thinking every star meant 'stage.'",
        clue="a green dab on one wheel matched the prop list",
        partner_line='"That star says sparkle; the green dab says props," her partner explained.',
        joke="Luna asked the star whether it could juggle, and it stayed impressively silent.",
        repair="they pushed the green-dabbed wagon to the field and checked each prop together",
        result="The juggling scarves, hoops, and tiny bells arrived before the curtain rose.",
        ending="At the end, the star wagon sparkled nearby while the teamwork wagon stole the show.",
    ),
    Scenario(
        key="crooked_crown",
        opening="A baby royal parade was planned for the village's youngest guest.",
        trouble="The little crown leaned sideways and tickled the guest's nose.",
        misunderstanding="Luna thought the crown was trying to whisper a secret.",
        clue="a golden dab showed that one soft ribbon had slipped loose",
        partner_line='"It is not whispering; it is wobbling," said her partner.',
        joke="The crown received a tiny reply: 'Please speak up, Your Wobbliness.'",
        repair="they held the crown steady, retied the ribbon, and checked the fit with a gentle nod",
        result="The guest could smile, wave, and see the parade clearly.",
        ending="At the end, the crown sat straight, and its crooked shadow danced beside the team.",
    ),
    Scenario(
        key="vanishing_chalk",
        opening="The sidewalk rhyme was ready, with swirls and stars along the street.",
        trouble="The yellow chalk vanished just before the final line.",
        misunderstanding="Luna searched the sky because she thought a yellow moon had borrowed it.",
        clue="a yellow dab led beneath the bench where the chalk had rolled",
        partner_line='"The moon is innocent; the bench has yellow toes," her partner said.',
        joke="Luna interviewed the moon anyway, and it answered with one round glow.",
        repair="they reached beneath the bench together and finished the last bright rhyme",
        result="The sidewalk poem stretched from the first star to its cheerful end.",
        ending="At the end, the yellow line curled like a smile around every helping hand.",
    ),
]


NAMES = ["Luna", "Babe", "Milo", "Tess", "Nia", "Pip", "Ollie", "Zara"]
PARTNERS = ["Babe", "Milo", "Tess", "Pip", "Nia", "Ollie"]
OBJECTS = ["hat", "muffin", "banner", "drum", "wagon", "crown", "chalk"]
COLORS = ["blue", "red", "yellow", "green", "golden", "purple"]

ACTIONS = {
    "hat": "carried the hat box carefully",
    "muffin": "set the muffin on a clean cloth",
    "banner": "held the banner flat between them",
    "drum": "steadied the drum against the cart",
    "wagon": "gripped the wagon handles together",
    "crown": "held the crown at a friendly height",
    "chalk": "placed the chalk on the dry pavement",
}

OPENING_RHYME = [
    "They hummed a little rhyme: 'A mix-up may appear, but helping friends can make it clear.'",
    "A cheerful couplet floated by: 'When clues are small and giggles grow, together we can make things go.'",
    "Luna tapped a beat and sang, 'A puzzled start need not feel sad; teamwork turns the muddle glad.'",
]

RESPONSE_RHYME = [
    "They answered with a rhyme: 'Look twice, ask why, then give a try.'",
    "Their plan had a beat: 'No need to blame, we share the game.'",
    "Babe clapped the rhythm: 'A careful clue can see us through.'",
]


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("The story needs a named main character.")
    if not params.partner.strip():
        raise StoryError("The teamwork story needs a named partner.")
    if params.name.strip().lower() == params.partner.strip().lower():
        raise StoryError("The main character and partner must be different people.")
    if params.object not in OBJECTS:
        raise StoryError("The object must be a gentle parade or performance prop.")
    if params.color not in COLORS:
        raise StoryError("The color must be a simple, visible story color.")


def valid_params(rng: random.Random) -> StoryParams:
    name = rng.choice(NAMES)
    partner_choices = [p for p in PARTNERS if p != name] or ["Babe"]
    return StoryParams(
        name=name,
        partner=rng.choice(partner_choices),
        object=rng.choice(OBJECTS),
        color=rng.choice(COLORS),
        seed=rng.randrange(2**31),
    )


def build_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity("hero", "character", params.name))
    partner = world.add(Entity("partner", "character", params.partner))
    object_ent = world.add(Entity("object", "prop", params.object, owner=params.name))
    dab = world.add(Entity("dab", "clue", f"{params.color} dab"))
    world.facts.update(
        hero=hero,
        partner=partner,
        object=object_ent,
        dab=dab,
        place=world.place,
        misunderstanding=True,
        humor=True,
        teamwork=True,
        rhyming=True,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    hero = world.get("hero")
    partner = world.get("partner")
    object_ent = world.get("object")
    dab = world.get("dab")

    hero.bump_meme("curiosity")
    partner.bump_meme("patience")
    object_ent.bump_meter("importance")
    dab.bump_meter("visibility")

    world.say(scenario.opening)
    world.say(
        f"{hero.label} and {partner.label} brought a {object_ent.label} for the show, "
        f"and {hero.label} promised, 'We will reach the end together.'"
    )
    world.say(rng.choice(OPENING_RHYME))
    world.para()

    world.say(scenario.trouble)
    world.say(
        f"The trouble caused a misunderstanding: {scenario.misunderstanding} "
        f"{hero.label} made one brave, funny guess."
    )
    world.say(scenario.joke)
    world.say(scenario.partner_line)
    world.para()

    hero.bump_meme("humor")
    partner.bump_meme("trust")
    world.say(f"Then they noticed the clue: {scenario.clue}.")
    world.say(f"The {dab.label} helped them understand what had really happened.")
    world.say(rng.choice(RESPONSE_RHYME))
    world.para()

    hero.bump_meter("teamwork")
    partner.bump_meter("teamwork")
    world.say(f"Together, {hero.label} {ACTIONS[object_ent.label]}.")
    world.say(f"Side by side, they {scenario.repair}.")
    world.say(scenario.result)
    world.para()

    hero.bump_meme("joy")
    partner.bump_meme("joy")
    world.say(
        f"{hero.label} laughed, {partner.label} laughed, and the mix-up became "
        "the funniest part of the day."
    )
    world.say(scenario.ending)
    world.say(
        "They learned that a misunderstanding can shrink when friends ask, listen, "
        "and work together."
    )

    world.facts.update(
        scenario=scenario.key,
        trouble=scenario.trouble,
        misunderstanding=scenario.misunderstanding,
        clue=scenario.clue,
        partner_line=scenario.partner_line,
        joke=scenario.joke,
        repair=scenario.repair,
        result=scenario.result,
        ending=scenario.ending,
        resolved=True,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    hero = facts["hero"].label
    partner = facts["partner"].label
    obj = facts["object"].label
    return [
        f"Write a rhyming story in which {hero} and {partner} solve a funny misunderstanding about a {obj}.",
        "Write a child-friendly story using the words end, babe, and dab, with humor and teamwork.",
        f"Tell a rhyming tale where a small clue turns a mix-up into a happy ending for {hero} and {partner}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"].label
    partner = facts["partner"].label
    return [
        QAItem(
            question="What trouble began the story?",
            answer=str(facts["trouble"]),
        ),
        QAItem(
            question=f"What did {hero} misunderstand?",
            answer=f"{hero} misunderstood that {facts['misunderstanding']}",
        ),
        QAItem(
            question=f"What clue helped {hero} and {partner} understand the problem?",
            answer=f"They noticed that {facts['clue']}.",
        ),
        QAItem(
            question="How did the friends solve the trouble?",
            answer=f"They worked together and {facts['repair']}.",
        ),
        QAItem(
            question="What showed that the story ended happily?",
            answer=str(facts["ending"]),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone gets the meaning of a word, clue, or event wrong.",
        ),
        QAItem(
            question="Why can humor help during a mistake?",
            answer="Humor can help people relax and notice a mistake without feeling ashamed.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people share ideas and actions to solve something together.",
        ),
        QAItem(
            question="What is a dab?",
            answer="A dab is a small spot or touch of something, such as paint or flour.",
        ),
    ]


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("story", "rhyming"),
            asp.fact("story_kind", "rhyming_story"),
            asp.fact("feature", "misunderstanding"),
            asp.fact("feature", "humor"),
            asp.fact("feature", "teamwork"),
            asp.fact("seed_word", "end"),
            asp.fact("seed_word", "babe"),
            asp.fact("seed_word", "dab"),
            asp.fact("ending_warm", "rhyming"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    program = asp_program(
        "#show has_turn/1.\n#show has_resolution/1.\n#show good_story/1."
    )
    model = asp.one_model(program)
    found = {
        (symbol.name, tuple(
            arg.name if arg.type != 4 else arg.string
            for arg in symbol.arguments
        ))
        for symbol in model
        if symbol.name in {"has_turn", "has_resolution", "good_story"}
    }
    expected = {
        ("has_turn", ("rhyming",)),
        ("has_resolution", ("rhyming",)),
        ("good_story", ("rhyming",)),
    }
    if found != expected:
        print("MISMATCH between ASP and Python story gate.")
        print("ASP:", sorted(found))
        print("PY :", sorted(expected))
        return 1

    for params in (
        StoryParams("Luna", "Babe", "hat", "blue", 11),
        StoryParams("Milo", "Tess", "drum", "golden", 29),
    ):
        sample = generate(params)
        if not sample.story.strip() or not sample.story_qa:
            print("Generated-story verification failed.")
            return 1

    print("OK: ASP twin matches the Python gate and generated stories pass.")
    return 0


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_story/1."))
    return sorted(asp.atoms(model, "good_story"))


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    return world.trace()


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rhyming storyworld about misunderstanding, humor, and teamwork."
    )
    parser.add_argument("--name")
    parser.add_argument("--partner")
    parser.add_argument("--object", choices=OBJECTS)
    parser.add_argument("--color", choices=COLORS)
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
    params = valid_params(rng)
    if args.name:
        params.name = args.name
    if args.partner:
        params.partner = args.partner
    if args.object:
        params.object = args.object
    if args.color:
        params.color = args.color
    reasonableness_gate(params)
    return params


CURATED = [
    StoryParams("Luna", "Babe", "hat", "blue", 11),
    StoryParams("Milo", "Tess", "drum", "golden", 29),
    StoryParams("Nia", "Pip", "chalk", "yellow", 47),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("ASP-compatible rhyming stories:")
        for item in asp_list():
            print(item)
        return

    rng = random.Random(
        args.seed if args.seed is not None else random.randrange(2**31)
    )

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            params = resolve_params(
                args, random.Random(rng.randrange(2**31))
            )
            sample = generate(params)
            attempts += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
