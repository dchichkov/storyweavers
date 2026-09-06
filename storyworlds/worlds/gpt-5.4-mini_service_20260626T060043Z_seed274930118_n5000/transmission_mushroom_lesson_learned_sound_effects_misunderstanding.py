#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402

THEMES = ("transmission", "mushroom")
SFX = {
    "radio": "bzzzt",
    "walkie": "krrt",
    "door": "tap-tap",
    "leaves": "swish",
    "footsteps": "pat-pat",
    "basket": "clink",
    "flask": "glug",
}
PLACES = {
    "lantern street": {"setting": "the lantern street", "inside": False, "has_radio": True, "has_mushroom": True},
    "brick market": {"setting": "the brick market", "inside": False, "has_radio": True, "has_mushroom": True},
    "quiet station": {"setting": "the quiet station", "inside": True, "has_radio": True, "has_mushroom": False},
    "old garden": {"setting": "the old garden", "inside": False, "has_radio": False, "has_mushroom": True},
}
CHAR_NAMES = ["Nina", "Milo", "Iris", "Pip", "Jasper", "Luna", "Toby", "Mara"]
JOB_TITLES = ["detective", "inspector", "helper", "spotter"]
MOODS = ["careful", "curious", "brave", "patient"]
OBJECTS = {
    "transmission": "a crackly transmission",
    "mushroom": "a spotted mushroom",
    "radio": "a little radio",
}

