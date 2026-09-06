#!/usr/bin/env python3
"""
A small pirate-tale story world with a cautionary turn, a sharing fix, and a
light humorous ending.

Seed premise:
- A little pirate sees a trouble spot with one eyed caution.
- The crew wants a shared treasure snack.
- A careless choice could spoil the loot.
- The captain warns, they share wisely, and the joke lands safely.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent / "storyworlds"))
        break
from results import QAItem, StoryError, StorySample  # noqa: E402

ASP_RULES = r"""
eyed(X) :- pirate(X), has_eye(X, one).
cautionary_scene(P) :- pirate(P), sees_warning(P).
sharing_scene(C) :- crew(C), has_treasure(C), shares(C).
humor_scene(P) :- pirate(P), jokes(P), nobody_splashes(P).
safe_story(P) :- cautionary_scene(P), humor_scene(P), sharing_scene(C).
"""

PIRATE_NAMES = ["Mara", "Jett", "Nico", "Luna", "Ivo", "Pip", "Rae", "Sail"]
CREW_NAMES = ["Captain Brine", "First Mate Wren", "Bosun Tilly", "Deckhand Oat"]
SCENES = ["dock", "cove", "deck", "island shore"]
TREASURES = ["golden pear", "sweet biscuit", "berry tart", "shiny apple"]
TREATS = ["crumbly bun", "salted plum", "tiny cake", "honey toast"]


@dataclass(frozen=True)
class PirateIncident:
    title: str
    premise: str
    danger: str
    impulse: str
    clue: str
    action: str
    result: str
    shared_use: str
    lesson: str
    joke: str
    ending: str


INCIDENTS = [
    PirateIncident(
        title="the leaning gangplank",
        premise="A supply cart waited beside a gangplank that dipped whenever a wave lifted the ship.",
        danger="a cracked support peg was sliding out beneath the middle board",
        impulse="hurry everyone across before the tide turned",
        clue="a line of fresh sawdust trembled below the loose peg",
        action="closed the gangplank, fetched the shipwright, and helped lash a sound spare board beside it",
        result="the supplies came aboard by the steady stern ramp without anyone falling",
        shared_use="cut the treasure into equal pieces for the tired carriers",
        lesson="A warning is useful only when it changes what the crew does next.",
        joke="That plank had one job, and it nearly went overboard from the pressure",
        ending="The repaired board rested level above the silver tide, with four empty plates stacked beside it.",
    ),
    PirateIncident(
        title="the smoke-filled galley",
        premise="Breakfast smoke curled from the galley while the cook searched for a missing oven cloth.",
        danger="a pan handle pointed into the narrow passage and its oil had begun to spit",
        impulse="reach past the hot pan to rescue the treat alone",
        clue="tiny bright drops snapped against the stove guard",
        action="warned the cook, cleared the passage, and carried cool lids while an adult covered the pan",
        result="the oil settled and breakfast reached the table safely",
        shared_use="served the treasure and treat from the same broad tray so every watch got a portion",
        lesson="Being quick-eyed does not mean doing a dangerous job without the right helper.",
        joke="The breakfast was hot enough to demand its own captain's hat",
        ending="Safe blue stove flames flickered beneath the kettle as spoons tapped clean bowls.",
    ),
    PirateIncident(
        title="the false treasure map",
        premise="Two maps appeared in the chart chest just before the crew sailed toward Gullwing Island.",
        danger="one map sent the ship through a channel marked with hidden rocks",
        impulse="choose the brighter map because its red X looked exciting",
        clue="the ink crossed a fold that was newer than the old salt stains",
        action="shared both maps with the navigator and compared their soundings line by line",
        result="the crew followed the verified channel and marked the false route for correction",
        shared_use="packed equal treasure slices for the two lookouts who checked the safe passage",
        lesson="Important choices deserve shared evidence, not the shiniest answer.",
        joke="The false map's X apparently meant 'extra wrong'",
        ending="At sunset, the corrected chart lay under glass while Gullwing Island glowed ahead.",
    ),
    PirateIncident(
        title="the crowded signal mast",
        premise="Festival ribbons fluttered from the mast as fog began swallowing the harbor bells.",
        danger="the ribbons had wrapped around the red emergency flag",
        impulse="leave the pretty knots until after the crew's picnic",
        clue="one red corner tugged beneath three loops of blue cloth",
        action="called the crew together, lowered the ribbons, and freed the signal halyard",
        result="the lookout raised the red flag in time for an approaching ferry to slow",
        shared_use="turned the saved ribbons into place mats beneath equal helpings of treasure",
        lesson="Decoration must never cover a signal that keeps neighbors safe.",
        joke="Even the flag looked relieved to stop dressing as a parcel",
        ending="The red flag flew clear above the fog while blue ribbons dried along the rail.",
    ),
    PirateIncident(
        title="the thirsty castaway",
        premise="A small boat waved for help beyond the cove after a long, sunny afternoon.",
        danger="the castaway was thirsty while the rescue skiff had only one full water jug",
        impulse="bring the treasure first because it looked more cheerful than plain water",
        clue="the castaway pointed to an empty cup and shaded tired eyes",
        action="shared the clue with the captain, loaded water first, and kept the skiff balanced",
        result="the castaway drank slowly and returned safely to shore",
        shared_use="divided the treasure and treat only after everyone had enough water",
        lesson="Fair sharing begins with what people need, not merely what looks festive.",
        joke="The biscuit tried to look useful, but it had forgotten how to pour",
        ending="Three filled cups caught the evening light beside a plate of equal crumbs.",
    ),
    PirateIncident(
        title="the sleeping turtle",
        premise="The crew found a treasure box wedged near a turtle nest on the island shore.",
        danger="dragging the box straight back would crush the low fence around the nest",
        impulse="pull hard before another crew could claim the prize",
        clue="tiny flipper tracks crossed the sand between the box and the fence",
        action="stopped the rope team, showed everyone the tracks, and built a wide carrying sling",
        result="the box moved around the nest while the resting turtle remained undisturbed",
        shared_use="opened the box publicly and shared its treasure according to the crew list",
        lesson="Finding something first does not give anyone permission to harm what surrounds it.",
        joke="The turtle declined a crew share because its pockets were at sea",
        ending="Moonlit flipper tracks curved toward the water beside an unbroken little fence.",
    ),
    PirateIncident(
        title="the tangled anchor line",
        premise="A squall darkened the bay while the anchor line lay looped around a barrel of treats.",
        danger="dropping the anchor would yank the barrel across the working deck",
        impulse="hold the barrel alone and tell the captain to lower away",
        clue="each warning bell made the tight loop creep closer to the barrel's rim",
        action="called a stop, shared the problem with both deck teams, and helped reroute the slack line",
        result="the anchor dropped cleanly and the ship held steady through the squall",
        shared_use="opened the unharmed barrel and passed one treat to each soaked sailor",
        lesson="A brave warning can be as important as a strong pair of hands.",
        joke="The barrel had nearly taken a very fast course in anchor management",
        ending="Rain pearls rolled from the quiet anchor line as warm treats circled the lantern-lit deck.",
    ),
    PirateIncident(
        title="the borrowed spyglass",
        premise="A neighboring crew lent its finest spyglass for the morning reef watch.",
        danger="sticky treasure crumbs on the lens made a dark reef look like open water",
        impulse="hide the smear and pretend the view was clear",
        clue="the same black blur stayed still when the spyglass turned toward the sky",
        action="admitted the spill, returned the glass for proper cleaning, and watched with the spare",
        result="the lookout called the reef correctly and the borrowed lens came back spotless",
        shared_use="put the treasure on plates away from every navigation tool",
        lesson="Telling the truth about a mistake protects both trust and safety.",
        joke="The reef was innocent; the biscuit crumb had been impersonating an island",
        ending="The clean spyglass reflected one sharp star above a crumb-free chart table.",
    ),
    PirateIncident(
        title="the overloaded dinghy",
        premise="The tide began falling while the crew loaded picnic baskets into a little dinghy.",
        danger="one more treasure chest would push the painted waterline below the waves",
        impulse="balance the chest on two knees and squeeze aboard anyway",
        clue="water already lapped over the lowest letter of the dinghy's name",
        action="asked everyone to count the load, left the chest guarded ashore, and made two trips",
        result="both crossings stayed level and every passenger arrived dry",
        shared_use="unlocked the chest at the picnic and gave both boat groups equal portions",
        lesson="Sharing space safely sometimes means waiting for a second turn.",
        joke="The dinghy was a boat, not a sandwich to be stuffed",
        ending="Two neat trails of footprints met beside the chest on a bright, dry beach.",
    ),
    PirateIncident(
        title="the ringing cave",
        premise="A cave echoed like a bell when the crew searched its ledges for a lost supply pouch.",
        danger="the rising tide could close the lowest tunnel before the searchers returned",
        impulse="keep the clue secret and dash into the tunnel for sole credit",
        clue="a wet shell line showed how high the last tide had climbed",
        action="showed the line to the crew, set a return bell, and searched the upper ledges in pairs",
        result="the pouch was found above the tide mark and everyone left before the bell rang twice",
        shared_use="shared its treasure with the whole search team outside the cave",
        lesson="A discovery becomes safer and more useful when it is shared early.",
        joke="The cave kept repeating orders, but never volunteered to carry the pouch",
        ending="The empty cave mouth mirrored the pink sky while the recovered pouch passed from hand to hand.",
    ),
    PirateIncident(
        title="the gull on the helm",
        premise="A bold gull landed on the helm just as the ship entered a busy fishing lane.",
        danger="a chase around the wheel could turn the ship across another boat's path",
        impulse="wave the treat overhead and race the gull for it",
        clue="the compass card slid two marks while the wheel moved beneath the bird",
        action="kept clear of the helm, warned the captain, and placed a shared crumb tray by the safe rail",
        result="the gull hopped away and the ship held its proper course",
        shared_use="broke the remaining treat into tiny fair pieces at the chart table",
        lesson="A funny surprise is no reason to crowd someone steering.",
        joke="The gull had excellent sea legs and absolutely no captain's license",
        ending="The wake ran straight behind the ship while one feather spun beside the empty tray.",
    ),
    PirateIncident(
        title="the cracked rain barrel",
        premise="A hot crossing left the fresh-water barrel with a thin crack near its lowest hoop.",
        danger="water was leaking faster each time someone tilted the barrel for a private cup",
        impulse="fill one large mug before telling the thirsty crew",
        clue="a dark wet line had reached the floorboards below the hoop",
        action="plugged the crack with the repair kit, announced the remaining level, and measured each cup",
        result="the saved water lasted until rain filled the clean catch cloth",
        shared_use="served the treasure beside equal water portions instead of rewarding whoever arrived first",
        lesson="Scarce supplies stay fair when the problem and the measure are visible to everyone.",
        joke="The barrel was sharing too generously with the floor",
        ending="Rain pattered into the clean cloth as twelve equal cups stood beneath it.",
    ),
]

OPENINGS = [
    "The trouble began during {title}.",
    "By the time the bell struck once, {hero} had eyed something wrong with {title}.",
    "No chart had warned the crew about {title}.",
    "The day's smallest clue belonged to {title}.",
    "A laugh was already traveling across the deck when {title} turned serious.",
    "At {place}, the crew's plans changed because of {title}.",
    "One-eyed {hero} expected a quiet watch, not {title}.",
    "The crew first treated {title} as a nuisance.",
    "Before anyone divided the food, {title} demanded attention.",
    "Captain and crew remembered this voyage as the day of {title}.",
]


@dataclass
class Character:
    id: str
    role: str
    eyed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"


@dataclass
class Setting:
    place: str = "the moonlit dock"


@dataclass
class StoryParams:
    name: str
    crew: str
    place: str
    treasure: str
    treat: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    hero: Character
    crew: Character
    shared_treasure: str
    shared_treat: str
    incident: Optional[PirateIncident] = None
    route: int = 0
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with caution, sharing, and humor.")
    ap.add_argument("--name", choices=PIRATE_NAMES)
    ap.add_argument("--crew", choices=CREW_NAMES)
    ap.add_argument("--place", choices=SCENES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--treat", choices=TREATS)
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


def asp_facts() -> str:
    import asp
    lines = [asp.fact("pirate", "hero"), asp.fact("crew", "crew"), asp.fact("has_eye", "hero", "one")]
    lines += [
        asp.fact("has_treasure", "crew"),
        asp.fact("shares", "crew"),
        asp.fact("jokes", "hero"),
        asp.fact("nobody_splashes", "hero"),
        asp.fact("sees_warning", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_story/1."))
    atoms = set(asp.atoms(model, "safe_story"))
    expected = {("hero",)}
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(PIRATE_NAMES),
        crew=args.crew or rng.choice(CREW_NAMES),
        place=args.place or rng.choice(SCENES),
        treasure=args.treasure or rng.choice(TREASURES),
        treat=args.treat or rng.choice(TREATS),
    )


def make_world(params: StoryParams) -> World:
    hero = Character(id=params.name, role="pirate", eyed=True, meters={"caution": 1.0}, memes={"humor": 0.5})
    crew = Character(id=params.crew, role="crew", eyed=False, meters={"sharing": 1.0}, memes={"kindness": 1.0})
    if params.seed is not None:
        key = params.seed
    else:
        raw = "|".join([params.name, params.crew, params.place, params.treasure, params.treat])
        key = int.from_bytes(hashlib.sha256(raw.encode("utf-8")).digest()[:8], "big")
    return World(
        setting=Setting(place=f"the {params.place}"),
        hero=hero,
        crew=crew,
        shared_treasure=params.treasure,
        shared_treat=params.treat,
        incident=INCIDENTS[key % len(INCIDENTS)],
        route=(key // len(INCIDENTS)) % len(OPENINGS),
    )


def tell(world: World) -> None:
    h, c = world.hero, world.crew
    incident = world.incident
    assert incident is not None
    opening = OPENINGS[world.route].format(
        title=incident.title,
        hero=h.id,
        place=world.setting.place,
    )
    world.say(f"{opening} {incident.premise}")
    world.say(
        f"At {world.setting.place}, one-eyed pirate {h.id} studied the scene instead of trusting the first impression. "
        f"They noticed that {incident.danger}."
    )
    world.para()
    world.say(
        f"For one hasty moment, {h.id} wanted to {incident.impulse}. "
        f'"Hold fast," said {c.id}. "A sharp eye still needs a careful plan."'
    )
    world.say(
        f"Then {h.id} eyed the evidence more closely: {incident.clue}. "
        f"They told the whole crew what they had seen rather than keeping the clue to themself."
    )
    world.para()
    world.say(f"Together, they {incident.action}. As a result, {incident.result}.")
    world.say(
        f"Once the danger had passed, they {incident.shared_use}. They also passed around "
        f"{world.shared_treasure} and {world.shared_treat}, checking that every pirate had a fair share."
    )
    world.para()
    world.say(
        f'"{incident.joke}," {h.id} said. Even {c.id} laughed, and the welcome humor loosened the last worried frowns.'
    )
    world.say(
        f"It was a cautionary pirate lesson about watching, speaking up, and sharing: {incident.lesson} "
        f"{incident.ending}"
    )
    world.facts.update(
        hero=h,
        crew=c,
        setting=world.setting,
        incident=incident,
        danger=incident.danger,
        clue=incident.clue,
        action=incident.action,
        result=incident.result,
        lesson=incident.lesson,
        ending=incident.ending,
        route=world.route,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly pirate tale about {f['incident'].title}, where an eyed pirate follows a clue, prevents harm, shares fairly, and ends with gentle humor.",
        f"Tell a cautionary story in which {f['hero'].id} and {f['crew'].id} respond to {f['danger']} at {f['setting'].place}.",
        f"Write a playful pirate story where the clue is {f['clue']}, the crew shares {world.shared_treasure} and {world.shared_treat}, and the ending shows what changed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h, c = world.hero, world.crew
    incident = world.incident
    assert incident is not None
    return [
        QAItem(
            question=f"What danger did {h.id} notice during {incident.title}?",
            answer=f"{h.id} noticed that {incident.danger}. Looking carefully kept the crew from acting on a risky first impression.",
        ),
        QAItem(
            question=f"Which clue changed the crew's plan at {world.setting.place}?",
            answer=f"The clue was that {incident.clue}. {h.id} shared that evidence with {c.id} and the rest of the crew.",
        ),
        QAItem(
            question=f"How did the pirates solve the problem in {incident.title}?",
            answer=f"Together, they {incident.action}. Because of that choice, {incident.result}.",
        ),
        QAItem(
            question=f"How did the crew practice sharing after the danger passed?",
            answer=f"They {incident.shared_use}. They also divided {world.shared_treasure} and {world.shared_treat} fairly among the pirates.",
        ),
        QAItem(
            question=f"What proved that the crew's choice worked?",
            answer=f"The result was that {incident.result}. The final image confirms it: {incident.ending}",
        ),
        QAItem(
            question=f"Why did the humor belong at the end of this cautionary tale?",
            answer=f"The danger had already been handled before {h.id} joked that {incident.joke.lower()}. The laugh released tension without making the warning seem unimportant.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be eyed?",
            answer="In this story, eyed appears in one-eyed and in the sense of looking closely. Having one eye does not create special powers; the pirate spots trouble by paying attention to evidence.",
        ),
        QAItem(
            question="Why should pirates share treasure?",
            answer="Pirates should share treasure so everyone gets a fair part and the crew stays happy.",
        ),
        QAItem(
            question="Why can humor help in a story?",
            answer="Humor can help because a small joke can ease tension and leave the ending feeling warm and cheerful.",
        ),
    ]


def dump_trace(world: World) -> str:
    incident = world.incident
    assert incident is not None
    return "\n".join([
        "--- world model state ---",
        f"hero={world.hero.id} role={world.hero.role} eyed={world.hero.eyed} meters={world.hero.meters} memes={world.hero.memes}",
        f"crew={world.crew.id} role={world.crew.role} meters={world.crew.meters} memes={world.crew.memes}",
        f"place={world.setting.place}",
        f"treasure={world.shared_treasure}",
        f"treat={world.shared_treat}",
        f"incident={incident.title}",
        f"danger={incident.danger}",
        f"clue={incident.clue}",
        f"result={incident.result}",
        f"route={world.route}",
    ])


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def curated() -> list[StoryParams]:
    return [
        StoryParams(name="Mara", crew="Captain Brine", place="dock", treasure="golden pear", treat="honey toast"),
        StoryParams(name="Pip", crew="First Mate Wren", place="cove", treasure="sweet biscuit", treat="tiny cake"),
        StoryParams(name="Nico", crew="Bosun Tilly", place="deck", treasure="berry tart", treat="salted plum"),
        StoryParams(name="Luna", crew="Deckhand Oat", place="island shore", treasure="shiny apple", treat="crumbly bun"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show eyed/1.\n#show cautionary_scene/1.\n#show sharing_scene/1.\n#show humor_scene/1.\n#show safe_story/1."))
        print("\n".join(str(a) for a in model))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            p.seed = (args.seed or 0) + i if args.seed is not None else None
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
