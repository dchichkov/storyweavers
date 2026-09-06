#!/usr/bin/env python3
"""
A small standalone story world for a Space Adventure-style tale about a
crew that meets a strange thorn-like foil object, gets a surprise, and ends
with reconciliation through a little magic.
"""

from __future__ import annotations

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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pilot", "engineer", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str = "the little starship"
    setting: str = "deep space"
    surprise: str = "a glowing surprise"
    magic: str = "soft magic"
    reconciliation: str = "a kind apology"
    obstacle: str = "a thorn-like foil shard"


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
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


@dataclass
class StoryParams:
    captain: str
    companion: str
    ship_name: str
    place: str
    seed: Optional[int] = None
    scenario: Optional[str] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    premise: str
    obstacle: str
    rushed_action: str
    consequence: str
    clue: str
    careful_action: str
    reveal: str
    apology: str
    repair: str
    outcome: str
    lesson: str
    ending: str


CAPTAIN_NAMES = ["Nova", "Mira", "Ari", "Zia", "Lena", "Tess"]
COMPANION_NAMES = ["Pip", "Bo", "Jax", "Rua", "Tavi", "Kio"]
PLACES = [
    "the quiet moon field",
    "the blue comet tunnel",
    "the ringed-planet orbit",
    "the lantern asteroid",
]

