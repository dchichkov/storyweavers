#!/usr/bin/env python3
"""A child-friendly superhero storyworld about bacon, a twist, and reconciliation."""

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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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
    partner: str = "Bolt"
    helper: str = "Mira"
    city: str = "Bright City"
    incident: int = 0
    opening: int = 0
    twist: int = 0
    reconciliation: int = 0
    cadence: int = 0


HEROES = ["Luna", "Nova", "Comet", "Skye", "Ruby", "Echo"]
PARTNERS = ["Bolt", "Dash", "Flash", "Clover", "Jet", "Pip"]
HELPERS = ["Mira", "Sunny", "Tess", "Robin", "Ash", "Kai"]
CITIES = ["Bright City", "Moonbeam City", "Sunrise City", "Star Harbor"]

INCIDENTS = [
    {
        "title": "the bacon beacon",
        "problem": "A hungry cloud-dragon had swallowed the city's emergency beacon and hidden it above the clock tower.",
        "bacon": "Luna carried a warm strip of bacon from the breakfast cart.",
        "plan": "The bacon smell would guide the dragon down while the heroes removed the beacon safely.",
        "failure": "Bolt rushed ahead and tugged the beacon's cable. The tower shook, and the dragon hugged the beacon tighter.",
        "clue": "Luna noticed that the dragon stopped growling whenever it smelled the bacon.",
        "action": "Luna offered the bacon, and Mira lowered a soft rescue net while Bolt carefully removed the loosened beacon.",
        "result": "The beacon flashed again, and its golden signal led lost children home.",
        "lesson": "A gentle invitation can work better than a powerful pull.",
        "ending": "That night, the beacon shone above the tower while the dragon nibbled its last crunchy bite.",
        "object": "emergency beacon",
    },
    {
        "title": "the bacon-powered rescue cart",
        "problem": "A rescue cart loaded with blankets rolled toward a fountain crowded with pigeons.",
        "bacon": "The cart's little snack box held a strip of bacon for the team's tired rescue dog.",
        "plan": "Luna would use the bacon to call the dog away from the cart, then remove the jammed wheel pin.",
        "failure": "Bolt grabbed the cart first. Rattle-rattle! It rolled faster down the hill.",
        "clue": "Luna saw the dog watching the bacon instead of the runaway cart.",
        "action": "She called softly, the dog padded aside, and Mira helped remove the bent pin with a silver tool.",
        "result": "The cart stopped before the fountain, and every blanket reached the chilly families.",
        "lesson": "Understanding what someone needs can open a safe path.",
        "ending": "The rescued cart rested beside the fountain, its blankets warm and dry.",
        "object": "rescue cart",
    },
    {
        "title": "the smoky rooftop signal",
        "problem": "Smoke covered the rooftop where a small robot was waiting for help.",
        "bacon": "A bacon-shaped signal sticker on Luna's glove made the robot beep with recognition.",
        "plan": "The team would follow the sticker's bright reflection and remove the robot's tangled antenna.",
        "failure": "Bolt waved a giant cape through the smoke, stirring it into a thicker cloud.",
        "clue": "Luna saw the robot's blue light blink whenever the bacon sticker caught the sun.",
        "action": "She covered the bright roof lamps, and Mira removed the antenna knot while Bolt guided the robot.",
        "result": "The robot rolled safely downstairs and turned on the clear-air fans.",
        "lesson": "A small clear signal can guide people through confusion.",
        "ending": "The robot projected a bright bacon-shaped thank-you into the clean evening sky.",
        "object": "tangled antenna",
    },
    {
        "title": "the midnight museum alarm",
        "problem": "A museum alarm rang because a wind-up moon statue had become stuck in its display case.",
        "bacon": "The night guard had packed a bacon sandwich, whose gentle smell reminded Luna of a careful morning plan.",
        "plan": "The heroes would quiet the alarm, remove the stuck spring, and leave the statue safely inside its case.",
        "failure": "Bolt struck the case with a bright power burst. Bong! The alarm became even louder.",
        "clue": "Luna saw that the alarm bell moved whenever the spring trembled.",
        "action": "She counted the bell's rhythm, then Mira removed the spring while Bolt held the case steady.",
        "result": "The alarm stopped, and the moon statue began turning again.",
        "lesson": "Listening before acting can prevent a bigger problem.",
        "ending": "The museum moon turned slowly beneath a quiet silver light.",
        "object": "moon statue",
    },
    {
        "title": "the storm-drain surprise",
        "problem": "Rainwater rushed toward a storm drain where a family of tiny robots was trapped.",
        "bacon": "Luna remembered that the robots loved the smell of bacon from the city's food festival.",
        "plan": "The bacon trail would lead them toward a dry ledge while the team removed the drain cover.",
        "failure": "Bolt tried to lift the cover alone, but the slippery metal slid back with a clang.",
        "clue": "The robots followed the bacon scent whenever Luna placed a piece near the dry stones.",
        "action": "Luna made a safe trail, and everyone pushed together to remove the cover.",
        "result": "The robots climbed out before the water rose, then repaired the city's rain sensors.",
        "lesson": "A shared plan makes heavy work safer.",
        "ending": "Rain drummed on the street while the little robots dried beside a warm bacon-scented stall.",
        "object": "drain cover",
    },
]

