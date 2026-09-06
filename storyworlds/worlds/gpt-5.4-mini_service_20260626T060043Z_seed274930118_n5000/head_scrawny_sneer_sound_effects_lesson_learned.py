#!/usr/bin/env python3
"""Varied woodland fables about a hurtful label, a sneer, and learning better."""

from __future__ import annotations

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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hare", "rabbit", "fox", "squirrel", "badger"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class Meadow:
    place: str = "the meadow"
    has_patch: bool = True
    has_stream: bool = True


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Pip"
    rival: str = "Grub"
    helper: str = "Moss"
    place: str = "meadow"
    incident: int = 0
    opening: int = 0
    reflection: int = 0
    apology: int = 0
    cadence: int = 0
    label_context: int = 0


NAMES = ["Pip", "Tilly", "Nip", "Wren", "Birch", "Pipkin"]
RIVALS = ["Grub", "Bram", "Muck", "Thorn"]
HELPERS = ["Moss", "Fern", "Sage", "Willow"]


INCIDENTS = [
    {
        "title": "the bell-rope puzzle",
        "premise": "The berry-patch bell had to ring before fog hid the safe trail.",
        "dismissal": "That knot plan will never hold",
        "problem": "A gust snapped the high bell rope, leaving its loose end beyond every paw.",
        "mistake": "Grub stacked slick stones, but clack-clack! they slid apart.",
        "clue": "Pip noticed that three low vine loops could share the pull without breaking.",
        "action": "Pip sketched the loops in mud while Moss tied and tested each one: tug, tug, TING!",
        "result": "The bell guided two lost fawns through the fog before dusk.",
        "lesson": "A careful plan can reach where a tall reach cannot.",
        "ending": "Three neat vine loops swayed beneath the shining bell.",
        "object": "bell rope",
    },
    {
        "title": "the hollow-log crossing",
        "premise": "Rain cut a silver stream across the path to the seed pantry.",
        "dismissal": "A little map cannot move a log",
        "problem": "The old crossing rolled whenever anyone stepped onto it.",
        "mistake": "Grub shoved from the bank. Bump! Splash! The log spun back.",
        "clue": "Pip saw wedge-shaped stones tucked beneath a nearby tree root.",
        "action": "Pip directed Moss to brace both ends while everyone pushed together: heave-ho, thunk!",
        "result": "The log stayed still, and the neighbors carried dry seed home.",
        "lesson": "Observation and teamwork can steady a difficult problem.",
        "ending": "At sunset, tiny pawprints crossed the firm log in one straight line.",
        "object": "hollow log",
    },
    {
        "title": "the runaway cart",
        "premise": "A nut cart waited on the hill above the harvest tables.",
        "dismissal": "Your twig brake is just a silly idea",
        "problem": "Its wheel pin popped free, and the loaded cart began to roll.",
        "mistake": "Grub grabbed the handle, but rattle-rattle! it pulled him downhill.",
        "clue": "Pip remembered how a forked branch had stopped an acorn on a slope.",
        "action": "Pip called a warning, slid the branch ahead of the wheel, and Moss cleared the path: skrrt, clunk!",
        "result": "The cart stopped before the crowded tables, and no one was hurt.",
        "lesson": "Quick thinking matters more than looking powerful.",
        "ending": "The rescued nuts filled twelve bowls beneath bright paper flags.",
        "object": "nut cart",
    },
    {
        "title": "the owl's mixed-up message",
        "premise": "An owl's warning arrived as wind scattered its leaf letters.",
        "dismissal": "No one needs your fussy sorting game",
        "problem": "The mixed leaves seemed to send everyone toward the flooded path.",
        "mistake": "Grub guessed the message and shouted the wrong direction: hoo-whoosh!",
        "clue": "Pip matched the torn leaf edges and found a drawing of the safe ridge.",
        "action": "Pip arranged the pieces head-to-tail while Moss pinned them with pebbles: tap, tap, tap.",
        "result": "The picnic group followed the ridge and avoided the deep water.",
        "lesson": "Patient reading is wiser than a confident guess.",
        "ending": "The mended leaf message rested under four smooth blue pebbles.",
        "object": "leaf message",
    },
    {
        "title": "the echo in the burrow",
        "premise": "A mysterious boom kept shaking dust from the nursery burrow.",
        "dismissal": "Your listening stops are wasting time",
        "problem": "The animals feared that the ceiling was cracking.",
        "mistake": "Grub charged inside to hunt a monster. Boom-boom! came the answer.",
        "clue": "Pip heard each boom follow a loose shutter striking a hollow root.",
        "action": "Pip marked the rhythm, and Moss padded the shutter while Grub held it steady: pat, knot, hush.",
        "result": "The frightening boom ended, and the sleeping kits woke to quiet.",
        "lesson": "Listening for a cause can make fear manageable.",
        "ending": "One dandelion seed floated through the peaceful burrow doorway.",
        "object": "loose shutter",
    },
    {
        "title": "the cracked water channel",
        "premise": "The garden beds drooped during a hot afternoon.",
        "dismissal": "Those tiny channels cannot help a whole garden",
        "problem": "Water burst from one cracked bank and pooled far from the roots.",
        "mistake": "Grub blocked it with one heavy rock. Glug-glug! water escaped around both sides.",
        "clue": "Pip traced several narrow grooves that could divide the flow gently.",
        "action": "Pip shaped the branching paths while Moss pressed clay along their rims: squish, trickle, sip.",
        "result": "Every row received water, including the smallest mint shoots.",
        "lesson": "Sharing a task into small parts can solve a large need.",
        "ending": "Silver threads of water gleamed between upright green leaves.",
        "object": "water channel",
    },
    {
        "title": "the trapped moon moth",
        "premise": "Festival lanterns were being hung along the hawthorn hedge.",
        "dismissal": "Your slow rescue idea will spoil the parade",
        "problem": "A moon moth fluttered inside a lantern without finding the narrow opening.",
        "mistake": "Grub shook the lantern. Whap-whap! The frightened moth beat its wings faster.",
        "clue": "Pip saw that dimming the other lights would make the open flap brightest.",
        "action": "Pip asked everyone to cover their lamps while Moss opened the flap: click, hush, ffffft.",
        "result": "The moth followed the moonlight out with every wing unharmed.",
        "lesson": "Gentleness can solve what force makes worse.",
        "ending": "The moon moth circled once above a row of softly glowing lanterns.",
        "object": "festival lantern",
    },
    {
        "title": "the missing drumbeat",
        "premise": "The woodland band rehearsed for the first spring dance.",
        "dismissal": "That quiet head-count will not find our beat",
        "problem": "Their rhythm kept stumbling whenever the bridge began.",
        "mistake": "Grub played louder to cover the gap: BOOM, BOOM, muddle-boom!",
        "clue": "Pip noticed that the woodpecker could not see Moss's starting signal.",
        "action": "Pip moved the signal flag above the fern and counted everyone in: one-two, rat-a-tat!",
        "result": "Every player entered together, and the dancers found the rhythm.",
        "lesson": "A team succeeds when everyone can receive the signal.",
        "ending": "Red and yellow ribbons bounced above the final drumbeat.",
        "object": "signal flag",
    },
    {
        "title": "the leaning nest shelf",
        "premise": "A family of wrens needed a dry shelf before the next rain.",
        "dismissal": "Your measuring marks are much too small to matter",
        "problem": "The new shelf tilted, sending every twig toward its edge.",
        "mistake": "Grub hammered the top corner. Bang! The other corner lifted higher.",
        "clue": "Pip compared the legs and found one resting in a hidden mole track.",
        "action": "Pip guided Moss to fill the track and tested the shelf with round berries: roll, stop, still.",
        "result": "The shelf held level through the evening shower.",
        "lesson": "Measure the cause before striking at the symptom.",
        "ending": "Four dry nest twigs lay still beside a sleeping wren.",
        "object": "nest shelf",
    },
    {
        "title": "the firefly count",
        "premise": "Young fireflies gathered for their first flight over the meadow.",
        "dismissal": "Your careful count is holding everyone back",
        "problem": "One light kept disappearing whenever the group crossed the brambles.",
        "mistake": "Grub ordered a faster flight. Zip-zap! The lights scattered farther apart.",
        "clue": "Pip spotted a tired firefly resting beneath each third leaf.",
        "action": "Pip arranged short rest stops while Moss called the count: blink, blink, twelve!",
        "result": "The whole group crossed together without leaving anyone behind.",
        "lesson": "Moving at a pace that includes everyone makes a group stronger.",
        "ending": "Twelve green lights formed a slow, complete circle over the grass.",
        "object": "firefly route",
    },
    {
        "title": "the seed-library mix-up",
        "premise": "Wind toppled the labeled jars in the woodland seed library.",
        "dismissal": "Your seed-by-seed method will take forever",
        "problem": "Round radish seeds and flat hollyhock seeds covered the same rug.",
        "mistake": "Grub swept them into one scoop: scritch-scratch, all mixed again.",
        "clue": "Pip found that a grooved bark tray rolled round seeds but held flat ones.",
        "action": "Pip tilted the tray while Moss caught each group in a clean cup: tick-tick, rustle.",
        "result": "The librarian relabeled every jar before planting day.",
        "lesson": "A thoughtful tool can turn slow work into careful work.",
        "ending": "Two tidy rows of jars shone on the repaired library shelf.",
        "object": "seed jars",
    },
    {
        "title": "the frost-warning flags",
        "premise": "Cold air slipped down the hill toward the new orchard blossoms.",
        "dismissal": "Those fluttering scraps prove nothing",
        "problem": "No one agreed which garden beds would freeze first.",
        "mistake": "Grub covered only the tallest tree. Flap-flap! Its blanket blew loose.",
        "clue": "Pip's ribbon flags showed the cold breeze pooling beside the lowest beds.",
        "action": "Pip mapped the airflow while Moss fastened shared covers from low ground upward: tuck, clip, snug.",
        "result": "The blossoms survived, and even Grub's tree received a secure cover.",
        "lesson": "Evidence deserves respect, no matter who notices it.",
        "ending": "At dawn, pink blossoms opened above twelve frost-silvered flags.",
        "object": "warning flags",
    },
]

