#!/usr/bin/env python3
"""
A standalone heartwarming storyworld about Ing, a mirror, and Pogo.

Ing wants to cross a quiet garden bridge with a little mirror. Pogo, a
bouncy puppy, keeps blocking the way because he is afraid of his reflection
in the stream. A small conflict becomes suspense when the mirror slips toward
the water, and kindness helps Pogo face what he fears.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


ENTITY_HUMAN = "human"
ENTITY_ANIMAL = "animal"
ENTITY_OBJECT = "object"


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""
    owner: Optional[str] = None


@dataclass
class World:
    setting: str
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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    setting: str
    hero: str = "Ing"
    animal: str = "Pogo"
    object_name: str = "mirror"
    challenge: str = "bridge"
    opening_style: int = 0
    suspense_style: int = 0
    kindness_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    opening: str
    conflict: str
    clue: str
    risk: str
    kind_action: str
    invitation: str
    helper_action: str
    resolution: str
    ending: str
    lesson: str


SETTINGS = {
    "garden": "the community garden",
    "courtyard": "the sunny courtyard",
    "park": "the little park",
    "schoolyard": "the schoolyard garden",
    "orchard": "the old orchard",
}

HERO_NAMES = ["Ing", "Mara", "Lina", "Nell", "Sumi", "Tavi"]
ANIMAL_NAMES = ["Pogo", "Bim", "Tumble", "Pip", "Wobble"]
OBJECT_NAMES = ["mirror", "round mirror", "pocket mirror", "silver mirror"]

SCENARIOS = {
    "bridge": Scenario(
        opening="was carrying a small mirror to the far side of the garden",
        conflict="planted all four paws on the bridge and barked whenever the mirror flashed",
        clue="noticed that Pogo kept staring past the glass at the dark stream below",
        risk="the mirror slid toward the water when Pogo bounced against the railing",
        kind_action="knelt beside Pogo instead of pulling him forward",
        invitation="We can go slowly. You may look at me, and then we can look together",
        helper_action="placed one paw on the first board and watched Ing cross each board beside him",
        resolution="Pogo discovered that the face in the mirror moved when he moved because it was only his own reflection",
        ending="At the bridge's far end, Pogo touched noses with his reflection and wagged at both of them.",
        lesson="Kindness can make a frightening moment small enough to understand.",
    ),
    "fountain": Scenario(
        opening="was bringing a mirror to a fountain so the children could study sunlight",
        conflict="kept leaping between Ing and the fountain whenever the mirror caught a bright spark",
        clue="saw Pogo hiding his nose whenever the fountain made a deep gurgling sound",
        risk="the mirror tipped against the fountain rim as Pogo scrambled backward",
        kind_action="covered the bright glass and sat quietly beside Pogo",
        invitation="We can listen first. You can decide when the light comes back",
        helper_action="peeked at the covered mirror, then stood close while Ing uncovered one corner",
        resolution="Pogo learned that the sparkle was light, not a chasing animal",
        ending="The fountain made one bright star in the mirror, and Pogo gave it a careful, friendly sniff.",
        lesson="Gentle patience gives courage time to grow.",
    ),
    "hill": Scenario(
        opening="was taking a mirror up a grassy hill for a cloud-watching game",
        conflict="bounced in front of Ing and tried to bury the mirror under a heap of leaves",
        clue="found two trembling ears beneath the leaves whenever a cloud covered the sun",
        risk="the mirror began sliding down the hill toward a patch of thorny bushes",
        kind_action="asked Pogo to help choose a safe, shady place to sit",
        invitation="You can help me stop the mirror, and I will stay right beside you",
        helper_action="pressed his paws into the grass and nudged the mirror toward a soft blanket",
        resolution="Pogo saw that the dark reflection changed with the clouds and did not mean danger",
        ending="A white cloud drifted across the mirror, and Pogo bounced beneath it like a tiny moon.",
        lesson="Sharing a job can turn fear into steady courage.",
    ),
    "shed": Scenario(
        opening="was carrying a mirror toward the garden shed to repair a loose window",
        conflict="guarded the shed door and growled at the tall shape reflected in the glass",
        clue="heard a tiny kitten crying inside the shed whenever Pogo barked",
        risk="the mirror wobbled as the door opened and nearly fell between the stones",
        kind_action="lowered the mirror and showed Pogo how to listen for the kitten",
        invitation="The reflection can wait. Let us help the small voice first",
        helper_action="stood quietly while Ing opened the door and guided the kitten into the sunlight",
        resolution="Pogo understood that the tall shape had been Ing carrying the mirror, not a stranger",
        ending="The kitten curled against Pogo's warm side while the mirror leaned safely against the shed.",
        lesson="Kindness listens for the need hidden inside a noisy conflict.",
    ),
    "pond": Scenario(
        opening="was walking beside a pond with a mirror for a family picture",
        conflict="kept nudging Ing away from the water and barking at the reflection of a bird",
        clue="realized Pogo was trying to warn the bird about a loose reed near the bank",
        risk="a sudden tug sent the mirror skittering across the damp path",
        kind_action="looked where Pogo was looking before asking him to move",
        invitation="Show me the trouble, Pogo, and then help me carry the mirror safely",
        helper_action="led Ing to the reed and held the loose end while she moved it from the water",
        resolution="The bird flew safely away, and Pogo stopped confusing the mirror's sparkle with danger",
        ending="The family picture showed Ing, Pogo, and a bright bird reflected together in the calm pond.",
        lesson="Understanding another creature's worry can reveal a helpful heart.",
    ),
}

OPENINGS = [
    "{hero} liked carrying useful things carefully, especially things that could catch a whole sky.",
    "In {setting}, {hero} had a plan, a steady pair of hands, and one shiny surprise.",
    "{hero} believed even an ordinary walk could become important if someone needed help.",
    "The morning began softly for {hero}, until a mirror, a puppy, and a narrow path met.",
    "Whenever {hero} saw a problem, {hero} first tried to look closely.",
]

SUSPENSE_LINES = [
    "For one breath, nobody moved.",
    "The shiny edge crept closer to danger.",
    "Ing heard the faint scrape and felt the moment balance on a thread.",
    "Pogo's paws slipped, and the quiet place suddenly seemed very large.",
    "The next choice mattered more than the next step.",
]

KINDNESS_LINES = [
    "Ing lowered her voice and let the silence become safe.",
    "Ing put the important object down and paid attention to Pogo first.",
    "Ing took one slow breath so Pogo could borrow her calm.",
    "Ing stopped arguing and watched for the clue in Pogo's worried face.",
    "Ing offered a choice instead of giving a command.",
]


ASP_RULES = r"""
% The mirror creates conflict when Pogo is afraid and near the route.
conflict(S) :- setting(S), near(pogo, mirror), afraid(pogo).

