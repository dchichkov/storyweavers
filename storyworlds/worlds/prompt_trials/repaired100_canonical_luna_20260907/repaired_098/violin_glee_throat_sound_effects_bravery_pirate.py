#!/usr/bin/env python3
"""A child-facing pirate tale about a violin, glee, a sore throat, and bravery."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
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
class Creature:
    name: str
    species: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Trouble:
    clue: str
    cause: str
    solved: bool = False


@dataclass
class StoryParams:
    seed: Optional[int] = None
    ship_name: str = "the Giggling Gull"
    sailor_name: str = "Luna"
    sailor_species: str = "cat"
    captain_name: str = "Captain Brine"
    captain_species: str = "parrot"
    trouble: str = "a scratchy throat"
    case: str = "scratchy_throat"
    route: str = "deck_first"


@dataclass(frozen=True)
class PirateCase:
    worry: str
    first_test: str
    failed_reason: str
    clue: str
    cause: str
    brave_action: str
    repair: str
    lesson: str
    ending: str


@dataclass
class World:
    ship: Place
    sailor: Creature
    captain: Creature
    violin: dict
    trouble: Trouble
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SHIPS = {
    "the Giggling Gull": Place("the Giggling Gull", "pirate ship"),
    "the Moonlit Minnow": Place("the Moonlit Minnow", "pirate ship"),
    "the Jolly Teapot": Place("the Jolly Teapot", "pirate ship"),
}

SAILORS = [
    ("Luna", "cat"),
    ("Mira", "mouse"),
    ("Toby", "otter"),
    ("Pip", "penguin"),
]

CAPTAINS = [
    ("Captain Brine", "parrot"),
    ("Captain Coral", "seal"),
    ("Captain Pebble", "turtle"),
]

CASES = {
    "scratchy_throat": PirateCase(
        "Luna's throat felt scratchy before the crew's music hour",
        "Luna played one soft violin note and listened to her breath",
        "the note was rough, but it did not show whether dust, cold air, or worry was responsible",
        "a puff of cinnamon-colored powder rose from the violin's open case",
        "a spilled spice sack had dusted the case and made the throat tickle when the lid moved",
        "told the cheerful crew she needed a pause instead of forcing a song",
        "Captain Brine moved the spice sack, washed the case cloth, offered warm honey water, and let Luna rest her voice",
        "bravery means telling the truth about your body before a small trouble grows",
        "the clean violin sang a warm note while Luna smiled silently beside her relieved crew",
    ),
    "fog_whistle": PirateCase(
        "the fog whistle made Luna's throat sting",
        "asked Captain Brine to sound the whistle from far across the deck while Luna stayed by the mast",
        "the sting still came when the whistle was silent, so the loud sound was not the whole cause",
        "a wet rope had rubbed salt crystals onto the whistle's mouthpiece",
        "the rough salt dust had irritated Luna's throat whenever she tested the whistle",
        "admitted she was afraid to disappoint the crew and asked someone else to lead the signal",
        "rinsed and dried the mouthpiece, replaced the frayed rope, and gave Luna warm tea",
        "bravery can mean asking for a safer role while a tool is being fixed",
        "the fog cleared as the clean whistle gave one gentle toot and Luna played no louder than comfort allowed",
    ),
    "singing_shell": PirateCase(
        "a singing shell made Luna cough",
        "held the shell away and compared its sound with a quiet violin string",
        "the cough followed the shell but not the violin, narrowing the search",
        "a crumb of dry biscuit rattled inside the shell",
        "the biscuit crumb had been trapped during the crew's snack and tickled Luna's throat",
        "spoke up even though everyone loved the shell's funny voice",
        "shook out the crumb over a bowl, cleaned the shell, and checked Luna's breathing with Captain Brine",
        "a brave warning can protect joy instead of spoiling it",
        "the shell whispered cleanly while Luna's violin answered with a bright, comfortable tune",
    ),
    "storm_chant": PirateCase(
        "Luna could not join the storm chant",
        "watched the crew chant quietly while she marked each breath with a finger",
        "her throat became rough after every attempted verse, even at a gentle volume",
        "cold spray had soaked the scarf around her neck",
        "the wet scarf had chilled her throat during the windy watch",
        "raised a hand and asked the crew to change the song rather than hiding her discomfort",
        "dried the scarf, wrapped Luna in a warm shawl, and changed the chant into a soft drum rhythm",
        "being brave can change a plan so everyone can take part safely",
        "the crew tapped a merry rhythm while Luna's violin carried the final sunny melody",
    ),
    "parrot_echo": PirateCase(
        "a parrot echo made Luna think her violin was broken",
        "played an open string while Captain Brine listened from three spots on deck",
        "the same rough echo appeared only beside the brass bell",
        "a loose bell rope trembled against the violin case",
        "the rope's rattle mixed with the violin sound and made it seem harsh",
        "said she needed help instead of blaming her own playing",
        "tied back the rope, padded the case, and retested the violin in the quiet cabin",
        "asking for another set of ears is a brave way to solve a confusing sound",
        "the violin's clear note sailed through the cabin while the bell rope rested quietly",
    ),
    "pepper_deck": PirateCase(
        "peppery dust made Luna's throat tickle on deck",
        "covered her mouth with a clean cloth and traced the dust back without rubbing it",
        "the dust stopped at the galley door, so it was not coming from the sea breeze",
        "a pepper pot had tipped inside a crate of cooking spoons",
        "the tipped pot had sent pepper across the deck whenever the ship rocked",
        "warned the cook before anyone swept the dust into the air",
        "closed the pot, carried the crate below, and cleaned the deck with a damp mop",
        "bravery includes stopping a risky shortcut before it hurts someone",
        "the deck shone clean, and Luna played a gentle violin jig for the grateful cook",
    ),
}

TROUBLES = [
    ("a scratchy throat", "a spilled spice sack had dusted the violin case", "scratchy_throat"),
    ("a stinging fog whistle", "salt crystals had roughened its mouthpiece", "fog_whistle"),
    ("a coughing singing shell", "a biscuit crumb was trapped inside it", "singing_shell"),
    ("a missing storm chant", "cold spray had soaked Luna's scarf", "storm_chant"),
    ("a harsh violin echo", "a loose bell rope was rattling against the case", "parrot_echo"),
    ("peppery deck dust", "a tipped pepper pot was shaking in a galley crate", "pepper_deck"),
]

ROUTES = (
    "deck_first",
    "dialogue_first",
    "map_first",
    "storm_memory",
    "two_theories",
    "quiet_first",
    "captain_first",
    "question_first",
)


ASP_RULES = r"""
brave(S) :- sailor(S), names_discomfort(S), chooses_safe_action(S).
solved(T) :- trouble(T), cause(T, _).
valid_story(T) :- sailor(sailor), brave(sailor), solved(T).
"""


def trouble_id(text: str) -> str:
    return "trouble_" + "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("sailor", "sailor"),
        asp.fact("names_discomfort", "sailor"),
        asp.fact("chooses_safe_action", "sailor"),
    ]
    for clue, cause, _ in TROUBLES:
        tid = trouble_id(clue)
        lines.extend((asp.fact("trouble", tid), asp.fact("cause", tid, cause)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/1."))
    got = set(asp.atoms(model, "solved"))
    expected = {(trouble_id(clue),) for clue, _, _ in TROUBLES}
    if got == expected:
        print(f"OK: clingo gate matches python reasoning ({len(expected)} troubles).")
        return 0
    print("MISMATCH between clingo and python reasoning.")
    print("clingo:", sorted(got))
    print("python:", sorted(expected))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(value) for value in (
        params.seed, params.ship_name, params.sailor_name, params.sailor_species,
        params.captain_name, params.captain_species, params.case, params.route,
    ))
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if params.ship_name not in SHIPS:
        raise StoryError(f"Unknown ship: {params.ship_name}")
    if params.case not in CASES:
        raise StoryError(f"Unknown pirate case: {params.case}")
    template = SHIPS[params.ship_name]
    case = CASES[params.case]
    return World(
        ship=Place(template.name, template.kind),
        sailor=Creature(params.sailor_name, params.sailor_species, "violin player"),
        captain=Creature(params.captain_name, params.captain_species, "captain"),
        violin={"name": "a small wooden violin", "meters": {"strings": 4}, "memes": {"glee": 0}},
        trouble=Trouble(params.trouble, case.cause),
    )


def tell_story(world: World, params: StoryParams) -> None:
    sailor = world.sailor
    captain = world.captain
    ship = world.ship
    case = CASES[params.case]
    rng = story_rng(params)

    sailor.memes.update(glee=1, bravery=0, worry=1)
    captain.memes.update(patience=1, care=1)

    openings = {
        "deck_first": f"On the bright deck of {ship.name}, {sailor.name} tuned a small wooden violin while the crew prepared for music hour. Then {case.worry.capitalize()}.",
        "dialogue_first": f'"I want to play with glee," {sailor.name} told the crew on {ship.name}, "but {case.worry}."',
        "map_first": f"On the ship's map, {sailor.name} marked the galley, the mast, and the music rug. Beside the map lay a violin, and {case.worry}.",
        "storm_memory": f"After the sea grew calm, {sailor.name} remembered the moment music hour changed on {ship.name}: {case.worry}.",
        "two_theories": f"Two guesses sailed around {ship.name}. Perhaps the violin was wrong, or perhaps the air held a hidden trick. The truth began when {case.worry}.",
        "quiet_first": f"The pirate crew grew quiet beside the mast. {case.worry.capitalize()} While the others waited, {sailor.name} held the violin carefully.",
        "captain_first": f"{captain.name}, the ship's {captain.species} captain, noticed that {case.worry}. The captain called for {sailor.name} and the violin.",
        "question_first": f'"Why does my throat feel this way when music time begins?" asked {sailor.name} on {ship.name}. The violin rested across their knees.',
    }
    world.say(openings[params.route])
    world.say(rng.choice([
        f"It mattered because {case.worry}, and the crew wanted music that brought glee without causing harm.",
        f"The crew loved cheerful sound, but they also knew that {case.worry}.",
        f"Even a pirate ship needs a careful plan when {case.worry}.",
    ]))
    world.say(rng.choice([
        f'"A brave sailor tells the truth about a body," {captain.name} said. "Glee should never require pain."',
        f'"We can solve this like a calm crew," said {captain.name}. "{sailor.name}, tell me what you notice."',
        f'{captain.name} lowered the ship map. "No teasing, no rushing. We will listen first."',
    ]))

    world.para()
    world.say(f"First, {sailor.name} {case.first_test}.")
    world.say(rng.choice([
        f"The first test was not enough because {case.failed_reason}.",
        f"It gave one useful hint, but {case.failed_reason}.",
        f'"That did not explain everything," {sailor.name} admitted. {case.failed_reason.capitalize()}.',
    ]))
    world.say(rng.choice([
        f"Then the crew found the important clue: {case.clue}.",
        f"Captain {captain.name} pointed to the small clue. {case.clue.capitalize()}.",
        f"Careful listening changed the mystery. They noticed that {case.clue}.",
    ]))
    world.say(f"Now the sounds made sense. {case.cause.capitalize()}.")

    world.para()
    world.say(rng.choice([
        f"{sailor.name} felt nervous but {case.brave_action}.",
        f'"I am worried, but I can choose a safe next step," {sailor.name} said, then {case.brave_action}.',
        f"That was the brave turn: {sailor.name} {case.brave_action}.",
    ]))
    sailor.memes["bravery"] = 1
    sailor.meters["safe_checks"] = 2
    world.say(rng.choice([
        f"Together, they {case.repair}.",
        f"{captain.name} guided the crew, and they {case.repair}.",
        f"The repair matched the evidence: they {case.repair}.",
    ]))
    world.trouble.solved = True
    world.violin["memes"]["glee"] = 1
    world.ship.meters["crew_safety"] = 1

    world.para()
    world.say(rng.choice([
        f"{sailor.name} learned that {case.lesson}.",
        f'"What did courage help you do?" asked {captain.name}. {sailor.name} answered, "{case.lesson.capitalize()}."',
        f"The captain wrote one rule in the ship log: {case.lesson}.",
    ]))
    world.say(rng.choice([
        f"At sunset, {case.ending}.",
        f"When the sea turned gold, {case.ending}.",
        f"The happy change was easy to hear: {case.ending}.",
    ]))
    world.facts.update(
        sailor=sailor,
        captain=captain,
        ship=ship,
        violin=world.violin,
        trouble=world.trouble,
        case=case,
        cause=case.cause,
        repair=case.repair,
        lesson=case.lesson,
        ending=case.ending,
        solved=True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case = f["case"]
    return [
        f"Write a child-facing pirate tale about {f['sailor'].name}, a violin, glee, and a throat problem on {f['ship'].name}.",
        f"Show how the pirate crew discovers that {case.cause}. Include sound effects and a brave safe choice.",
        f"End with this changed image: {case.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case = f["case"]
    sailor = f["sailor"]
    captain = f["captain"]
    return [
        QAItem(
            question=f"What trouble did {sailor.name} notice before playing the violin?",
            answer=f"{sailor.name} noticed that {f['trouble'].clue}. It mattered because {case.worry}.",
        ),
        QAItem(
            question="What clue revealed the real cause?",
            answer=f"The important clue was that {case.clue}. This showed that {case.cause}.",
        ),
        QAItem(
            question=f"How did {sailor.name} show bravery?",
            answer=f"{sailor.name} {case.brave_action}. That was brave because it protected their throat instead of hiding the problem.",
        ),
        QAItem(
            question=f"How did {captain.name} and the crew help?",
            answer=f"They {case.repair}. They made room for safe music and let {sailor.name} recover.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer=f"{case.ending}. The crew could enjoy glee without ignoring a warning from the body.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a violin?",
            answer="A violin is a small string instrument played with a bow or with the fingers.",
        ),
        QAItem(
            question="Why can sound effects help a pirate tale?",
            answer="Sound effects such as a creak, splash, or soft toot help readers imagine what is happening on the ship.",
        ),
        QAItem(
            question="What does glee mean?",
            answer="Glee means bright, excited happiness.",
        ),
        QAItem(
            question="Why should someone speak up about throat pain?",
            answer="Speaking up helps others choose a safer activity and prevents a small discomfort from becoming worse.",
        ),
        QAItem(
            question="What is bravery in this story?",
            answer="Bravery is telling the truth about a worry and choosing a careful action, even when a person wants to keep having fun.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale about a violin, glee, throat care, and bravery.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--ship", choices=sorted(SHIPS))
    ap.add_argument("--sailor-name")
    ap.add_argument("--captain-name")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    ship_name = args.ship or rng.choice(sorted(SHIPS))
    sailor_name, sailor_species = rng.choice(SAILORS)
    captain_name, captain_species = rng.choice(CAPTAINS)
    trouble, _, case = rng.choice(TROUBLES)
    return StoryParams(
        seed=args.seed,
        ship_name=ship_name,
        sailor_name=args.sailor_name or sailor_name,
        sailor_species=sailor_species,
        captain_name=args.captain_name or captain_name,
        captain_species=captain_species,
        trouble=trouble,
        case=case,
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in (world.ship, world.sailor, world.captain):
        lines.append(
            f"{entity.name}: meters={entity.meters} "
            f"memes={getattr(entity, 'memes', {})}"
        )
    lines.append(
        f"violin: {world.violin!r}; "
        f"trouble={world.trouble.clue!r}; solved={world.trouble.solved}; "
        f"cause={world.facts['cause']!r}"
    )
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/1."))
        print(sorted(set(asp.atoms(model, "solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 3 if args.all else args.n
    samples: list[StorySample] = []
    for i in range(count):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