OPENINGS = [
    "In {city}, {hero} wore a silver cape and listened for trouble.",
    "At sunrise in {city}, {hero} checked the rooftops before the first hero alarm.",
    "The people of {city} knew that {hero} could fly, but they also knew {hero} asked careful questions.",
    "A bright alarm blinked over {city}, and {hero} raced toward it with {partner}.",
    "Before breakfast, {hero} and {partner} promised to protect every corner of {city}.",
]

TWISTS = [
    "{partner} had expected a fight, but the real danger was fear making the dragon hold tighter.",
    "The heroes thought the problem needed more strength. The twist was that the stuck object was protecting someone frightened.",
    "Just as the heroes prepared their biggest power, a small clue changed the whole plan.",
    "The loudest hero move made things worse, so the team had to try something patient instead.",
    "Behind the frightening noise was a lonely creature asking for help in the only way it knew.",
]

RECONCILIATIONS = [
    "{partner} lowered their head. 'I rushed in and made it worse. Can you forgive me?' {hero} nodded. 'Yes. Next time, we listen together.'",
    "'Your plan was wiser than my hurry,' said {partner}. '{hero}, may I help repair what I shook loose?' 'Please,' said {hero}.",
    "{partner} took a breath. 'I thought power was the answer.' {hero} replied, 'Power is best when it protects someone.'",
    "'I am sorry I ignored your clue,' {partner} said. '{hero} smiled. 'You noticed the next clue. That is how teammates grow.'",
]

CADENCES = [
    "The team moved in three careful steps: notice, invite, and remove.",
    "No cape flashed until every helper knew where to stand.",
    "The city held its breath while the quiet plan met the noisy trouble.",
    "One hero watched the danger, one offered kindness, and one handled the tool.",
    "Their second try began with listening instead of leaping.",
]


