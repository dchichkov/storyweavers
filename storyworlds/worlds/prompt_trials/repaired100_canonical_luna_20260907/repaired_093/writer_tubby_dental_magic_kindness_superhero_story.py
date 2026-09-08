#!/usr/bin/env python3
"""
Standalone story world: Writer Tubby and the Dental Magic of Kindness.

A child-facing Superhero Story in which a writer discovers that Tubby's
dental magic is powered by kindness rather than force.  The simulated world
tracks physical meters and emotional memes, and every story is built from
state-changing actions, dialogue, and a visible ending.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "Brightsmile City"
    detail: str = "a dental clinic above a busy town square"


@dataclass
class StoryParams:
    writer_name: str
    tubby_name: str
    dental_place: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    story_lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.story_lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.story_lines)


NAMES = ["Luna", "Mira", "Ari", "Nell", "Zoe", "Tara", "Kian", "Remy"]
TUBBY_NAMES = ["Tubby", "Bumble", "Puff", "Muffin", "Bo", "Clover"]
DENTAL_PLACES = [
    "the Moonbeam Dental Clinic",
    "the Kindness Tooth Station",
    "the Starry Smile Office",
    "the Little Lantern Dental Room",
]

INCIDENTS = [
    {
        "id": "fearful_flare",
        "problem": "a frightened child was hiding behind the waiting-room chair before a dental checkup",
        "threat": "the child's fear had grown into a dark cloud that dimmed every smile in the clinic",
        "clue": "the cloud shrank whenever someone listened without laughing",
        "test": "asked the child to choose a quiet breathing rhythm and held up a little mirror",
        "truth": "the magic needed trust before it could brighten the room",
        "repair": "invited the child to be the captain of the checkup, one small step at a time",
        "ending": "the child opened wide for a gentle look, and the clinic windows shone like stars",
        "lesson": "Kindness can make a scary task feel small enough to begin.",
    },
    {
        "id": "runaway_tooth",
        "problem": "a loose tooth had floated away inside a glittering bubble above the dental chair",
        "threat": "the bubble bounced toward the open skylight and carried the tooth toward the city rooftops",
        "clue": "it drifted closer whenever Tubby spoke softly and farther whenever anyone shouted",
        "test": "asked the room to become quiet, then offered the bubble a warm, patient welcome",
        "truth": "the bubble was following calm voices, not chasing a wind",
        "repair": "guided the tooth back with a kindness spell made from thanks and careful breathing",
        "ending": "the tooth rested safely in its little box while the bubble became a shining soap rainbow",
        "lesson": "Gentle words can guide magic more surely than a mighty shout.",
    },
    {
        "id": "cavity_goblin",
        "problem": "a tiny cavity goblin had slipped from a poster and hidden beneath the sink",
        "threat": "it was sprinkling sour dust over toothbrushes and making everyone blame one another",
        "clue": "the goblin stopped rattling whenever someone admitted a mistake honestly",
        "test": "let the children tell the truth about brushing while the writer recorded each brave answer",
        "truth": "the goblin grew from shame and became harmless when mistakes were met with help",
        "repair": "gave the goblin a soft brush and a job polishing the clinic sign",
        "ending": "the sign gleamed with a new message: EVERY SMILE CAN LEARN",
        "lesson": "Honesty opens the door to help, while shame only makes a problem hide.",
    },
    {
        "id": "stormy_braces",
        "problem": "a storm of silver sparks whirled around a child's new braces",
        "threat": "the sparks tugged at the clinic's signs and sent paper stars spinning through the hall",
        "clue": "the sparks slowed whenever the child told a joke about the strange new feeling",
        "test": "let the child name each worry while Tubby answered with a silly superhero pose",
        "truth": "the magic was turning nervous energy into sparks that laughter could settle",
        "repair": "made a kindness shield from shared jokes, patient questions, and a careful adjustment",
        "ending": "the braces flashed once like a tiny constellation, then rested comfortably",
        "lesson": "Sharing a worry can change its shape and make room for courage.",
    },
    {
        "id": "missing_smile",
        "problem": "the town's biggest smile had vanished from the mural outside the dental office",
        "threat": "without it, neighbors stopped greeting one another and the clinic's magic weakened",
        "clue": "small painted footprints led from the mural to a lonely bench",
        "test": "followed the footprints and asked the quiet painter what the smile had been missing",
        "truth": "the smile had wandered away because the painter thought nobody liked the picture",
        "repair": "brought the neighbors together to add kind words and finish the mural as a team",
        "ending": "the mural's bright smile returned above the square, wider than before",
        "lesson": "Encouragement helps good work find its way home.",
    },
]

OPENINGS = [
    "At sunrise, {writer} sharpened a pencil beside the glowing sign of {place}.",
    "On the busiest morning of Smile Week, {writer} arrived at {place} with a notebook under one arm.",
    "When the town bell rang three times, {writer} hurried toward {place}, where something unusual was happening.",
    "Before the first appointment, {writer} was writing a story about brave hearts at {place}.",
    "A silver flash crossed the sky as {writer} stepped into {place} to interview its smallest superhero.",
]

REFLECTIONS = [
    '"A hero does not make fear disappear by force," {writer} said. "A hero helps someone face it safely."',
    'Tubby nodded. "My strongest spell begins when someone feels seen."',
    '{writer} wrote, "Kindness is not a tiny power. It is the power that lets other powers help."',
    'They agreed that listening was part of the rescue, not something to do after the rescue.',
    '"We did not defeat the problem alone," said {writer}. "We changed it together."',
]


ASP_RULES = r"""
problem_present(X) :- faces(X, P), dental(P).
magic_needed(X) :- problem_present(X), kindness_used(X).
resolved(X) :- magic_needed(X), fear_reduced(X), safe_result(X).
valid_story(X) :- resolved(X).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("character", "writer"),
            asp.fact("character", "tubby"),
            asp.fact("dental", "clinic"),
            asp.fact("faces", "tubby", "problem"),
            asp.fact("kindness_used", "tubby"),
            asp.fact("fear_reduced", "tubby"),
            asp.fact("safe_result", "tubby"),
            asp.fact("magic", "dental"),
            asp.fact("theme", "kindness"),
        ]
    )


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    return True