CASES = (
    {
        "name": "rain gauge relay",
        "opening": "A storm had flooded the community garden, and its tiny weather station had stopped reporting.",
        "message": "cap under mushroom, rain rising",
        "mistake": "thought the transmission warned that a mushroom was trapping rain beneath its cap",
        "clue": "raindrops tapped only one metal cap while the mushroom beside it stayed perfectly still",
        "false_step": "held a basket over the mushroom, but the radio only crackled louder",
        "discovery": "the 'mushroom' was the station's mushroom-shaped rain-gauge cover",
        "action": "cleaned mud from the gauge and clicked its loose battery cap into place",
        "result": "the weather station transmitted the falling water level to every shopkeeper",
        "lesson": "check what a clue names before acting on the first picture in your mind",
        "ending": "Under the clearing sky, silver drops ticked from the gauge while the real mushroom shone beside it.",
        "sounds": ("tap-tap", "click", "bzzzt"),
    },
    {
        "name": "delivery label mix-up",
        "opening": "The market cook was waiting for mushrooms for a soup served after sunset.",
        "message": "mushroom parcel, door three",
        "mistake": "believed the radio was ordering them to pick the mushrooms growing by door three",
        "clue": "a paper label fluttered from an unopened basket whenever the market door went swish",
        "false_step": "reached toward the garden patch, then stopped when a snail peeked from the damp leaves",
        "discovery": "the transmission referred to a delivered parcel, not to the living patch",
        "action": "matched the basket number to the cook's written order and carried it to the kitchen",
        "result": "the cultivated mushrooms arrived safely and the wild ones remained untouched",
        "lesson": "read the whole label before deciding what a short message means",
        "ending": "Soon soup bowls clinked indoors, and the moonlit garden kept every wild mushroom in its place.",
        "sounds": ("swish", "clink", "krrt"),
    },
    {
        "name": "lost puppy beacon",
        "opening": "A small dog named Button slipped its lead during the evening market.",
        "message": "spot by mushroom, bell faint",
        "mistake": "assumed 'spot' described the dots on a mushroom instead of Button's location",
        "clue": "a soft jingle followed by pat-pat paws came from behind the painted mushroom sign",
        "false_step": "counted spots on three mushroom caps and found no hidden note",
        "discovery": "the caller meant the landmark shaped like a mushroom",
        "action": "lowered the radio volume, followed the tiny bell, and opened the sign's side gate",
        "result": "Button trotted out safely and returned to its relieved family",
        "lesson": "one word can have several meanings, so nearby sounds and landmarks matter",
        "ending": "Button curled beneath the mushroom sign as its brass bell gave one sleepy ting.",
        "sounds": ("pat-pat", "ting", "krrt"),
    },
    {
        "name": "library code",
        "opening": "The street library's return box jammed with a borrowed field guide still inside.",
        "message": "turn to mushroom, then forty-two",
        "mistake": "thought someone wanted the mushroom beside the library physically turned around",
        "clue": "the field guide's mushroom chapter had a penciled arrow pointing toward page forty-two",
        "false_step": "gently inspected the mushroom from every side but found no hinge or writing",
        "discovery": "'turn to mushroom' meant turn to the mushroom chapter in the book",
        "action": "opened page forty-two and followed its diagram for releasing the return-box latch",
        "result": "the jammed book slid free without bending a page",
        "lesson": "directions make sense only when you know which object they belong to",
        "ending": "The rescued field guide rested open to a brown mushroom drawing while the return slot clicked shut.",
        "sounds": ("rustle", "click", "bzzzt"),
    },
    {
        "name": "lantern circuit",
        "opening": "Half the lanterns blinked out just as families began walking home.",
        "message": "mushroom ring breaks the line",
        "mistake": "feared that a circle of mushrooms had somehow chewed through the electrical line",
        "clue": "the dark lamps formed a ring around one mushroom-shaped junction cover",
        "false_step": "searched the soil for a broken wire while keeping safely away from the locked electrical box",
        "discovery": "the engineer used 'mushroom ring' as the nickname for that round junction cover",
        "action": "reported its exact number by radio so an adult electrician could reset the protected circuit",
        "result": "the safe walkway lights glowed again without anyone touching exposed equipment",
        "lesson": "ask what a technical nickname means and leave dangerous repairs to trained adults",
        "ending": "Warm lantern circles returned one by one, ending at the little mushroom-shaped cover.",
        "sounds": ("buzz", "click", "krrt"),
    },
    {
        "name": "parade costume signal",
        "opening": "The children's lantern parade paused because its final float could not find the starting lane.",
        "message": "mushroom ready, send the cap",
        "mistake": "expected someone to launch a real mushroom cap through the air",
        "clue": "behind a curtain, cardboard scales scraped and a performer sneezed inside a giant costume",
        "false_step": "looked for a basket small enough to carry a mushroom without bruising it",
        "discovery": "Mushroom was the float's name, and the cap was its enormous painted top",
        "action": "cleared the lane and radioed the costume team to roll forward slowly",
        "result": "the missing float joined the parade in the correct order",
        "lesson": "names and ordinary nouns can sound alike, so context prevents mix-ups",
        "ending": "The painted cap bobbed beneath the lanterns as children called, 'Hooray for the Mushroom float!'",
        "sounds": ("scrape", "achoo", "rumble"),
    },
    {
        "name": "sprinkler whistle",
        "opening": "A thin whistle crossed the garden whenever the watering pipes switched on.",
        "message": "hiss near mushroom, close blue",
        "mistake": "thought the mushroom itself was hissing and should be covered",
        "clue": "the hiss stopped whenever the blue-handled valve turned, although the mushroom did not change",
        "false_step": "listened beneath the mushroom cap and heard only a beetle walking through dry grass",
        "discovery": "a cracked sprinkler beside the mushroom was leaking, and 'blue' meant its valve",
        "action": "marked the leak, asked the gardener to close the blue valve, and fetched a repair washer",
        "result": "water stopped spraying onto the path and reached the seedlings after the repair",
        "lesson": "compare what changes with what stays still before blaming the nearest thing",
        "ending": "At dusk, neat droplets whispered over the seedlings and the mushroom stood in quiet soil.",
        "sounds": ("hiss", "plink", "swish"),
    },
    {
        "name": "music rehearsal cue",
        "opening": "The market musicians lost their place while rehearsing a song for the harvest dance.",
        "message": "after mushroom, drums enter",
        "mistake": "waited for a mushroom to appear before allowing the drummer to play",
        "clue": "the conductor's score showed a tune titled 'Mushroom Morning' just before the drum section",
        "false_step": "searched the vegetable stalls while the musicians repeated the same quiet bars",
        "discovery": "'Mushroom' was the title of a musical passage, not a physical signal",
        "action": "held the radio near the score and counted the final four beats aloud",
        "result": "the drums entered together and the whole tune reached its bright finish",
        "lesson": "a clue may name a song, sign, or place rather than the object itself",
        "ending": "Boom-boom went the final beat, and a paper mushroom on the music stand trembled happily.",
        "sounds": ("hmm-hmm", "boom-boom", "tap"),
    },
    {
        "name": "science fair spores",
        "opening": "A science display began beeping after wind tipped one of its sample cards.",
        "message": "mushroom sample escaped",
        "mistake": "imagined a mushroom had grown legs and run away from the display",
        "clue": "a blank square on the sample board matched a labeled paper envelope under the table",
        "false_step": "followed tiny muddy marks until they proved to be drops from a watering can",
        "discovery": "the escaped sample was a sealed spore-print card blown loose by the wind",
        "action": "put on the provided gloves, returned the sealed card, and clipped the display shut",
        "result": "the alarm stopped and visitors could compare the mushroom print safely",
        "lesson": "funny-sounding reports still deserve careful evidence instead of wild guesses",
        "ending": "The clipped card showed a delicate brown star while the monitor settled into a soft beep.",
        "sounds": ("beep-beep", "flutter", "snick"),
    },
    {
        "name": "bakery button",
        "opening": "The bakery's order board sent a scrambled message while two trays waited at the counter.",
        "message": "press mushroom twice for rolls",
        "mistake": "thought the cook wanted someone to squash a mushroom two times",
        "clue": "the order board had a round brown button painted with a mushroom picture",
        "false_step": "asked why food should be pressed and refused to harm the fresh ingredients",
        "discovery": "the instruction referred to the picture-button for mushroom-filled rolls",
        "action": "confirmed the order number, pressed the picture-button twice, and watched the correct ticket print",
        "result": "each customer received the intended tray without any food being wasted",
        "lesson": "pause when an instruction seems harmful and ask for a clearer explanation",
        "ending": "The printer chirped, two warm trays slid forward, and the picture-button glowed green.",
        "sounds": ("chirp", "tap-tap", "ding"),
    },
    {
        "name": "map shadow",
        "opening": "A visiting family radioed that they could see the clock tower but not the meeting point.",
        "message": "wait where mushroom points at moonrise",
        "mistake": "expected a mushroom to bend like a finger and point across the street",
        "clue": "the tall mushroom sculpture cast a narrow shadow that moved toward a blue map tile",
        "false_step": "checked which way every small garden mushroom leaned and got twelve different answers",
        "discovery": "the message described the sculpture's shadow as a pointer",
        "action": "waited for moonrise, marked the blue tile, and transmitted the landmark back to the family",
        "result": "the visitors followed the clear directions and reached the meeting point",
        "lesson": "time and light can be part of a direction, so observe before rushing",
        "ending": "Four friends met on the blue tile as the sculpture's long shadow touched their shoes.",
        "sounds": ("krrt", "tick-tock", "pat-pat"),
    },
    {
        "name": "rescue channel",
        "opening": "A gardener twisted an ankle near the far end of the market garden and called for help.",
        "message": "channel seven, mushroom shed",
        "mistake": "searched for a seventh row of mushrooms instead of changing the radio channel",
        "clue": "the radio dial showed a glowing seven while a shed roof shaped like a mushroom stood beyond the gate",
        "false_step": "counted six planting rows twice and realized the message could not mean the garden beds",
        "discovery": "seven was the rescue channel, and Mushroom Shed was the landmark's nickname",
        "action": "switched channels, repeated the gardener's exact location, and waited with them for adult helpers",
        "result": "the rescue team found the correct gate and helped the gardener home",
        "lesson": "repeat urgent directions in your own words so misunderstandings are caught early",
        "ending": "The empty stretcher wheels rolled home beneath a safe green radio light and a rising moon.",
        "sounds": ("click", "krrt", "rumble"),
    },
)

