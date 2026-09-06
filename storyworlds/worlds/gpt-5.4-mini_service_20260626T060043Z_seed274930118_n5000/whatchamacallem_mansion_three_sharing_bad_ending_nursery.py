#!/usr/bin/env python3
"""
A tiny nursery-rhyme story world about three small characters, a mansion, and
a whatchamacallem that does not get shared very well.

Premise:
- Three little characters explore a grand mansion.
- They find one curious object, the whatchamacallem.
- They try to share it.

Turn:
- Sharing is hard because the object is only comfortable for one at a time.
- The first attempt goes badly and leaves everyone cross, crowded, or sad.

Ending:
- The bad ending is gentle and child-facing: the object breaks, the room is
  messy, and the three must settle for a sad quiet rather than a tidy fix.

This script keeps the prose in a nursery-rhyme cadence while still driving it
from a simulated world model with meters and memes.
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
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["tired", "sad", "crowded", "mess", "broken", "unavailable", "care", "joy", "greed", "share"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name1: str
    name2: str
    name3: str
    mansion: str = "the mansion"
    seed: Optional[int] = None
    incident: str = "music_room"
    telling_mode: str = "couplets"
    variation: int = 0


@dataclass(frozen=True)
class Incident:
    key: str
    room: str
    object_phrase: str
    invitation: str
    conflict: str
    first_try: str
    clue: str
    careful_action: str
    consequence: str
    final_image: str
    lesson: str
    sound: str


INCIDENTS = [
    Incident(
        "music_room", "music room", "a brass music-box whatchamacallem",
        "wind its moon-shaped key and choose the first tune",
        "each friend wanted a different song before the moon clock chimed",
        "They twisted the key in three directions instead of taking turns.",
        "A paper note inside said that one gentle turn played one whole tune.",
        "They stopped pulling and set the bent key on a velvet cloth.",
        "The spring sighed flat, so the promised dance never began.",
        "Three still slippers stood beneath a silent silver horn.",
        "A turn snatched from a friend may spoil everybody's turn.", "ting-tang-TUNK",
    ),
    Incident(
        "winter_garden", "winter garden", "a wheeled watering whatchamacallem",
        "guide its three little spouts among the thirsty ferns",
        "all three steered toward their favorite flower bed at once",
        "They tugged separate handles and rolled over the marked path.",
        "Tiny arrows showed that the cart had to travel in one shared loop.",
        "They caught the cart before it reached the glass and closed its tap.",
        "Its front wheel lodged in mud, and the noon watering had to be canceled.",
        "Dry fern tips curled beside one muddy, motionless wheel.",
        "Sharing the route matters as much as sharing the cart.", "squish-swish-clunk",
    ),
    Incident(
        "portrait_gallery", "portrait gallery", "a rainbow-lens whatchamacallem",
        "hold it before the portraits and discover their hidden colors",
        "nobody would let go long enough for another friend to focus the lens",
        "Six hands crowded the rim and left three cloudy fingerprints.",
        "A painted eye on the case pointed toward a soft cleaning square.",
        "They placed the lens safely in its case and wiped only the case lid.",
        "The lens stayed cloudy, so the secret rainbow remained unseen.",
        "A shut black case reflected three disappointed faces.",
        "An object cannot be enjoyed together when nobody makes room.", "rub-rub-blur",
    ),
    Incident(
        "clock_tower", "clock-tower room", "a feathered clock whatchamacallem",
        "carry one message to the bell keeper before three o'clock",
        "each friend tried to make it deliver a different message",
        "They pushed three message cards into its narrow silver slot.",
        "Three tiny dots over the slot meant one card for each trip.",
        "They pulled their cards free, but one torn corner remained inside.",
        "The mechanism jammed, and the bell keeper received no message at all.",
        "At three, an empty perch rocked while the great bell stayed still.",
        "Agreeing first keeps a shared messenger from carrying nothing.", "whirr-click-hush",
    ),
    Incident(
        "nursery", "old nursery", "a patchwork rocking whatchamacallem",
        "rock one sleepy toy while the friends sang a counting rhyme",
        "the friends argued over which toy deserved the first ride",
        "They piled a bear, a rabbit, and a wooden duck onto the small seat.",
        "The stitched number three belonged to the rhyme, not the seat's capacity.",
        "They lifted the toys away when the rocker's wooden arm began to bow.",
        "A runner split before anyone had a ride, and the lullaby ended early.",
        "Three toys waited in a row beside one crooked patchwork rocker.",
        "Fair turns protect both a friendship and the thing being shared.", "rock-creak-crack",
    ),
    Incident(
        "kitchen", "mansion kitchen", "a cherry-red mixing whatchamacallem",
        "turn its handle together to make three small berry buns",
        "each friend poured in a favorite filling without asking the others",
        "Jam, mint, and mustard tumbled into the bowl together.",
        "The recipe card showed three buns made one flavor at a time.",
        "They switched off the mixer and told the cook exactly what happened.",
        "The batter could not be served, and there were no buns for tea.",
        "Three clean plates circled one bowl of green-and-red swirls.",
        "Sharing a treat begins with sharing the plan.", "glop-whop-stop",
    ),
    Incident(
        "map_room", "map room", "a rolling-map whatchamacallem",
        "reveal one safe path through the mansion's garden maze",
        "each friend pulled toward a different painted destination",
        "They unrolled all three map tabs across one another.",
        "A compass rose showed that the blue tab had to open first.",
        "They released the tabs, but not before a ribbon tore from its spindle.",
        "The map curled shut, and the garden expedition was called off.",
        "Three packed satchels rested below a map tied closed with string.",
        "A shared adventure needs one path chosen together.", "flap-snap-zip",
    ),
    Incident(
        "ballroom", "dusty ballroom", "a star-projecting whatchamacallem",
        "cast three constellations across the ceiling for a midnight show",
        "all three friends grabbed its single direction lever",
        "They jerked the lever north, south, and sideways in one beat.",
        "A brass star beside the lever marked a slow clockwise path.",
        "They let go and covered the hot lamp with its safety shade.",
        "The bulb went dark, so the guests saw only an ordinary ceiling.",
        "Paper invitations lay under a ceiling with no stars at all.",
        "Shared control works only when friends listen before they move.", "fizz-pop-dark",
    ),
    Incident(
        "library", "round library", "a story-wheel whatchamacallem",
        "choose one picture and begin a tale for three listeners",
        "each friend spun toward a different ending before hearing the beginning",
        "They slapped three picture buttons while the wheel was still turning.",
        "A tiny bookmark said, 'Beginning, middle, ending: one at a time.'",
        "They waited for the wheel to stop and marked the muddled page.",
        "The paper ribbon tangled, and story hour ended without a story.",
        "Three cushions faced a blank white square on the library wall.",
        "Taking turns helps a shared story make sense.", "flip-whip-rip",
    ),
    Incident(
        "attic", "moonlit attic", "a wind-up flying whatchamacallem",
        "carry three paper wishes across the room",
        "each friend tied on a wish too large for its little wings",
        "They wound the propeller again when it could not lift the heavy bundle.",
        "A faded label allowed one light wish on each flight.",
        "They stopped the propeller with its wooden brake and stepped back.",
        "One wing bent, and all three wishes stayed in the attic.",
        "Moonlight rested on three unopened wishes beneath a drooping wing.",
        "Sharing a helper means respecting what it can safely carry.", "brrr-flutter-plop",
    ),
    Incident(
        "game_room", "green game room", "a marble-sorting whatchamacallem",
        "sort three colored marbles for a friendly mansion game",
        "each friend claimed the center chute for a different color",
        "They dropped all the marbles before choosing whose rule to use.",
        "Three painted cups showed that the colors needed separate rounds.",
        "They closed the chute as soon as marbles began knocking together.",
        "A glass marble chipped, and the game was put away for inspection.",
        "Three empty score cards lay beside a latched wooden game box.",
        "Rules must be shared before game pieces can be shared.", "click-clack-crick",
    ),
    Incident(
        "conservatory", "rainy conservatory", "an umbrella-tree whatchamacallem",
        "open one broad canopy so the three could watch the rain",
        "each friend pulled a different opening cord without counting together",
        "They yanked red, blue, and yellow cords in a jumble.",
        "A rhyme stitched on the trunk gave the order: blue, then red, then gold.",
        "They released the cords and moved clear when the branches shivered.",
        "The canopy folded inside out, and their rain-watching picnic was over.",
        "Three dry cups sat packed away while rain ticked on bare glass.",
        "A shared shelter needs patience, order, and room for every hand.", "tug-twang-flump",
    ),
]

TELLING_MODES = ["couplets", "counting", "echo", "question", "bell", "whisper", "refrain", "footsteps"]
OPENINGS = [
    "In a mansion of windows and weather-vane gold, three little friends found a room full of old.",
    "One-two-three went the feet on the floor; three friends crossed the mansion and opened a door.",
    "The mansion was waking with tickle and tap when three friends set out with a rhyme and a map.",
    "What waits where the long mansion passage bends? A curious room and three curious friends.",
    "Bong went a clock in the mansion's east wing; three friends hurried over to look at the thing.",
    "Soft through the mansion, where sleepy halls gleam, three friends went exploring as quiet as dream.",
    "Share it with care, share it fair, sang three friends as they climbed the broad stair.",
    "Pat-pat-patter through shadow and sun, three friends searched the mansion for something to do.",
]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.params)
        w.entities = copy.deepcopy(self.entities)
        w.lines = list(self.lines)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def name_pool() -> list[str]:
    return ["Milo", "Nina", "Toby", "Luna", "Pip", "Cora", "Otto", "Daisy"]


def build_nursery_names(rng: random.Random) -> tuple[str, str, str]:
    names = rng.sample(name_pool(), 3)
    return names[0], names[1], names[2]


def bad_share_penalty(world: World) -> None:
    for e in world.entities.values():
        if e.kind == "character" and e.memes["share"] < 1:
            e.meters["sad"] += 1
            e.meters["crowded"] += 1


def maybe_break_whatchamacallem(world: World) -> None:
    obj = world.get("whatchamacallem")
    holders = [e for e in world.entities.values() if e.kind == "character" and e.held_by == e.id]
    if len(holders) >= 2:
        obj.meters["broken"] += 1
        obj.meters["mess"] += 1
        for h in holders:
            h.meters["sad"] += 1
            h.memes["greed"] += 1
        world.say("The whatchamacallem gave a tiny crack and made a sorry little clatter.")


def setup_world(params: StoryParams) -> World:
    w = World(params)
    w.add(Entity(id=params.name1, kind="character", type="child", label=params.name1, location=params.mansion))
    w.add(Entity(id=params.name2, kind="character", type="child", label=params.name2, location=params.mansion))
    w.add(Entity(id=params.name3, kind="character", type="child", label=params.name3, location=params.mansion))
    w.add(Entity(
        id="whatchamacallem",
        kind="thing",
        type="thing",
        label="whatchamacallem",
        phrase=next(i.object_phrase for i in INCIDENTS if i.key == params.incident),
        location=next(i.room for i in INCIDENTS if i.key == params.incident),
        plural=False,
    ))
    return w


def tell_story(w: World) -> None:
    a, b, c = w.get(w.params.name1), w.get(w.params.name2), w.get(w.params.name3)
    obj = w.get("whatchamacallem")
    mansion = w.params.mansion
    incident = next(i for i in INCIDENTS if i.key == w.params.incident)
    rng = random.Random(w.params.variation)
    mode_index = TELLING_MODES.index(w.params.telling_mode)
    discovery_lines = [
        f"There, in the {incident.room}, waited {incident.object_phrase}.",
        f"Behind a low curtain in the {incident.room}, they discovered {incident.object_phrase}.",
        f"A gleam from the {incident.room} led them to {incident.object_phrase}.",
        f"On a little stand in the {incident.room} sat {incident.object_phrase}.",
        f"The strangest treasure in the {incident.room} was {incident.object_phrase}.",
        f"Under a dust cover in the {incident.room}, they found {incident.object_phrase}.",
    ]
    proposals = [
        f'"Let all three of us share it," said {a.id}. "We can {incident.invitation}."',
        f'{a.id} read its purpose aloud: they could {incident.invitation}. "A job for three!" cried {b.id}.',
        f'"What if we {incident.invitation}?" asked {b.id}. {c.id} clapped, and {a.id} agreed.',
        f'{c.id} proposed that they use it together to {incident.invitation}. The others answered, "One-two-three!"',
        f'The three promised to share the whatchamacallem and {incident.invitation}.',
        f'"Together," said {a.id}. "We shall {incident.invitation}." {b.id} and {c.id} nodded.',
    ]
    warnings = [
        f'"Wait," said {c.id}. "Sharing is not the same as grabbing."',
        f'{b.id} began, "Perhaps we need a plan," but the eager hands were already moving.',
        f'"One at a time might be wiser," {a.id} murmured too late.',
        f'{c.id} counted, "One, two--" Yet nobody waited for three.',
        f'A quiet thought tugged at {b.id}: fair sharing needed listening first.',
        f'"Slow and fair," whispered {a.id}, though excitement swallowed the words.',
    ]
    reactions = [
        f'{a.id} stared at the result. "I wanted a turn, not this," they said.',
        f'"Oh," breathed {b.id}. "Our three wishes left no wish for anyone."',
        f'{c.id} folded their hands. "We shared the grabbing, but not the choosing."',
        f'"We hurried past one another," said {a.id}, and nobody disagreed.',
        f'{b.id} looked from friend to friend. "Next time, the plan comes first."',
        f'The three said together, very softly, "That was not fair sharing."',
    ]
    closing_leads = [
        "No cheer, no encore, no second try came that day.",
        "The mansion felt bigger when their happy plan was gone.",
        "They stayed friends, but the afternoon could not be mended.",
        "Nobody was hurt, yet all three carried a lump of disappointment.",
        "The caretaker would help later; for now, the adventure was finished.",
        "They apologized, but an apology could not bring back the missed event.",
        "Their quarrel ended, though its consequence remained.",
        "They knew what to do next time, but next time was not today.",
    ]

    discovery = discovery_lines[rng.randrange(len(discovery_lines))]
    proposal = proposals[rng.randrange(len(proposals))]
    warning = warnings[rng.randrange(len(warnings))]
    reaction = reactions[rng.randrange(len(reactions))]
    closing_lead = closing_leads[rng.randrange(len(closing_leads))]
    w.say(OPENINGS[mode_index])
    w.say(f"Their names were {a.id}, {b.id}, and {c.id}; three in a mansion, nimble and small.")
    w.say("They meant to share fairly, though meaning is easier than doing.")
    w.say(discovery)
    w.say(proposal)

    w.para()
    w.say(f"The trouble was this: {incident.conflict}.")
    w.say(warning)
    w.say(incident.first_try)
    w.say(f"{incident.sound.capitalize()}! went the whatchamacallem.")
    obj.held_by = a.id
    for child in (a, b, c):
        child.held_by = child.id
        child.memes["share"] += 0.25
        child.meters["crowded"] += 1
    obj.meters["mess"] += 1

    w.para()
    w.say(f"Then they noticed the clue they had missed. {incident.clue}")
    w.say(incident.careful_action)
    w.say(reaction)
    obj.meters["unavailable"] += 1
    if incident.key in {"music_room", "nursery", "map_room", "attic", "game_room"}:
        obj.meters["broken"] += 1
    obj.held_by = None
    for child in (a, b, c):
        child.held_by = None
        child.meters["sad"] += 1
        child.memes["care"] += 0.5
    w.say(incident.consequence)

    w.para()
    w.say(closing_lead)
    w.say(f"Their sad little lesson was plain: {incident.lesson}")
    if w.params.telling_mode in {"couplets", "refrain", "echo"}:
        w.say("Share with a pause, share with a plan; three careful friends do all that they can.")
    elif w.params.telling_mode in {"counting", "bell"}:
        w.say("One for listening, two for care, three for taking a turn that is fair.")
    elif w.params.telling_mode == "question":
        w.say("Was it the ending they wanted to see? No--but it taught all three how sharing should be.")
    elif w.params.telling_mode == "whisper":
        w.say("Soft went the lesson from wall to wall: share with care, or joy may fall.")
    else:
        w.say("Pat went one foot, pat went two; the third walked slowly, thinking it through.")
    w.say(incident.final_image)

    w.facts.update(
        a=a, b=b, c=c, obj=obj, mansion=mansion, incident=incident,
        broken=obj.meters["broken"] > 0, unavailable=True,
        consequence=incident.consequence, lesson=incident.lesson,
        ending_image=incident.final_image, discovery=discovery, proposal=proposal,
        warning=warning, reaction=reaction, closing_lead=closing_lead,
    )


def story_qa(world: World) -> list[QAItem]:
    a, b, c = world.facts["a"], world.facts["b"], world.facts["c"]
    incident: Incident = world.facts["incident"]
    return [
        QAItem(
            question="Who were the three friends in the mansion?",
            answer=f"The three friends were {a.id}, {b.id}, and {c.id}.",
        ),
        QAItem(
            question="What did they find?",
            answer=world.facts["discovery"],
        ),
        QAItem(
            question=f"What poor first attempt did the friends make in the {incident.room}?",
            answer=incident.first_try,
        ),
        QAItem(
            question="What warning or careful thought did somebody offer?",
            answer=world.facts["warning"],
        ),
        QAItem(
            question="What clue did the friends understand too late?",
            answer=incident.clue,
        ),
        QAItem(
            question="What careful action did the friends take after noticing the clue?",
            answer=incident.careful_action,
        ),
        QAItem(
            question="What gentle bad ending followed their poor sharing?",
            answer=f"{incident.consequence} {incident.final_image}",
        ),
        QAItem(
            question="What lesson did the three friends learn?",
            answer=incident.lesson,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mansion?",
            answer="A mansion is a very big house with many rooms.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or enjoy the same thing too.",
        ),
        QAItem(
            question="What is a whatchamacallem?",
            answer="A whatchamacallem is a playful word for an object when someone does not want to name it exactly.",
        ),
    ]


def generation_prompts() -> list[str]:
    return [
        'Write a short nursery-rhyme story about three friends in a mansion who find a whatchamacallem and try to share it.',
        'Tell a child-facing story with three small characters, a grand mansion, and a bad ending caused by poor sharing.',
        'Write a simple rhyming tale using the words whatchamacallem, mansion, and three, ending with a gentle consequence.',
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world: three, mansion, whatchamacallem, and a bad ending.")
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--name3")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    n1, n2, n3 = args.name1, args.name2, args.name3
    if len({x for x in [n1, n2, n3] if x}) != len([x for x in [n1, n2, n3] if x]):
        raise StoryError("Please choose three different names.")
    if not n1 or not n2 or not n3:
        n1, n2, n3 = build_nursery_names(rng)
    return StoryParams(
        name1=n1,
        name2=n2,
        name3=n3,
        seed=args.seed,
        incident=rng.choice(INCIDENTS).key,
        telling_mode=rng.choice(TELLING_MODES),
        variation=rng.getrandbits(63),
    )


def generate(params: StoryParams) -> StorySample:
    w = setup_world(params)
    tell_story(w)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(),
        story_qa=story_qa(w),
        world_qa=world_qa(w),
        world=w,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
entity(E) :- child(E).
entity(whatchamacallem).

three_children(A,B,C) :- child(A), child(B), child(C), A != B, A != C, B != C.

shared_bad_end(A,B,C) :- three_children(A,B,C), takes(A), takes(B), takes(C).
broken_object :- shared_bad_end(_,_,_).

#show shared_bad_end/3.
#show broken_object/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("child", "alpha"),
        asp.fact("child", "beta"),
        asp.fact("child", "gamma"),
        asp.fact("object", "whatchamacallem"),
        asp.fact("takes", "alpha"),
        asp.fact("takes", "beta"),
        asp.fact("takes", "gamma"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show broken_object/0."))
    ok = any(sym.name == "broken_object" for sym in model)
    if ok:
        print("OK: ASP twin produces a bad ending model.")
        return 0
    print("MISMATCH: ASP twin did not produce expected model.")
    return 1


CURATED = [
    StoryParams("Milo", "Nina", "Toby", incident="music_room", telling_mode="couplets", variation=11),
    StoryParams("Luna", "Pip", "Cora", incident="winter_garden", telling_mode="counting", variation=22),
    StoryParams("Otto", "Daisy", "Mia", incident="attic", telling_mode="whisper", variation=33),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show broken_object/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