SCENARIOS = [
    Scenario(
        key="seed_vault",
        premise="was carrying moon-seeds to a greenhouse station before its lamps went dark",
        obstacle="a thorn-like foil cage had folded around the station's solar sail",
        rushed_action="tugged the cage with the ship's tractor beam",
        consequence="the foil tightened and shaded the last row of seedlings",
        clue="each thorn relaxed whenever the greenhouse chimes rang",
        careful_action="matched the chimes with three notes from a magic tuning crystal",
        reveal="the cage was a frightened space-vine protecting its silver seeds",
        apology="admitted that pulling first had made the vine more afraid",
        repair="returned the loose seeds and guided the vine onto an empty trellis",
        outcome="the solar sail opened and warm light reached every seedling",
        lesson="listening can reveal what force only makes worse",
        ending="one silver vine curled beside the window while green shoots lifted into the light",
    ),
    Scenario(
        key="comet_hatchling",
        premise="was mapping a nursery trail used by young comet-fish",
        obstacle="a thorn-like foil shell was flashing across the safest channel",
        rushed_action="switched on a bright warning beacon to chase it away",
        consequence="the shell spun faster and scattered the comet-fish into the dark",
        clue="a tiny peeping sound answered every dim pulse from the dashboard",
        careful_action="lowered the lights and sent a slow magic heartbeat through the radio",
        reveal="the sharp shell held a lost hatchling that mistook the beacon for its parent",
        apology="said the loud light had frightened a creature they meant to protect",
        repair="wrapped the shell in a soft signal and led it back to the glowing school",
        outcome="the comet-fish gathered around the hatchling and reopened the channel",
        lesson="gentle signals travel farther than frightening ones",
        ending="the smallest comet-fish flicked a bright tail goodbye beneath the ship",
    ),
    Scenario(
        key="mirror_moon",
        premise="was delivering a peace lantern to two villages on opposite sides of a tiny moon",
        obstacle="a thorn-like foil mirror hung between them and threw each village's signals backward",
        rushed_action="accused the far village of sending a dazzling prank",
        consequence="both villages closed their landing gates and the peace lantern began to fade",
        clue="the same bent star appeared in every reflected message",
        careful_action="traced the reflections with a magic compass instead of blaming either village",
        reveal="an old weather mirror had torn loose and twisted their friendly greetings",
        apology="sent both villages the complete recording and owned the mistaken accusation",
        repair="worked with both signal crews to flatten and anchor the mirror",
        outcome="the original greetings crossed clearly and both gates opened together",
        lesson="checking the whole message can mend a quarrel built from fragments",
        ending="the peace lantern glowed between two open gates under one small moon",
    ),
    Scenario(
        key="clockwork_beacon",
        premise="was racing to restart a beacon before a family ship reached a dusty space crossing",
        obstacle="thorn-like foil teeth had jammed the beacon's clockwork crown",
        rushed_action="struck the restart switch again and again",
        consequence="the crown shed sparks and pointed the family ship toward a rock field",
        clue="one foil tooth carried the same maker's mark as the beacon",
        careful_action="used a magic lens to read the tiny repair instructions hidden in the mark",
        reveal="the supposed debris was the beacon's own folded emergency key",
        apology="confessed that impatience had nearly broken the machine they needed",
        repair="unfolded the key, reset the crown by hand, and sent the corrected route",
        outcome="the family ship crossed safely beneath a steady blue beam",
        lesson="a strange piece deserves inspection before it is treated as rubbish",
        ending="the repaired beacon swept one calm blue circle across the waiting stars",
    ),
    Scenario(
        key="ice_library",
        premise="was collecting a promised story from a library carved inside a wandering ice moon",
        obstacle="a thorn-like foil bookmark had frozen across the library door",
        rushed_action="warmed the bookmark with the engine exhaust",
        consequence="letters melted from the nearest ice-page and ran like blue rain",
        clue="the loose letters gathered around a small empty line in the bookmark",
        careful_action="spelled the missing name with a magic ink-light",
        reveal="the bookmark was a lonely index spirit waiting to be properly introduced",
        apology="promised the librarian to repair the damaged page instead of hiding the mistake",
        repair="restored each letter and gave the index spirit a place in the catalog",
        outcome="the door opened and the promised story rang softly from the shelves",
        lesson="honest repair belongs beside every apology",
        ending="a new silver name gleamed on the catalog while blue letters froze neatly into place",
    ),
    Scenario(
        key="storm_kite",
        premise="was helping a weather crew steer a harmless crystal storm away from a school dome",
        obstacle="a thorn-like foil kite had snagged the storm's steering ribbon",
        rushed_action="cut what looked like the kite's loose tail",
        consequence="the storm turned toward the school and rattled its glass roof",
        clue="the cut end sparked in time with the weather crew's control drum",
        careful_action="joined the ends with a magic knot that carried both rhythm and current",
        reveal="the kite was the storm's missing rudder, not an obstacle",
        apology="told the weather crew exactly which line had been cut",
        repair="retied the rudder and beat the correct turning rhythm together",
        outcome="the storm curved toward an empty plain and watered its crystal flowers",
        lesson="learning an object's purpose should come before changing it",
        ending="rainbows trembled over the school dome as crystal flowers opened far away",
    ),
    Scenario(
        key="whale_song",
        premise="was following an ancient space-whale song through a field of quiet satellites",
        obstacle="a thorn-like foil ribbon had wrapped around the oldest satellite dish",
        rushed_action="ordered the dish to broadcast at full power through the ribbon",
        consequence="the song cracked into noise and the space whale turned away",
        clue="the foil holes formed the opening notes of the whale's melody",
        careful_action="played those notes through a magic flute at half volume",
        reveal="the ribbon was a translation sheet left by earlier whale listeners",
        apology="lowered the transmitter and apologized for trying to shout through a song",
        repair="aligned the ribbon's holes and answered the whale in its own gentle pattern",
        outcome="the whale returned and guided the ship around the silent satellites",
        lesson="understanding begins when an answer leaves room to listen",
        ending="a vast silver tail passed beneath the stars as one clear note lingered behind",
    ),
    Scenario(
        key="shared_meteor",
        premise="was escorting two mining crews who both claimed the same singing meteor",
        obstacle="a thorn-like foil seam divided the meteor into two glittering halves",
        rushed_action="promised the brighter half to the crew that called first",
        consequence="the other crew blocked the route and both halves stopped singing",
        clue="each half produced only every other note of the melody",
        careful_action="used a magic echo bowl to let both crews hear the missing notes together",
        reveal="the meteor made power only while its paired halves answered one another",
        apology="withdrew the hasty promise and invited both crews to design a fair plan",
        repair="built a shared station around the seam with controls on both sides",
        outcome="the whole melody returned and powered both crews' homes",
        lesson="reconciliation can create more than winning one half of a dispute",
        ending="two crews waved from opposite windows while the joined meteor sang between them",
    ),
    Scenario(
        key="garden_satellite",
        premise="was bringing water to a garden satellite whose flowers cleaned the nearby air",
        obstacle="thorn-like foil petals had closed over the satellite's drinking funnels",
        rushed_action="pried one metal petal open with a cargo hook",
        consequence="the petal snapped and a cloud of thirsty seed-dust escaped",
        clue="the remaining petals leaned toward the ship's warm kitchen window",
        careful_action="coaxed them open with a magic sunrise projected across the hull",
        reveal="the foil was a night-blooming plant that had overslept in an eclipse",
        apology="gathered the lost seed-dust and admitted the hook had caused the break",
        repair="mended the petal, filled the funnels, and adjusted the satellite's dawn clock",
        outcome="the flowers drank deeply and began cleaning the air again",
        lesson="careful observation can turn a rescue into the right rescue",
        ending="silver petals opened around beads of water as the first clean breeze crossed the deck",
    ),
    Scenario(
        key="robot_message",
        premise="was carrying a homesick repair robot back to its makers",
        obstacle="a thorn-like foil bundle tapped against the cargo door in a secret rhythm",
        rushed_action="locked the bundle in a shield box without asking the robot about it",
        consequence="the robot went silent and erased the route to its home workshop",
        clue="the tapping matched the robot's goodbye rhythm, only played backward",
        careful_action="reversed the rhythm with a magic music wheel and opened the box safely",
        reveal="the bundle was a reply from the robot's makers saying they missed it too",
        apology="admitted that fear had made the crew ignore the robot's knowledge",
        repair="invited the robot to decode the route and steer the final approach",
        outcome="the workshop doors opened before the ship even finished landing",
        lesson="trust grows when everyone affected gets a voice in the solution",
        ending="the robot tapped hello on the ramp while a hundred workshop lights blinked back",
    ),
    Scenario(
        key="shadow_bridge",
        premise="was taking medicine across a gap where no ordinary bridge could stand",
        obstacle="a thorn-like foil shadow stretched across the gap and bristled whenever engines approached",
        rushed_action="fired a clearing pulse at the shadow",
        consequence="the bridge vanished completely and the medicine case began to warm",
        clue="a nearby moon painted one safe silver stripe whenever the engines were quiet",
        careful_action="let magic sails catch the moonbeam while every engine rested",
        reveal="the sharp shadow was the bridge's warning shape, not the bridge itself",
        apology="told the waiting clinic why the careless pulse had delayed them",
        repair="followed the moonlit stripe and reset the warning stones on the far side",
        outcome="the medicine arrived cool and the shadow bridge became visible again",
        lesson="courage includes admitting delay and choosing a safer second attempt",
        ending="the medicine case clicked shut beneath a bridge drawn in pale moonlight",
    ),
    Scenario(
        key="festival_crown",
        premise="was delivering a floating crown for the first shared festival of three small planets",
        obstacle="thorn-like foil points sprang from the crown and made each planet suspect sabotage",
        rushed_action="hid the crown behind the ship and claimed the delivery was merely late",
        consequence="the three festival bands stopped playing and began packing their instruments",
        clue="each point cast the symbol of a different planet when turned toward starlight",
        careful_action="raised the crown with a magic thread so everyone could inspect it together",
        reveal="the surprise points were folded picture screens meant to honor all three planets",
        apology="told the gathered children the truth about hiding the unfamiliar crown",
        repair="unfolded each screen with one helper from every planet",
        outcome="the bands combined their songs and the shared festival finally began",
        lesson="truth and shared work can reconcile people faster than a tidy excuse",
        ending="three bright symbols revolved above the dancers while the crown chimed in time",
    ),
]