OPENINGS = (
    "The first clue arrived before anyone knew there was a mystery.",
    "A familiar place sounded unfamiliar that evening.",
    "Just before closing time, the radio interrupted the ordinary bustle.",
    "The case began with a noise too deliberate to ignore.",
    "A puzzling message turned a simple errand into an investigation.",
    "Nobody was frightened, but everyone needed the message understood quickly.",
    "The mystery started small: one crackle, one odd phrase, and one mushroom.",
    "Under the evening lights, a broken message asked for careful ears.",
)

INVESTIGATION_MOVES = (
    "They repeated the exact words and circled the part they knew for certain.",
    "They separated what they had heard from what they had merely guessed.",
    "They checked the sound, the nearby objects, and the order of events.",
    "They asked what else the puzzling word might name in this place.",
    "They compared the radio message with each visible clue before touching anything.",
    "They took turns listening so one eager guess would not become everyone's answer.",
    "They described the evidence aloud and noticed which detail did not fit their first idea.",
    "They slowed down, replayed the transmission, and tested the safest explanation first.",
)

DIALOGUE_TURNS = (
    ("I have a guess, but it is only a guess", "Good. Now let us find evidence"),
    ("The mushroom must be the answer", "Or mushroom may mean something else here"),
    ("Should we hurry", "We can be quick and still be careful"),
    ("That message sounds impossible", "Then one of its words may have another meaning"),
    ("I heard it clearly", "Hearing words clearly is not the same as understanding them"),
    ("What if our first idea is wrong", "Then the clues will help us replace it"),
    ("The nearest thing looks guilty", "Nearness is not proof"),
    ("Can we ask the sender", "First let us report exactly what we heard"),
)