% Suspense exists while the mirror is at risk and the helper has not acted.
suspense(S) :- setting(S), conflict(S), mirror_at_risk(mirror), not helped(pogo).

% A kind action turns conflict into cooperation.
cooperation(pogo) :- kind_action(ing), helped(pogo), understood(pogo).

% A reasonable story contains conflict, suspense, kindness, and resolution.
valid_story(S) :- setting(S), conflict(S), suspense(S), cooperation(pogo).
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("setting", key) for key in SETTINGS]
    lines.extend(
        [
            asp.fact("near", "pogo", "mirror"),
            asp.fact("afraid", "pogo"),
            asp.fact("mirror_at_risk", "mirror"),
            asp.fact("kind_action", "ing"),
            asp.fact("helped", "pogo"),
            asp.fact("understood", "pogo"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp

    expected = set(SETTINGS)
    actual = {setting for (setting,) in asp_valid()}
    if expected != actual:
        print("MISMATCH between Python and ASP setting coverage.")
        print("only python:", sorted(expected - actual))
        print("only asp:", sorted(actual - expected))
        return 1

    rng = random.Random(17)
    for setting in SETTINGS:
        params = resolve_params(
            argparse.Namespace(
                setting=setting,
                hero=None,
                animal=None,
                object_name=None,
                challenge=None,
            ),
            rng,
        )
        params.setting = setting
        sample = generate(params)
        if not sample.story or "Pogo" not in sample.story:
            print(f"Generated story check failed for {setting}.")
            return 1

    print(f"OK: ASP model covers {len(expected)} settings and generated stories pass.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming Ing, mirror, and Pogo kindness-conflict storyworld."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero")
    parser.add_argument("--animal")
    parser.add_argument("--object-name")
    parser.add_argument("--challenge", choices=SCENARIOS)
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
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        hero=args.hero or rng.choice(HERO_NAMES),
        animal=args.animal or rng.choice(ANIMAL_NAMES),
        object_name=args.object_name or rng.choice(OBJECT_NAMES),
        challenge=args.challenge or rng.choice(list(SCENARIOS)),
        opening_style=rng.randrange(len(OPENINGS)),
        suspense_style=rng.randrange(len(SUSPENSE_LINES)),
        kindness_style=rng.randrange(len(KINDNESS_LINES)),
    )


def validate_params(params: StoryParams) -> None:
    if not params.hero.strip():
        raise StoryError("The hero needs a name.")
    if not params.animal.strip():
        raise StoryError("Pogo needs a name.")
    if params.hero.lower() == params.animal.lower():
        raise StoryError("The child and the puppy need different names.")
    if params.object_name.lower() in {params.hero.lower(), params.animal.lower()}:
        raise StoryError("The mirror needs a name different from the characters.")
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}.")
    if params.challenge not in SCENARIOS:
        raise StoryError(f"Unknown challenge: {params.challenge}.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(SETTINGS[params.setting])

    hero = world.add(
        Entity(
            id="ing",
            kind=ENTITY_HUMAN,
            type="child",
            label=params.hero,
            phrase=f"{params.hero}",
            memes={"kindness": 0.0, "worry": 0.0, "patience": 0.0},
            location="path",
        )
    )
    pogo = world.add(
        Entity(
            id="pogo",
            kind=ENTITY_ANIMAL,
            type="puppy",
            label=params.animal,
            phrase=f"the puppy {params.animal}",
            meters={"bouncy": 1.0, "steady": 0.0, "safe": 1.0},
            memes={"fear": 0.0, "trust": 0.0, "joy": 0.0},
            location="path",
        )
    )
    mirror = world.add(
        Entity(
            id="mirror",
            kind=ENTITY_OBJECT,
            type="mirror",
            label=params.object_name,
            phrase=f"the small {params.object_name}",
            meters={"shiny": 1.0, "safe": 1.0, "at_risk": 0.0},
            owner="ing",
            location="path",
        )
    )

    world.facts.update(
        params=params,
        scenario=SCENARIOS[params.challenge],
        hero=hero,
        pogo=pogo,
        mirror=mirror,
        conflict=False,
        clue_found=False,
        helped=False,
        understood=False,
        resolved=False,
    )
    return world


def predict_reasonableness(world: World) -> dict[str, bool]:
    clone = world.copy()
    pogo = clone.get("pogo")
    mirror = clone.get("mirror")
    return {
        "conflict": pogo.location == "route" and pogo.memes.get("fear", 0) > 0,
        "suspense": mirror.meters.get("at_risk", 0) > 0,
        "resolution": clone.facts.get("understood", False)
        and clone.facts.get("helped", False),
    }


def act_opening(world: World) -> None:
    params = world.facts["params"]
    scenario = world.facts["scenario"]
    hero = world.get("ing")
    mirror = world.get("mirror")
    world.say(
        OPENINGS[params.opening_style].format(
            hero=hero.label,
            setting=world.setting,
        )
    )
    world.say(
        f"{hero.label} {scenario.opening}, carrying {mirror.phrase} by its handle."
    )
    world.say(
        f"The mirror held a pale patch of sky, while {world.get('pogo').phrase} "
        "bounced along beside the path."
    )


def act_conflict(world: World) -> None:
    params = world.facts["params"]
    scenario = world.facts["scenario"]
    hero = world.get("ing")
    pogo = world.get("pogo")
    mirror = world.get("mirror")

    pogo.location = "route"
    pogo.memes["fear"] = 1.0
    world.facts["conflict"] = True
    world.say(f"Then {pogo.phrase} {scenario.conflict}.")
    world.say(
        f'"Move, Pogo," {hero.label} said. "I need to get this mirror across."'
    )
    world.say(
        f'"I cannot," Pogo seemed to say, though he only gave a frightened little bark.'
    )
    world.say(
        f"{hero.label} felt annoyed, but {pogo.label}'s paws stayed planted between "
        f"{hero.label} and {mirror.phrase}."
    )
    mirror.location = "route"
    world.para()


def act_clue_and_kindness(world: World) -> None:
    params = world.facts["params"]
    scenario = world.facts["scenario"]
    hero = world.get("ing")
    pogo = world.get("pogo")

    world.say(
        f"{hero.label} {KINDNESS_LINES[params.kindness_style]} "
        f"Then {hero.pronoun if False else 'she'} {scenario.clue}."
    )
    world.say(
        f'That changed the question. "{scenario.invitation}," {hero.label} said.'
    )
    world.say(
        f'"You can stay close to me," {hero.label} added. "We will solve this together."'
    )
    hero.memes["kindness"] = 1.0
    hero.memes["patience"] = 1.0
    pogo.memes["trust"] = 1.0
    world.facts["clue_found"] = True
    world.facts["helped"] = True


def act_suspense(world: World) -> None:
    params = world.facts["params"]
    scenario = world.facts["scenario"]
    hero = world.get("ing")
    pogo = world.get("pogo")
    mirror = world.get("mirror")

    mirror.meters["at_risk"] = 1.0
    mirror.meters["safe"] = 0.0
    world.say(f"Just then, {scenario.risk}.")
    world.say(SUSPENSE_LINES[params.suspense_style])
    world.say(
        f"{hero.label} reached for the handle, but {pogo.label} was still trembling."
    )
    world.say(
        f'"Do not jump," {hero.label} whispered. "Put one paw where I put my hand."'
    )
    world.say(f"{pogo.label} took a breath and tried.")


def act_resolution(world: World) -> None:
    scenario = world.facts["scenario"]
    hero = world.get("ing")
    pogo = world.get("pogo")
    mirror = world.get("mirror")

    pogo.location = "beside hero"
    pogo.meters["steady"] = 1.0
    pogo.meters["safe"] = 1.0
    pogo.memes["fear"] = 0.0
    pogo.memes["trust"] = 2.0
    pogo.memes["joy"] = 1.0
    mirror.location = "safe path"
    mirror.meters["at_risk"] = 0.0
    mirror.meters["safe"] = 1.0
    world.facts["understood"] = True

    world.say(
        f"Together, {hero.label} and {pogo.label} {scenario.helper_action}."
    )
    world.say(f"At last, {scenario.resolution}.")
    world.say(
        f'"You were scared, not naughty," {hero.label} told {pogo.label}. '
        '"Thank you for letting me help."'
    )
    world.say(f"{scenario.ending}")
    world.say(scenario.lesson)
    world.facts["resolved"] = True


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    act_opening(world)
    world.para()
    act_conflict(world)
    act_clue_and_kindness(world)
    act_suspense(world)
    act_resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        f"Write a heartwarming story about {params.hero}, a mirror, and {params.animal} in {world.setting}.",
        f"Show how conflict begins when {params.animal} {scenario.conflict}.",
        f"Build suspense around this risk: {scenario.risk}.",
        f"Resolve the story through kindness, ending with: {scenario.ending}",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        QAItem(
            question=f"Why was {params.hero} carrying the mirror?",
            answer=f"{params.hero} was carrying the mirror because {scenario.opening}.",
        ),
        QAItem(
            question=f"How did {params.animal} create the conflict?",
            answer=f"{params.animal} {scenario.conflict}.",
        ),
        QAItem(
            question=f"What clue helped {params.hero} understand {params.animal}?",
            answer=f"{params.hero} {scenario.clue}. This showed that {params.animal} was frightened rather than simply being difficult.",
        ),
        QAItem(
            question="What made the middle of the story suspenseful?",
            answer=f"The mirror became unsafe because {scenario.risk}. Ing had to help Pogo stay calm while protecting the mirror.",
        ),
        QAItem(
            question="How did kindness change the conflict?",
            answer=f"Ing {scenario.kind_action}. Ing offered Pogo a safe choice and stayed close while Pogo learned to help.",
        ),
        QAItem(
            question=f"What did {params.animal} do at the end?",
            answer=f"{params.animal} {scenario.helper_action}. The puppy became steady enough to cooperate.",
        ),
        QAItem(
            question="What does the final image show?",
            answer=scenario.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a mirror do?",
            answer="A mirror reflects light and can show an image of the things in front of it.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means noticing another person's or animal's needs and responding with care while still solving any harm.",
        ),
        QAItem(
            question="What is conflict?",
            answer="Conflict is a problem caused by different needs, fears, or choices. Listening can help people find a safe solution.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next when something important may go wrong.",
        ),
        QAItem(
            question="What kind of transformation happens to Pogo?",
            answer="Pogo changes from frightened and blocking the path to trusting Ing and helping carefully. The transformation is emotional and behavioral, not magical.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        parts = [
            f"meters={entity.meters}",
            f"memes={entity.memes}",
            f"location={entity.location}",
        ]
        lines.append(f"{entity.id}: {entity.label} ({entity.type}) " + " ".join(parts))
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


CURATED = [
    StoryParams(setting="garden", hero="Ing", animal="Pogo", object_name="mirror", challenge="bridge"),
    StoryParams(setting="courtyard", hero="Mara", animal="Bim", object_name="round mirror", challenge="fountain"),
    StoryParams(setting="park", hero="Lina", animal="Tumble", object_name="pocket mirror", challenge="hill"),
    StoryParams(setting="schoolyard", hero="Nell", animal="Pip", object_name="silver mirror", challenge="shed"),
    StoryParams(setting="orchard", hero="Sumi", animal="Wobble", object_name="mirror", challenge="pond"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("Compatible ASP story settings:")
        for (setting,) in asp_valid():
            print(f"  {setting}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for params in CURATED:
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 30):
            seed = base_seed + attempts
            attempts += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            try:
                sample = generate(params)
            except StoryError as error:
                print(error)
                return
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.hero} / {params.animal} / {params.object_name} in {params.setting}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