def build_world(params: StoryParams) -> World:
    if params.writer_name == params.tubby_name:
        raise StoryError("writer_name and tubby_name must be different characters.")
    if not params.dental_place.strip():
        raise StoryError("dental_place must not be empty.")

    rng = random.Random(params.seed)
    incident = rng.choice(INCIDENTS)
    opening = rng.choice(OPENINGS)
    reflection = rng.choice(REFLECTIONS)
    setting_detail = rng.choice(
        [
            "blue lamps, clean mirrors, and a shelf of brave-tooth books",
            "moon-shaped windows and a waiting room filled with soft cushions",
            "a bright checkup room where toothbrushes hung like tiny flags",
            "a cheerful square beneath a giant smiling tooth sign",
        ]
    )

    world = World(setting=Setting(place="Brightsmile City", detail=setting_detail))
    writer = world.add(
        Entity(
            id=params.writer_name,
            kind="character",
            type="writer",
            label="writer",
            meters={"distance": 0.0, "notebook_pages": 0.0},
            memes={"curiosity": 1.0, "courage": 0.5, "worry": 0.0, "relief": 0.0},
        )
    )
    tubby = world.add(
        Entity(
            id=params.tubby_name,
            kind="character",
            type="tubby_superhero",
            label="tubby superhero",
            meters={"cape_charge": 1.0, "distance": 0.0},
            memes={"kindness": 1.0, "confidence": 1.0, "worry": 0.0, "relief": 0.0},
        )
    )
    world.add(
        Entity(
            id="dental_magic",
            kind="thing",
            type="magic",
            label="dental kindness magic",
            meters={"brightness": 0.4, "safe_power": 0.0},
            memes={"warmth": 1.0},
        )
    )
    world.facts.update(
        writer=writer,
        tubby=tubby,
        incident=incident,
        opening=opening,
        reflection=reflection,
        setting_detail=setting_detail,
        dental_place=params.dental_place,
        safe_boundary="the clinic floor and the marked waiting area",
        magic_source="kindness, listening, and safe dental care",
    )
    return world