OPENINGS = [
    "Near {place}, {name} the hare loved noticing details that busier animals missed.",
    "At {place}, {name} arrived with a notebook, bright eyes, and a question for everything.",
    "The morning began quietly at {place}, where {name} was already studying the day's work.",
    "Everyone hurried through {place}, except {name}, who paused to look and listen.",
    "A new task brought {name}, {rival}, and {helper} together at {place}.",
    "Before breakfast at {place}, {name} had drawn three possible plans in the dust.",
    "Clouds crossed {place} as {name} checked what the woodland neighbors might need.",
    "At the edge of {place}, {name} heard trouble before anyone could see it.",
]

REFLECTIONS = [
    "The sneer stung, but {name} took one breath and looked at the problem again.",
    "For a moment {name}'s ears drooped. Then {helper} whispered, 'Your idea deserves a fair test.'",
    "{name} nearly stepped aside, then thought, 'A mean expression is not evidence.'",
    "{helper} stood beside {name}. 'Let's check the clues before we decide,' the friend said.",
    "Instead of answering the sneer with another sneer, {name} asked everyone to watch closely.",
    "{name} felt hurt, yet chose to explain the plan one clear step at a time.",
    "The unkind look made the clearing quiet. {name} broke the silence by pointing to the first clue.",
    "{name} remembered that bodies come in many shapes and focused on what careful thinking could do.",
]