TELLING_MODES = ["arrival", "warning", "dialogue", "countdown", "memory", "mystery", "promise", "question"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld with surprise, reconciliation, and magic.")
    ap.add_argument("--captain", choices=CAPTAIN_NAMES)
    ap.add_argument("--companion", choices=COMPANION_NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ship-name")
    ap.add_argument("--scenario", choices=[scenario.key for scenario in SCENARIOS])
    ap.add_argument("--telling-mode", choices=TELLING_MODES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("theme", "space"),
        asp.fact("feature", "surprise"),
        asp.fact("feature", "reconciliation"),
        asp.fact("feature", "magic"),
        asp.fact("word", "thorn"),
        asp.fact("word", "like"),
        asp.fact("word", "foil"),
        asp.fact("obstacle", "thorn_like_foil"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
#show feature/1.
#show word/1.
#show obstacle/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show feature/1.")
    model = asp.one_model(program)
    feats = sorted(set(asp.atoms(model, "feature")))
    wanted = [("magic",), ("reconciliation",), ("surprise",)]
    if sorted(feats) == wanted:
        print("OK: ASP facts include the required features.")
        return 0
    print("MISMATCH: ASP feature facts are wrong.")
    print(feats)
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    companion = args.companion or rng.choice([n for n in COMPANION_NAMES if n != captain])
    place = args.place or rng.choice(PLACES)
    ship_name = args.ship_name or rng.choice(["Star Finch", "Silver Comet", "Moon Ripple", "Bright Loop"])
    return StoryParams(
        captain=captain,
        companion=companion,
        ship_name=ship_name,
        place=place,
        scenario=args.scenario or rng.choice(SCENARIOS).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def _pick(rng: random.Random, *choices: str) -> str:
    return rng.choice(choices)


def _opening(params: StoryParams, scenario: Scenario, rng: random.Random) -> list[str]:
    captain = f"Captain {params.captain}"
    setting = params.place
    ship = params.ship_name
    mode = params.telling_mode or "arrival"
    if mode == "warning":
        return [
            f'"Something sharp is ahead," {params.companion} warned as {ship} entered {setting}.',
            f"{captain} slowed the starship. The crew {scenario.premise}.",
        ]
    if mode == "dialogue":
        return [
            f'"Ready for one quiet trip?" {captain} asked. "In space? Never," {params.companion} replied.',
            f"Aboard {ship}, the crew {scenario.premise} near {setting}.",
        ]
    if mode == "countdown":
        return [
            f"The dashboard counted down from ten as {ship} crossed {setting}.",
            f"Before the count reached one, {captain} and {params.companion} needed to finish their task: the crew {scenario.premise}.",
        ]
    if mode == "memory":
        return [
            f"Later, {captain} would remember how peaceful {setting} looked from {ship}.",
            f"That was where the crew {scenario.premise}, just before the trouble began.",
        ]
    if mode == "mystery":
        return [
            f"The first surprise was a sound where space should have been silent.",
            f"It reached {ship} in {setting} while {captain}'s crew {scenario.premise}.",
        ]
    if mode == "promise":
        return [
            f"{captain} had made a promise, and {ship} carried the crew through {setting} to keep it.",
            f"The crew {scenario.premise}.",
        ]
    if mode == "question":
        return [
            f'"Why is it shining like that?" {params.companion} asked as {ship} reached {setting}.',
            f"{captain} had no answer yet. The crew {scenario.premise}.",
        ]
    return [
        f"{ship} glided into {setting} with {captain} at the controls and {params.companion} checking the instruments.",
        f"The crew {scenario.premise}.",
    ]


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    scenario = next((item for item in SCENARIOS if item.key == params.scenario), SCENARIOS[0])
    ship = Ship(name=params.ship_name, setting=params.place)
    world = World(ship)

    captain = world.add(Entity(
        id=params.captain,
        kind="character",
        type="captain",
        label="captain",
        phrase=f"Captain {params.captain}",
        location="bridge",
        traits=["brave", "curious"],
    ))
    companion = world.add(Entity(
        id=params.companion,
        kind="character",
        type="engineer",
        label="shipmate",
        phrase=f"{params.companion}",
        location="engine room",
        traits=["quick", "gentle"],
    ))
    shard = world.add(Entity(
        id="shard",
        kind="thing",
        type="artifact",
        label="thorn-like foil shard",
        phrase="a thorn-like foil shard",
        location="outside the hull",
        meters={"gleam": 1.0, "sharpness": 1.0},
        memes={"mystery": 1.0},
    ))
    world.facts.update(
        captain=captain,
        companion=companion,
        shard=shard,
        params=params,
        scenario=scenario.key,
        initial_task=scenario.premise,
        obstacle=scenario.obstacle,
        mistake=scenario.rushed_action,
        consequence=scenario.consequence,
        clue=scenario.clue,
        reveal=scenario.reveal,
        repair=scenario.repair,
        outcome=scenario.outcome,
        lesson=scenario.lesson,
    )

    for sentence in _opening(params, scenario, rng):
        world.say(sentence)
    world.say(
        _pick(
            rng,
            f"Then the scanners chimed: {scenario.obstacle}.",
            f"Their calm trip changed when they discovered {scenario.obstacle}.",
            f"A silver flicker became their next surprise: {scenario.obstacle}.",
        )
    )

    world.para()
    world.say(
        _pick(
            rng,
            f"It looked as thin as foil but bristled like a thorn, so {companion.id} {scenario.rushed_action}.",
            f'"I can fix that quickly," {companion.id} said, and {companion.pronoun()} {scenario.rushed_action}. The strange object looked like foil and thorn at once.',
            f"Because the thorn-like foil shape seemed dangerous, {companion.id} {scenario.rushed_action} before the crew studied it.",
        )
    )
    world.say(f"The choice had an immediate cost: {scenario.consequence}.")
    world.say(
        _pick(
            rng,
            f'"Stop," Captain {captain.id} said. "We need evidence, not another guess."',
            f"Captain {captain.id} took a slow breath and asked everyone to name what they knew, not what they feared.",
            f'"A surprise is not always an attack," Captain {captain.id} reminded the crew.',
        )
    )

    world.para()
    world.say(f"While they watched instead of rushing, they noticed that {scenario.clue}.")
    world.say(f"Captain {captain.id} {scenario.careful_action}.")
    world.say(
        _pick(
            rng,
            f"The magic did not erase the problem; it made the hidden pattern clear. They learned that {scenario.reveal}.",
            f"A quiet wash of magic revealed the truth: {scenario.reveal}.",
            f"Under the magic's soft light came the real surprise. They discovered that {scenario.reveal}.",
        )
    )

    world.para()
    world.say(f"{companion.id} {scenario.apology}.")
    world.say(
        _pick(
            rng,
            f'"Let us mend it together," Captain {captain.id} answered.',
            f"Captain {captain.id} accepted the apology and made room for everyone affected to help.",
            f'"Reconciliation needs a repair, too," Captain {captain.id} said kindly.',
        )
    )
    world.say(f"Together they {scenario.repair}.")
    world.say(f"At last, {scenario.outcome}.")

    world.para()
    world.say(
        _pick(
            rng,
            f"The crew carried one lesson onward: {scenario.lesson}.",
            f"From then on, they remembered that {scenario.lesson}.",
            f"Their repaired friendship taught them that {scenario.lesson}.",
        )
    )
    world.say("What began as a troubling surprise had ended in honest reconciliation.")
    world.say(f"As {ship.name} moved on through space, {scenario.ending}.")

    shard.location = "safely resolved"
    shard.meters["sharpness"] = 0.0
    shard.meters["understood"] = 1.0
    companion.memes["accountability"] = 1.0
    captain.memes["reconciliation"] = 1.0
    world.facts.update(story_end="reconciled", magic_used=True, surprise=True, repaired=True)

    prompts = [
        f"Write a short Space Adventure about Captain {params.captain} and a mistake the crew repairs. Include this obstacle: {scenario.obstacle}.",
        f"Tell a gentle spaceship story where surprise turns into reconciliation with magic. Use this clue: {scenario.clue}.",
        f"Write a child-friendly tale aboard {params.ship_name} whose ending shows that {scenario.lesson}.",
    ]
    story_qa = [
        QAItem(
            question=f"What obstacle surprised Captain {params.captain}'s crew?",
            answer=f"The obstacle was that {scenario.obstacle}. It interrupted the crew's task in {params.place}.",
        ),
        QAItem(
            question="What clue helped the crew understand the surprise?",
            answer=f"They noticed that {scenario.clue}. That evidence led them to discover that {scenario.reveal}.",
        ),
        QAItem(
            question=f"Why did {params.companion} apologize?",
            answer=f"{params.companion} apologized because {companion.pronoun()} {scenario.rushed_action}, and {scenario.consequence}. Together, the crew {scenario.repair}.",
        ),
        QAItem(
            question="How did the crew reach reconciliation?",
            answer=f"They listened to the apology and chose to make a repair together. The crew {scenario.repair}, so {scenario.outcome}.",
        ),
        QAItem(
            question="What lesson did the crew carry onward?",
            answer=f"They learned that {scenario.lesson}. Their final repair showed the lesson in action.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is surprise in a story like this?",
            answer="Surprise is when something unexpected appears and changes what the characters do next.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after worry or disagreement.",
        ),
        QAItem(
            question="What can magic do in a Space Adventure tale?",
            answer="Magic can help characters understand strange things, calm danger, and solve a problem kindly.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            bits = []
            if e.location:
                bits.append(f"location={e.location}")
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            print(f"  {e.id}: {e.type} {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show obstacle/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                captain="Nova",
                companion="Pip",
                ship_name="Star Finch",
                place="the quiet moon field",
                seed=101,
                scenario="seed_vault",
                telling_mode="arrival",
            ),
            StoryParams(
                captain="Mira",
                companion="Bo",
                ship_name="Silver Comet",
                place="the blue comet tunnel",
                seed=202,
                scenario="mirror_moon",
                telling_mode="dialogue",
            ),
            StoryParams(
                captain="Ari",
                companion="Jax",
                ship_name="Moon Ripple",
                place="the ringed-planet orbit",
                seed=303,
                scenario="festival_crown",
                telling_mode="mystery",
            ),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            attempt_seed = base_seed + i
            params = resolve_params(args, random.Random(attempt_seed))
            params.seed = attempt_seed
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.captain} and {p.companion} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