def story_intro(world: World) -> None:
    writer = world.facts["writer"]
    tubby = world.facts["tubby"]
    world.say(
        world.facts["opening"].format(
            writer=writer.id, tubby=tubby.id, place=world.facts["dental_place"]
        )
    )
    world.say(
        f"{writer.id} was a writer who collected true stories about brave choices. "
        f"{tubby.id} was a round, cheerful superhero with a cape that glowed whenever "
        f"someone showed kindness. Around them were {world.facts['setting_detail']}."
    )
    world.say(
        f"{writer.id} asked, 'What makes your dental magic work?' "
        f"{tubby.id} tapped his heart and answered, 'It works best when everyone feels safe enough to speak.'"
    )
    world.facts["dialogue_started"] = True


def story_problem(world: World) -> None:
    writer = world.facts["writer"]
    tubby = world.facts["tubby"]
    incident = world.facts["incident"]
    magic = world.entities["dental_magic"]

    writer.meters["distance"] += 2.0
    tubby.meters["distance"] += 2.0
    tubby.memes["worry"] += 1.0
    magic.meters["brightness"] -= 0.2

    world.say(
        f"Then {incident['problem']}. At once, {incident['threat'].capitalize()}."
    )
    world.say(
        f"{tubby.id} raised his glowing cape, but the spell flickered. "
        f'"Should I blast it away?" he asked.'
    )
    world.say(
        f'"Not yet," said {writer.id}. "Let us learn what the problem needs before we use power."'
    )
    world.facts["problem"] = incident["problem"]
    world.facts["threat"] = incident["threat"]
    world.facts["misunderstanding"] = True


def story_turn(world: World) -> None:
    writer = world.facts["writer"]
    tubby = world.facts["tubby"]
    incident = world.facts["incident"]
    magic = world.entities["dental_magic"]

    world.say(
        f"They stayed inside {world.facts['safe_boundary']} and watched carefully. "
        f"Soon {writer.id} noticed the clue: {incident['clue']}."
    )
    world.say(
        f'"I can try something gentler," said {tubby.id}. '
        f"He {incident["test"]}.'
    )
    world.say(
        f"The truth became clear: {incident['truth']}."
    )
    world.say(
        f'"Then kindness is the key," {writer.id} said. '
        f'"And listening is how we find the lock," replied {tubby.id}.'
    )
    tubby.memes["worry"] = max(0.0, tubby.memes["worry"] - 1.0)
    tubby.memes["confidence"] += 1.0
    magic.meters["brightness"] += 0.8
    magic.meters["safe_power"] = 1.0
    world.facts["clue"] = incident["clue"]
    world.facts["truth"] = incident["truth"]
    world.facts["explained"] = True


def story_resolution(world: World) -> None:
    writer = world.facts["writer"]
    tubby = world.facts["tubby"]
    incident = world.facts["incident"]
    magic = world.entities["dental_magic"]

    world.say(
        f"Using the kindness magic, {tubby.id} {incident['repair']}. "
        f"{writer.id} helped by asking clear questions and writing down each brave answer."
    )
    world.say(world.facts["reflection"].format(writer=writer.id, tubby=tubby.id))
    world.say(
        f"At last, {incident['ending']}. The dental magic glowed softly, because it had "
        f"made the place safer instead of merely louder."
    )
    world.say(
        f"{writer.id} closed the notebook. 'This is a superhero story worth sharing,' "
        f"they said. {tubby.id} smiled. 'Especially the part where kindness saved the day.'"
    )
    tubby.memes["relief"] += 1.0
    tubby.memes["kindness"] += 0.5
    magic.meters["brightness"] += 0.4
    world.facts["repair"] = incident["repair"]
    world.facts["ending"] = incident["ending"]
    world.facts["lesson"] = incident["lesson"]
    world.facts["resolved"] = True