APOLOGIES = [
    "{rival}'s sneer vanished. 'I judged your idea before I understood it. I'm sorry,' the badger said.",
    "{rival} lowered the head that had worn the sneer. 'You deserved listening, not mockery.'",
    "'That look was unkind,' {rival} admitted. 'Next time I will test the plan before dismissing it.'",
    "{rival} faced {name}. 'I used a sneer instead of a reason. May I help finish the work?'",
]

CADENCES = [
    "First came the clue, then the test, and only then the answer.",
    "No one cheered yet; they checked the repair twice before trusting it.",
    "The clearing held its breath while the small plan met the large problem.",
    "One neighbor watched, one worked, and one called out what changed.",
    "The answer arrived in steps instead of in one grand leap.",
    "Their first try taught them what the second try needed.",
    "Careful eyes found the cause that hurried paws had missed.",
    "When every helper understood a job, the plan began to work.",
]

LABEL_CONTEXTS = [
    "A word card nearby read 'scrawny.' The friends crossed it out because body labels can hurt and reveal nothing about someone's worth.",
    "Their lesson board named 'scrawny' as a word not to use for a person or animal; appearance is not a fair measure of ability.",
    "An old book used 'scrawny' to mock someone's body. The friends marked the passage unkind and chose respectful words instead.",
    "Before starting, the group discussed the word 'scrawny.' They agreed that judging a body shape cannot tell them who has a good idea.",
    "A torn poster praised strength by insulting a 'scrawny' body. The friends took it down because no body deserves ridicule.",
    "Someone had chalked 'scrawny means weak' on a stump. The friends erased it; shape and size do not decide courage or skill.",
    "The day's vocabulary list included 'scrawny,' but the teacher explained that it is a hurtful body label, not a useful fact about anyone.",
    "A storybook villain used the word 'scrawny' as an insult. The friends paused to say that no person or animal should be reduced to a body label.",
]