ASP_RULES = r"""
kind(transmission).
kind(mushroom).
kind(sound_effects).
kind(misunderstanding).
kind(lesson_learned).

feature(transmission) :- kind(transmission).
feature(mushroom) :- kind(mushroom).
feature(sound_effects) :- kind(sound_effects).
feature(misunderstanding) :- kind(misunderstanding).
feature(lesson_learned) :- kind(lesson_learned).

compatible(P, transmission) :- setting(P), radio_ok(P).
compatible(P, mushroom) :- setting(P), mushroom_ok(P).
compatible_story(P) :- compatible(P, transmission), compatible(P, mushroom).

setting("lantern_street").
setting("brick_market").
setting("quiet_station").
setting("old_garden").

radio_ok("lantern_street").
radio_ok("brick_market").
radio_ok("quiet_station").
mushroom_ok("lantern_street").
mushroom_ok("brick_market").
mushroom_ok("old_garden").

#show compatible/2.
#show compatible_story/1.
"""

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    carried_by: Optional[str] = None
    location: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    place: str
    hero: str
    sidekick: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld about a transmission and a mushroom.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_facts() -> str:
    import asp
    lines = []
    for p, meta in PLACES.items():
        lines.append(asp.fact("setting", p.replace(" ", "_")))
        if meta["has_radio"]:
            lines.append(asp.fact("radio_ok", p.replace(" ", "_")))
        if meta["has_mushroom"]:
            lines.append(asp.fact("mushroom_ok", p.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatibilities() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_set = {(p.replace(" ", "_"), "transmission") for p, m in PLACES.items() if m["has_radio"]}
    python_set |= {(p.replace(" ", "_"), "mushroom") for p, m in PLACES.items() if m["has_mushroom"]}
    clingo_set = set(asp_compatibilities())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python reasoning ({len(clingo_set)} facts).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice([p for p in PLACES if PLACES[p]["has_radio"] and PLACES[p]["has_mushroom"]])
    if not (PLACES[place]["has_radio"] and PLACES[place]["has_mushroom"]):
        raise StoryError("This story needs both a radio transmission and a mushroom clue in the same place.")
    hero = rng.choice(CHAR_NAMES)
    sidekick = rng.choice([n for n in CHAR_NAMES if n != hero])
    mood = rng.choice(MOODS)
    return StoryParams(place=place, hero=hero, sidekick=sidekick, mood=mood)


def _sfx(key: str) -> str:
    return SFX[key]


def _story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    identity = "|".join((params.place, params.hero, params.sidekick, params.mood))
    return int.from_bytes(hashlib.blake2b(identity.encode("utf-8"), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    meta = PLACES[params.place]
    story_seed = _story_seed(params)
    rng = random.Random(story_seed)
    case = CASES[story_seed % len(CASES)]
    opening = OPENINGS[(story_seed // len(CASES)) % len(OPENINGS)]
    investigation = INVESTIGATION_MOVES[
        (story_seed // (len(CASES) * len(OPENINGS))) % len(INVESTIGATION_MOVES)
    ]
    dialogue = DIALOGUE_TURNS[
        (story_seed // (len(CASES) * len(OPENINGS) * len(INVESTIGATION_MOVES)))
        % len(DIALOGUE_TURNS)
    ]
    lead_in = rng.choice(
        (
            "They had solved puzzles together before, but neither pretended to know this answer.",
            "They carried a notebook because remembered clues often change shape.",
            "Their rule was to keep living things safe while they investigated.",
            "They knew a clear question could be more useful than a quick answer.",
            "They agreed that the radio's words were evidence, not yet an explanation.",
            "They listened as partners: one tracked sounds while the other watched the scene.",
        )
    )
    reflection = rng.choice(
        (
            "They wrote the corrected meaning beneath their first guess.",
            "They radioed the full explanation back so nobody would repeat the mix-up.",
            "They thanked each other for challenging the first idea kindly.",
            "They added the new meaning to their case notebook.",
            "They practiced saying the message again with clearer words.",
            "They checked that their solution had fixed the cause, not merely hidden the symptom.",
        )
    )
    world = World(place=meta["setting"])
    detective = Entity(id=params.hero, kind="character", label="detective", type="detective", meters={"alert": 1.0}, memes={"curious": 1.0})
    helper = Entity(id=params.sidekick, kind="character", label="helper", type="helper", meters={"alert": 0.5}, memes={"curious": 0.5})
    radio = Entity(id="radio", label=OBJECTS["radio"], type="radio", location=params.place, carried_by=detective.id)
    mushroom = Entity(id="mushroom", label=OBJECTS["mushroom"], type="mushroom", location=params.place)
    world.entities = {e.id: e for e in [detective, helper, radio, mushroom]}

    world.say(opening)
    world.say(f"{detective.id}, a {params.mood} young detective, was exploring {world.place} with {helper.id} when the case began.")
    world.say(lead_in)
    world.say(case["opening"])

    world.para()
    first_sound, second_sound, third_sound = case["sounds"]
    world.say(f"The little radio went '{first_sound} ... {case['message']} ... {second_sound}.' It was a real transmission, but some words had dropped out.")
    world.say(f"A spotted mushroom stood nearby. {helper.id} {case['mistake']}.")
    world.say(f"'{dialogue[0]},' {helper.id} said. '{dialogue[1]},' replied {detective.id}.")
    world.say(f"Their first attempt did not settle the case: {helper.id} {case['false_step']}.")

    world.para()
    world.say(investigation)
    world.say(f"Then they noticed that {case['clue']}.")
    world.say(f"'{third_sound}!' went the next useful sound. The evidence showed that {case['discovery']}.")
    world.say(f"That cleared up the misunderstanding: their first interpretation had confused the mushroom with what the sender actually meant.")

    world.para()
    world.say(f"Working together, {detective.id} and {helper.id} {case['action']}.")
    world.say(f"Because they corrected the meaning before rushing, {case['result']}.")
    world.say(reflection)
    world.say(f"The lesson learned was this: {case['lesson'].capitalize()}.")
    world.say(case["ending"])

    detective.meters["alert"] = 1.5
    helper.meters["alert"] = 1.0
    detective.memes["careful_reasoning"] = 1.0
    helper.memes["careful_reasoning"] = 1.0
    radio.memes["message_understood"] = 1.0
    mushroom.memes["wrongly_blamed"] = 0.0
    world.trace = [
        f"received:{case['message']}",
        f"misunderstood:{case['mistake']}",
        f"observed:{case['clue']}",
        f"discovered:{case['discovery']}",
        f"resolved:{case['result']}",
    ]

    world.facts = {
        "hero": detective,
        "helper": helper,
        "radio": radio,
        "mushroom": mushroom,
        "place": params.place,
        "setting": meta["setting"],
        "case": case["name"],
        "transmission": case["message"],
        "misunderstanding": case["mistake"],
        "clue": case["clue"],
        "discovery": case["discovery"],
        "resolution": case["result"],
        "lesson": case["lesson"],
    }

    prompts = [
        f"Write a child-friendly {case['name']} mystery set in {meta['setting']} that includes a radio transmission and a mushroom clue.",
        f"Tell how {params.hero} and {params.sidekick} test evidence after misunderstanding the words '{case['message']}'.",
        f"Write a gentle detective story with the sound effects '{first_sound}' and '{second_sound}', a corrected misunderstanding, and a lesson learned.",
    ]

    story_qa = [
        QAItem(
            question=f"What message did {params.hero} and {params.sidekick} receive?",
            answer=f"They received the transmission '{case['message']}.' Missing words made it easy to misunderstand at first.",
        ),
        QAItem(
            question=f"What did {params.sidekick} misunderstand about the mushroom?",
            answer=f"{params.sidekick} {case['mistake']}. That was a guess rather than a fact supported by the scene.",
        ),
        QAItem(
            question="Which clue changed the detectives' minds?",
            answer=f"They noticed that {case['clue']}. That evidence led them away from their first interpretation.",
        ),
        QAItem(
            question=f"How did the {case['name']} case end?",
            answer=f"{params.hero} and {params.sidekick} {case['action']}. As a result, {case['result']}.",
        ),
        QAItem(
            question="What lesson did the detectives learn?",
            answer=f"They learned this: {case['lesson'].capitalize()}. Their corrected explanation solved the real problem.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a transmission?",
            answer="A transmission is a message sent through a radio or another signal so someone can hear it somewhere else.",
        ),
        QAItem(
            question="What is a mushroom?",
            answer="A mushroom is a kind of fungus that can grow in soil, near trees, or beside damp places.",
        ),
        QAItem(
            question="Why do detectives listen carefully?",
            answer="Detectives listen carefully because small sounds can carry important clues.",
        ),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            bits = []
            if e.label:
                bits.append(f"label={e.label}")
            if e.location:
                bits.append(f"location={e.location}")
            if e.carried_by:
                bits.append(f"carried_by={e.carried_by}")
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            print(f"  {e.id}: {e.kind} {(' '.join(bits))}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
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


CURATED = [
    StoryParams(place="lantern street", hero="Nina", sidekick="Milo", mood="curious"),
    StoryParams(place="brick market", hero="Iris", sidekick="Toby", mood="careful"),
    StoryParams(place="lantern street", hero="Mara", sidekick="Pip", mood="patient"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp.one_model(asp_program("#show compatible/2.\n#show compatible_story/1."))
        print(asp.atoms(models, "compatible"))
        print(asp.atoms(models, "compatible_story"))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < args.n * 20:
            i += 1
            params = resolve_params(args, random.Random((args.seed or 0) + i))
            params.seed = (args.seed or 0) + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