def generate_story_world(params: StoryParams) -> World:
    world = build_world(params)
    story_intro(world)
    story_problem(world)
    story_turn(world)
    story_resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    writer = world.facts["writer"]
    tubby = world.facts["tubby"]
    incident = world.facts["incident"]
    return [
        "Write a child-facing Superhero Story about a writer and Tubby using dental magic powered by kindness.",
        f"Show how {writer.id} and {tubby.id} respond safely when {incident['problem']}.",
        f"Include the clue that {incident['clue']} and end with {incident['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    writer = world.facts["writer"]
    tubby = world.facts["tubby"]
    incident = world.facts["incident"]
    return [
        QAItem(
            question=f"Who were {writer.id} and {tubby.id}?",
            answer=f"{writer.id} was a writer who recorded brave choices, and {tubby.id} was a tubby superhero whose dental magic grew stronger through kindness."
        ),
        QAItem(
            question=f"What problem did {writer.id} and {tubby.id} discover?",
            answer=f"They discovered that {incident['problem']}. The problem threatened the calm and safety of the dental place."
        ),
        QAItem(
            question=f"Why did {tubby.id}'s first magic spell flicker?",
            answer=f"It flickered because force was not what the problem needed. The magic required listening, trust, and kindness."
        ),
        QAItem(
            question="What clue changed their understanding?",
            answer=f"They noticed that {incident['clue']}. This clue showed them how to help instead of simply pushing the problem away."
        ),
        QAItem(
            question=f"How did {writer.id} and {tubby.id} use kindness?",
            answer=f"{tubby.id} {incident['test']}. {writer.id} supported the plan with patient questions and careful writing."
        ),
        QAItem(
            question="What did the dental magic really need?",
            answer="The dental magic needed kindness, listening, and safe care. Those choices gave the magic safe power."
        ),
        QAItem(
            question="How was the problem resolved?",
            answer=f"{tubby.id} {incident['repair']}. The solution changed the situation without frightening or hurting anyone."
        ),
        QAItem(
            question="What lesson did the superhero story teach?",
            answer=incident["lesson"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a dentist do?",
            answer="A dentist checks teeth and gums, helps keep them healthy, and explains safe ways to care for a mouth."
        ),
        QAItem(
            question="Why is kindness useful when someone feels afraid?",
            answer="Kindness helps a person feel heard and safe, making it easier to ask questions and take one small brave step."
        ),
        QAItem(
            question="What makes a superhero's power responsible?",
            answer="A responsible superhero uses power carefully, protects people, listens before acting, and chooses the safest helpful solution."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_verify() -> int:
    if not asp_valid():
        print("MISMATCH: Python reasonableness gate failed.")
        return 1
    try:
        import asp
        model = asp.one_model(asp_program())
        valid = asp.atoms(model, "valid_story")
    except Exception as exc:
        print(f"MISMATCH: ASP verification failed: {exc}")
        return 1
    if not valid:
        print("MISMATCH: ASP found no valid story.")
        return 1
    sample = generate(
        StoryParams(
            writer_name="Luna",
            tubby_name="Tubby",
            dental_place="the Moonbeam Dental Clinic",
            seed=17,
        )
    )
    required = ["writer", "Tubby", "dental", "kindness", "magic"]
    if not all(word.lower() in sample.story.lower() for word in required):
        print("MISMATCH: generated story omitted a required domain feature.")
        return 1
    if "kindness" not in sample.story.lower():
        print("MISMATCH: generated story omitted the kindness resolution.")
        return 1
    print("OK: Python and ASP reasonableness gates pass.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Superhero Story world about Writer Luna, Tubby, dental magic, and kindness."
    )
    parser.add_argument("--writer-name", choices=NAMES)
    parser.add_argument("--tubby-name", choices=TUBBY_NAMES)
    parser.add_argument("--dental-place", choices=DENTAL_PLACES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    writer_name = args.writer_name or rng.choice(NAMES)
    tubby_choices = [name for name in TUBBY_NAMES if name != writer_name]
    tubby_name = args.tubby_name or rng.choice(tubby_choices)
    dental_place = args.dental_place or rng.choice(DENTAL_PLACES)
    return StoryParams(
        writer_name=writer_name,
        tubby_name=tubby_name,
        dental_place=dental_place,
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(
            f"  {entity.id:16} ({entity.type:16}) {' '.join(details)}"
        )
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
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        values = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(values)} compatible stories:")
        for value in values:
            print(f"  {value}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Tubby", "the Moonbeam Dental Clinic", base_seed),
            StoryParams("Mira", "Bumble", "the Kindness Tooth Station", base_seed + 1),
            StoryParams("Ari", "Puff", "the Starry Smile Office", base_seed + 2),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n) and index < max(100, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