ASP_RULES = r"""
#show lesson/1.
#show sneer/2.

lesson(L) :- learned(L).
sneer(R, H) :- proud(R), scorns(R, H).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("proud", "badger"),
            asp.fact("scorns", "badger", "hare"),
            asp.fact("learned", "kindness_is_stronger_than_mockery"),
            asp.fact("learned", "small_can_still_be_brave"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable storyworld: scrawny, sneer, and a lesson learned.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--rival", choices=RIVALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--place", default="meadow")
    ap.add_argument("--incident", type=int, choices=range(len(INCIDENTS)))
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
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(NAMES),
        rival=args.rival or rng.choice(RIVALS),
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or "meadow",
        incident=args.incident if args.incident is not None else rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        reflection=rng.randrange(len(REFLECTIONS)),
        apology=rng.randrange(len(APOLOGIES)),
        cadence=rng.randrange(len(CADENCES)),
        label_context=rng.randrange(len(LABEL_CONTEXTS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = World()
    meadow = Meadow(place=f"the {params.place}")
    world.facts["meadow"] = meadow

    hare = world.add(Entity(id=params.name, kind="character", type="hare", label=params.name))
    badger = world.add(Entity(id=params.rival, kind="character", type="badger", label=params.rival))
    helper = world.add(Entity(id=params.helper, kind="character", type="mouse", label=params.helper))

    hare.meters["scrawny"] = 1.0
    hare.memes["hope"] = 1.0
    badger.memes["pride"] = 1.0
    incident = INCIDENTS[params.incident % len(INCIDENTS)]

    def personalize(text: str) -> str:
        return text.replace("Pip", hare.id).replace("Grub", badger.id).replace("Moss", helper.id)

    common = {
        "place": meadow.place,
        "name": hare.id,
        "rival": badger.id,
        "helper": helper.id,
    }
    world.say(OPENINGS[params.opening % len(OPENINGS)].format(**common))
    world.say(personalize(incident["premise"]))
    world.say(LABEL_CONTEXTS[params.label_context % len(LABEL_CONTEXTS)])
    world.say(personalize(incident["problem"]))
    world.say(
        f"{badger.id} wore a sneer and said, '{incident['dismissal']}.' The sneer mocked the plan, "
        f"not {hare.id}'s head or body, but it was still unkind."
    )
    world.say(REFLECTIONS[params.reflection % len(REFLECTIONS)].format(**common))
    world.say(personalize(incident["mistake"]))
    world.say(personalize(incident["clue"]))
    world.say(CADENCES[params.cadence % len(CADENCES)])
    world.say(personalize(incident["action"]))
    world.say(personalize(incident["result"]))
    hare.memes["bravery"] = 1.0
    badger.memes["shame"] = 1.0
    badger.memes["sneer"] = 0.0
    world.say(APOLOGIES[params.apology % len(APOLOGIES)].format(**common))
    world.say(f"Lesson learned: {incident['lesson']}")
    world.say(personalize(incident["ending"]))

    world.facts.update(
        hare=hare,
        badger=badger,
        helper=helper,
        meadow=meadow,
        incident=incident,
        lesson=incident["lesson"],
        sneer=True,
        apology=True,
        solved_object=incident["object"],
        sound_effects=True,
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
    f = world.facts
    hare = f["hare"]
    badger = f["badger"]
    incident = f["incident"]
    return [
        f"Write a short fable about {hare.id}, a hare who solves {incident['title']} after an unkind sneer.",
        f"Tell a child-friendly story where {badger.id} dismisses an idea, then learns to respect evidence.",
        f"Write a woodland fable with sound effects, a lesson learned, and a final image involving {incident['object']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hare = f["hare"]
    badger = f["badger"]
    helper = f["helper"]
    incident = f["incident"]

    def personalize(text: str) -> str:
        return text.replace("Pip", hare.id).replace("Grub", badger.id).replace("Moss", helper.id)

    return [
        QAItem(
            question="How did the story handle the word scrawny?",
            answer=(
                "The friends discussed scrawny as a hurtful body label and did not apply it to anyone. "
                "They understood that body shape does not determine health, skill, courage, or worth."
            ),
        ),
        QAItem(
            question=f"What idea did {badger.id} dismiss with a sneer?",
            answer=f"{badger.id} dismissed the plan for {incident['title']}. The sneer targeted the idea, but it was still unkind.",
        ),
        QAItem(
            question=f"What clue helped solve {incident['title']}?",
            answer=personalize(incident["clue"]),
        ),
        QAItem(
            question=f"How did {hare.id} and {helper.id} solve the problem?",
            answer=personalize(incident["action"]),
        ),
        QAItem(
            question="What lesson was learned from the result?",
            answer=f"The lesson learned was this: {incident['lesson']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sneer?",
            answer="A sneer is a mean or mocking look or smile that shows scorn.",
        ),
        QAItem(
            question="What does scrawny mean?",
            answer=(
                "Scrawny is an unkind word sometimes used for a person or animal who looks very thin. "
                "A body shape does not tell us someone's health, ability, or worth."
            ),
        ),
        QAItem(
            question="Why can sound effects make a story fun to read?",
            answer="Sound effects like hiss, splash, and thump help the reader imagine what is happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    python = {
        ("badger", "hare"),
    }
    model = asp.one_model(asp_program("#show sneer/2."))
    clingo_set = set(asp.atoms(model, "sneer"))
    if clingo_set == python:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python))
    return 1


CURATED = [
    StoryParams(name="Pip", rival="Grub", helper="Moss", place="meadow", incident=0),
    StoryParams(
        name="Tilly", rival="Bram", helper="Fern", place="meadow",
        incident=6, opening=3, reflection=2, apology=2, cadence=5,
    ),
    StoryParams(
        name="Nip", rival="Muck", helper="Sage", place="meadow",
        incident=11, opening=6, reflection=7, apology=1, cadence=6,
    ),
]


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show sneer/2.\n#show lesson/1."))
    return sorted(set(asp.atoms(model, "sneer")))


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show sneer/2.\n#show lesson/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} ASP-suggested sneer facts")
        for t in asp_valid():
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name}: sneer at the meadow"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