ASP_RULES = r"""
#show bacon/1.
#show remove/2.
#show reconciled/2.

bacon(B) :- useful(B).
remove(H, O) :- careful(H), loose(O).
reconciled(A, B) :- apologizes(A, B), forgives(B, A).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("useful", "bacon"),
            asp.fact("careful", "hero"),
            asp.fact("loose", "beacon"),
            asp.fact("apologizes", "partner", "hero"),
            asp.fact("forgives", "hero", "partner"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld about bacon, removal, a twist, and reconciliation."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--partner", choices=PARTNERS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--city", choices=CITIES, default=None)
    parser.add_argument("--incident", type=int, choices=range(len(INCIDENTS)))
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
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(HEROES),
        partner=args.partner or rng.choice(PARTNERS),
        helper=args.helper or rng.choice(HELPERS),
        city=args.city or rng.choice(CITIES),
        incident=args.incident if args.incident is not None else rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        twist=rng.randrange(len(TWISTS)),
        reconciliation=rng.randrange(len(RECONCILIATIONS)),
        cadence=rng.randrange(len(CADENCES)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.partner:
        raise StoryError("The hero and partner must have different names.")
    if not 0 <= params.incident < len(INCIDENTS):
        raise StoryError("The incident number is outside the available story domain.")

    world = World()
    hero = world.add(Entity(params.hero, kind="character", type="superhero", label=params.hero))
    partner = world.add(Entity(params.partner, kind="character", type="superhero", label=params.partner))
    helper = world.add(Entity(params.helper, kind="character", type="helper", label=params.helper))
    bacon = world.add(Entity("bacon", kind="food", type="bacon", label="bacon"))
    incident = INCIDENTS[params.incident]

    hero.meters.update({"energy": 1.0, "care": 0.8})
    partner.meters.update({"energy": 1.0, "hurry": 0.9})
    helper.meters.update({"tool_skill": 0.9})
    bacon.memes["comfort"] = 1.0
    partner.memes["pride"] = 1.0

    def fill(text: str) -> str:
        return text.format(
            hero=hero.id,
            partner=partner.id,
            helper=helper.id,
            city=params.city,
        )

    world.say(fill(OPENINGS[params.opening % len(OPENINGS)]))
    world.say(f"{incident['problem']} {incident['bacon']}")
    world.say(f"{hero.id} explained, '{incident['plan']}'")
    world.say(
        f"{partner.id} replied, 'We are superheroes. I can handle this!' "
        f"Then {incident['failure'].replace('Bolt', partner.id)}"
    )
    world.say(fill(TWISTS[params.twist % len(TWISTS)]))
    world.say(
        f"{hero.id} said, 'Please stop for one breath. Tell me what you see.' "
        f"{partner.id} answered, 'I see the danger holding on, not attacking.'"
    )
    world.say(incident["clue"])
    world.say(CADENCES[params.cadence % len(CADENCES)])
    world.say(incident["action"].replace("Luna", hero.id).replace("Mira", helper.id).replace("Bolt", partner.id))
    world.say(incident["result"])
    world.say(fill(RECONCILIATIONS[params.reconciliation % len(RECONCILIATIONS)]))
    world.say(f"Together, the heroes celebrated the lesson: {incident['lesson']}")
    world.say(incident["ending"])

    hero.memes["wisdom"] = 1.0
    partner.memes["humility"] = 1.0
    partner.memes["pride"] = 0.0
    world.facts.update(
        hero=hero,
        partner=partner,
        helper=helper,
        bacon=bacon,
        incident=incident,
        city=params.city,
        twist=True,
        reconciliation=True,
        removed=incident["object"],
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
    incident = f["incident"]
    hero = f["hero"]
    return [
        f"Write a child-friendly superhero story where {hero.id} uses bacon to help solve {incident['title']}.",
        f"Tell a superhero story with a twist, careful removal of the {incident['object']}, and reconciliation.",
        "Write a bright adventure in which listening and kindness succeed where rushing fails.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    helper = f["helper"]
    incident = f["incident"]
    return [
        QAItem(
            question=f"How did bacon help {hero.id}?",
            answer=incident["bacon"] + " " + incident["clue"],
        ),
        QAItem(
            question=f"What was the twist in {incident['title']}?",
            answer=(
                f"The twist was that rushing or using more power made the danger worse. "
                f"{hero.id} realized that listening revealed what the frightened problem needed."
            ),
        ),
        QAItem(
            question=f"How was the {incident['object']} removed?",
            answer=incident["action"].replace("Luna", hero.id).replace("Mira", helper.id).replace("Bolt", partner.id),
        ),
        QAItem(
            question=f"How did {hero.id} and {partner.id} reconcile?",
            answer=(
                f"{partner.id} admitted that rushing had been harmful, and {hero.id} accepted the apology. "
                "They agreed to listen and work together before using their powers."
            ),
        ),
        QAItem(
            question="What lesson did the heroes learn?",
            answer=f"They learned that {incident['lesson']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can listening help during a rescue?",
            answer="Listening can reveal what is causing the trouble and what kind of help is safest.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means repairing a relationship after conflict by being honest, apologizing, forgiving, and cooperating again.",
        ),
        QAItem(
            question="Why should a hero remove something carefully?",
            answer="Careful removal prevents extra damage and protects the people, animals, or objects nearby.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
            f"  {entity.id}: type={entity.type} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_valid() -> tuple[set[tuple], set[tuple], set[tuple]]:
    import asp
    model = asp.one_model(
        asp_program("#show bacon/1.\n#show remove/2.\n#show reconciled/2.")
    )
    return (
        set(asp.atoms(model, "bacon")),
        set(asp.atoms(model, "remove")),
        set(asp.atoms(model, "reconciled")),
    )


def asp_verify() -> int:
    bacon, removed, reconciled = asp_valid()
    expected = ({("bacon",)}, {("hero", "beacon")}, {("partner", "hero")})
    if (bacon, removed, reconciled) != expected:
        print("MISMATCH between clingo and Python gate.")
        print("  clingo:", bacon, removed, reconciled)
        print("  python:", expected)
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or "bacon" not in sample.story.lower():
            print("Generated story exercise failed.")
            return 1
    print("OK: clingo parity and generated-story checks passed.")
    return 0


CURATED = [
    StoryParams(hero="Luna", partner="Bolt", helper="Mira", city="Bright City", incident=0),
    StoryParams(
        hero="Nova",
        partner="Dash",
        helper="Sunny",
        city="Moonbeam City",
        incident=2,
        opening=3,
        twist=1,
        reconciliation=2,
        cadence=4,
    ),
    StoryParams(
        hero="Comet",
        partner="Flash",
        helper="Tess",
        city="Star Harbor",
        incident=4,
        opening=1,
        twist=4,
        reconciliation=0,
        cadence=2,
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
        print(asp_program("#show bacon/1.\n#show remove/2.\n#show reconciled/2."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        bacon, removed, reconciled = asp_valid()
        print("ASP bacon facts:", sorted(bacon))
        print("ASP removal facts:", sorted(removed))
        print("ASP reconciliation facts:", sorted(reconciled))
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
                samples.append(sample)
                seen.add(sample.story)
            attempt += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            header = f"### {sample.params.hero}: superhero rescue"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
